"""Prepare and verify the lab's Azure AI Search index and Foundry connection."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchableField,
    SimpleField,
    SearchFieldDataType,
)
from dotenv import load_dotenv, set_key


class SearchSetup:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.env_file = self.project_dir / ".env"
        load_dotenv(self.env_file)
        self.docs_dir = self.project_dir / "sample_documents"
        self.project_endpoint = os.getenv("PROJECT_ENDPOINT")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.location = os.getenv("AZURE_LOCATION")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.search_service_name = os.getenv("SEARCH_SERVICE_NAME")
        self.search_endpoint = os.getenv("SEARCH_ENDPOINT", "").rstrip("/")
        self.search_key = os.getenv("SEARCH_KEY")
        self.index_name = os.getenv("SEARCH_INDEX_NAME", "company-knowledge")
        self.connection_id = os.getenv("SEARCH_PROJECT_CONNECTION_ID")
        self.document_ids = set()

    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def print_step(self, step_num, title):
        print(f"\nStep {step_num}: {title}\n" + "-" * 70)

    def run_az(self, *arguments):
        executable = shutil.which("az")
        if not executable:
            raise RuntimeError("Azure CLI is required to manage the Search service.")
        command = [executable, *arguments]
        if self.subscription_id:
            command.extend(["--subscription", self.subscription_id])
        result = subprocess.run(
            [*command, "--output", "json", "--only-show-errors"],
            capture_output=True, text=True, check=True, cwd=self.project_dir,
        )
        return json.loads(result.stdout)

    def get_deployment_info(self):
        """Prefer the lab's .env and discover its existing Foundry Search connection."""
        self.print_step(1, "Resolving Project and Search Configuration")
        if not self.project_endpoint and (self.project_dir / "azure.yaml").exists():
            result = subprocess.run(
                ["azd", "env", "get-values"], capture_output=True, text=True,
                check=True, cwd=self.project_dir,
                env={**os.environ, "AZURE_DEV_USER_AGENT": "microsoft_foundry_skill"},
            )
            values = {}
            for line in result.stdout.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    values[key] = value.strip().strip('"')
            self.project_endpoint = next((
                values[key] for key in (
                    "PROJECT_ENDPOINT", "AZURE_AI_PROJECT_ENDPOINT",
                    "AZURE_AIPROJECT_ENDPOINT", "AZUREAI_PROJECT_ENDPOINT",
                ) if values.get(key)
            ), None)
            self.resource_group = self.resource_group or values.get("AZURE_RESOURCE_GROUP")
            self.location = self.location or values.get("AZURE_LOCATION")
            self.subscription_id = self.subscription_id or values.get("AZURE_SUBSCRIPTION_ID")

        if not self.project_endpoint:
            raise ValueError("Set PROJECT_ENDPOINT in this lab's .env file.")

        with DefaultAzureCredential() as credential, AIProjectClient(
            endpoint=self.project_endpoint, credential=credential,
        ) as project:
            connections = [
                connection for connection in project.connections.list()
                if connection.type == "CognitiveSearch"
            ]
        if self.connection_id:
            connections = [
                connection for connection in connections if connection.id == self.connection_id
            ]
        if self.search_endpoint:
            connections = [
                connection for connection in connections
                if connection.target.rstrip("/").lower() == self.search_endpoint.lower()
            ]
        if len(connections) != 1:
            raise ValueError(
                "Exactly one matching Foundry Azure AI Search connection is required. "
                "Add a Search connection in Foundry, or set SEARCH_ENDPOINT and "
                "SEARCH_PROJECT_CONNECTION_ID to select an existing connection."
            )

        connection = connections[0]
        self.connection_id = connection.id
        self.search_endpoint = connection.target.rstrip("/")
        self.search_service_name = urlparse(self.search_endpoint).hostname.split(".")[0]
        resource_parts = connection.id.split("/")
        self.subscription_id = self.subscription_id or resource_parts[2]
        if not self.resource_group:
            # Search can be in a different resource group from the Foundry project.
            services = self.run_az("resource", "list", "--resource-type", "Microsoft.Search/searchServices")
            matches = [service for service in services if service["name"] == self.search_service_name]
            if len(matches) != 1:
                raise ValueError("Set AZURE_RESOURCE_GROUP to the Search service's resource group.")
            self.resource_group = matches[0]["resourceGroup"]
            self.location = self.location or matches[0]["location"]

        print(f"Foundry connection: {connection.name}")
        print(f"Search endpoint: {self.search_endpoint}")
        print(f"Resource group: {self.resource_group}")
        return True

    def create_search_service(self):
        """Reuse the connected service without changing its SKU or authentication."""
        self.print_step(2, "Verifying Existing Search Service")
        service = self.run_az(
            "search", "service", "show", "--name", self.search_service_name,
            "--resource-group", self.resource_group,
        )
        self.location = service["location"]
        print(f"Reusing {self.search_service_name} ({service['sku']['name']}).")
        print("No new service will be provisioned; existing indexes will be preserved.")
        return True

    def search_credential(self):
        return AzureKeyCredential(self.search_key) if self.search_key else DefaultAzureCredential()

    def create_search_index(self):
        self.print_step(3, "Creating or Verifying the Lab Index")
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
        ]
        credential = self.search_credential()
        try:
            with SearchIndexClient(self.search_endpoint, credential) as client:
                client.create_or_update_index(SearchIndex(name=self.index_name, fields=fields))
        finally:
            if isinstance(credential, DefaultAzureCredential):
                credential.close()
        print(f"Index ready: {self.index_name}")
        return True

    def upload_documents(self):
        self.print_step(4, "Uploading Sample Documents")
        files = sorted(
            path for path in self.docs_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}
        )
        if not files:
            raise ValueError(f"No .md or .txt sample documents found in {self.docs_dir}.")
        documents = []
        for number, path in enumerate(files, 1):
            print(f"[Upload {number}/{len(files)}] Reading sample document: {path.name}", flush=True)
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                raise ValueError(f"Sample document is empty: {path.name}")
            category = next((
                category for keyword, category in (
                    ("handbook", "Handbook"), ("security", "Security"), ("expense", "Finance"),
                ) if keyword in path.name.lower()
            ), "Policy")
            documents.append({
                "id": hashlib.md5(path.name.encode()).hexdigest(),
                "title": content.strip().splitlines()[0].lstrip("# ")[:100],
                "content": content,
                "category": category,
                "source_file": path.name,
            })

        credential = self.search_credential()
        try:
            print("[Upload] Sending the sample documents to the configured lab index...", flush=True)
            with SearchClient(self.search_endpoint, self.index_name, credential) as client:
                results = client.upload_documents(documents=documents)
        finally:
            if isinstance(credential, DefaultAzureCredential):
                credential.close()
        failures = [result for result in results if not result.succeeded]
        if failures or len(results) != len(documents):
            details = "; ".join(f"{result.key}: {result.error_message}" for result in failures)
            raise RuntimeError(f"Document upload was incomplete. {details}")
        self.document_ids = {document["id"] for document in documents}
        print(f"Uploaded {len(documents)} documents: " + ", ".join(path.name for path in files))
        return True

    def test_search(self):
        """Wait for the uploaded documents and verify topic-specific retrieval."""
        self.print_step(5, "Verifying Indexed Documents and Policy Queries")
        checks = (
            ("remote work", "remote_work_policy.txt", "25 Mbps"),
            ("expense reports", "expense_report_guide.md", "concur.contoso.com"),
            ("laptop security", "it_security_policy.txt", "BitLocker"),
        )
        credential = self.search_credential()
        try:
            with SearchClient(self.search_endpoint, self.index_name, credential) as client:
                for attempt in range(12):
                    print(f"[Indexing] Checking uploaded document visibility ({attempt + 1}/12)...", flush=True)
                    indexed_ids = {
                        document["id"] for document in client.search(
                            search_text="*", select=["id"], top=1000,
                        )
                    }
                    if self.document_ids and self.document_ids.issubset(indexed_ids):
                        break
                    if attempt == 11:
                        raise RuntimeError("Uploaded documents did not become searchable within 60 seconds.")
                    time.sleep(5)
                for query, source, fact in checks:
                    print(f"[Validation] Searching for {query}; expecting source {source}...", flush=True)
                    results = list(client.search(
                        search_text=query, search_fields=["title", "content"], top=4,
                    ))
                    if not any(
                        result.get("source_file") == source and fact in result.get("content", "")
                        for result in results
                    ):
                        raise RuntimeError(f"Search validation failed for '{query}'; expected source {source}.")
                    print(f"PASS: {query} -> {source} (verified '{fact}')")
        finally:
            if isinstance(credential, DefaultAzureCredential):
                credential.close()
        return True

    def save_configuration(self):
        self.print_step(6, "Saving Verified Configuration")
        values = {
            "SEARCH_ENDPOINT": self.search_endpoint,
            "SEARCH_INDEX_NAME": self.index_name,
            "SEARCH_SERVICE_NAME": self.search_service_name,
            "SEARCH_PROJECT_CONNECTION_ID": self.connection_id,
            "AZURE_RESOURCE_GROUP": self.resource_group,
            "AZURE_LOCATION": self.location,
            "AZURE_SUBSCRIPTION_ID": self.subscription_id,
        }
        for key, value in values.items():
            set_key(str(self.env_file), key, value)
        print(f"Updated {self.env_file.name}; no admin keys are retrieved or saved.")
        return True

    def show_next_steps(self):
        print("\nSearch setup and all three retrieval checks passed.")
        print("Run m365_teams_lab.py and select option 1 for grounded policy answers,")
        print("or option 4 for interactive chat using the same Search index.")
        print("The index uses keyword search; no embeddings or semantic-ranker setup is needed.")

    def run(self):
        self.print_header("Lab-z10a: Azure AI Search Setup")
        print("This script reuses the project's connected Search service.")
        print("It creates/updates only the configured lab index and uploads the sample documents.")
        try:
            for step in (
                self.get_deployment_info, self.create_search_service, self.create_search_index,
                self.upload_documents, self.test_search, self.save_configuration,
            ):
                if not step():
                    return False
        except subprocess.CalledProcessError as error:
            print(f"ERROR: Azure CLI command failed: {error.stderr.strip()}")
            return False
        except (AzureError, OSError, ValueError, RuntimeError) as error:
            print(f"ERROR: Search setup failed: {error}")
            return False
        self.show_next_steps()
        return True


def main():
    sys.exit(0 if SearchSetup().run() else 1)


if __name__ == "__main__":
    main()
