from dotenv import load_dotenv
import os
import json
import sys
from pathlib import Path
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import ContentAnalyzerStatus
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential


def main():

    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    try:

        # Get the business card schema
        lab_dir = Path(__file__).resolve().parent
        schema_path = lab_dir / "biz-card.json"
        print(f"Loading analyzer schema: {schema_path}", flush=True)
        with schema_path.open(encoding="utf-8") as file:
            schema_json = json.load(file)
        
        card_schema = json.dumps(schema_json)

        # Get config settings
        load_dotenv(lab_dir / ".env")
        ai_svc_endpoint = os.getenv('ENDPOINT')
        analyzer = os.getenv('ANALYZER_NAME')

        # Create the analyzer
        create_analyzer(card_schema, analyzer, ai_svc_endpoint)

    except (AzureError, OSError, ValueError) as ex:
        print(f"Analyzer creation failed: {ex}", file=sys.stderr)
        raise SystemExit(1) from ex



def create_analyzer(schema, analyzer, endpoint):
    
    # Create a Content Understanding analyzer
    if not endpoint or endpoint == "YOUR_ENDPOINT":
        raise ValueError("Set ENDPOINT in this lab's .env to the Foundry resource root endpoint.")
    if not analyzer:
        raise ValueError("Set ANALYZER_NAME in this lab's .env.")
    analyzer_definition = json.loads(schema)
    with DefaultAzureCredential() as credential, ContentUnderstandingClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2025-11-01"
    ) as client:
        print(f"Submitting creation request for analyzer '{analyzer}'...", flush=True)
        print("If this analyzer ID already exists, its definition will be replaced.", flush=True)
        poller = client.begin_create_analyzer(
            analyzer_id=analyzer,
            resource=analyzer_definition,
            allow_replace=True
        )
        print("Request accepted. Waiting for the analyzer to become ready...", flush=True)
        result = poller.result()
        if result.status != ContentAnalyzerStatus.READY:
            raise ValueError(f"Analyzer was not ready after creation: {result.status}")
        print(f"Analyzer '{analyzer}' created successfully.")
        print(f"Status: {result.status.value}")




if __name__ == "__main__":
    main()        
