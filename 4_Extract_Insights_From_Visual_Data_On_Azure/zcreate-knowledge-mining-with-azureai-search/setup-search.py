import argparse
import json
import re
import sys
import time
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import requests
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient, ContentSettings

from lab_config import LAB_DIR, load_search_config, required_setting

API_VERSION = "2026-04-01"
EXPECTED_DOCUMENTS = {
    "Dubai Brochure.pdf": 388622,
    "Las Vegas Brochure.pdf": 569917,
    "London Brochure.pdf": 450635,
    "Margies Travel Company Info.pdf": 352264,
    "New York Brochure.pdf": 382414,
    "San Francisco Brochure.pdf": 385331,
}


class SearchRest:
    def __init__(self, endpoint, credential, session):
        self.endpoint = endpoint
        self.credential = credential
        self.session = session

    def call(self, method, path, body=None):
        token = self.credential.get_token("https://search.azure.com/.default")
        response = self.session.request(
            method,
            f"{self.endpoint}/{path}",
            params={"api-version": API_VERSION},
            headers={"Authorization": f"Bearer {token.token}"},
            json=body,
            timeout=90,
        )
        if not response.ok:
            raise RuntimeError(
                f"Search {method} {path}: HTTP {response.status_code}: {response.text}"
            )
        return response.json() if response.content else None


def field(name, field_type="Edm.String", *, searchable=False, filterable=False,
          sortable=False, key=False):
    return {
        "name": name,
        "type": field_type,
        "key": key,
        "searchable": searchable,
        "filterable": filterable,
        "sortable": sortable,
        "facetable": False,
        "retrievable": True,
    }


def index_definition(index):
    collection = "Collection(Edm.String)"
    return {
        "name": index,
        "fields": [
            field("id", key=True),
            field("content", searchable=True),
            field("merged_content", searchable=True),
            field("metadata_storage_name", searchable=True),
            field("metadata_storage_path"),
            field("metadata_storage_size", "Edm.Int64",
                  filterable=True, sortable=True),
            field("metadata_storage_last_modified", "Edm.DateTimeOffset",
                  filterable=True, sortable=True),
            field("title", searchable=True, filterable=True, sortable=True),
            field("locations", collection, searchable=True, filterable=True),
            field("persons", collection, searchable=True, filterable=True),
            field("keyPhrases", collection, searchable=True, filterable=True),
            field("imageTags", collection, searchable=True),
            field("imageCategories", collection, searchable=True),
        ],
        "semantic": {
            "defaultConfiguration": "margies-semantic",
            "configurations": [{
                "name": "margies-semantic",
                "prioritizedFields": {
                    "titleField": {"fieldName": "title"},
                    "prioritizedContentFields": [{"fieldName": "merged_content"}],
                    "prioritizedKeywordsFields": [{"fieldName": "keyPhrases"}],
                },
            }],
        },
    }


def skill(skill_type, name, inputs, outputs, *, context="/document", **settings):
    return {
        "@odata.type": f"#Microsoft.Skills.{skill_type}",
        "name": name,
        "context": context,
        "inputs": [{"name": key, "source": value} for key, value in inputs.items()],
        "outputs": [{"name": key, "targetName": value}
                    for key, value in outputs.items()],
        **settings,
    }


def skillset_definition(index):
    image = "/document/normalized_images/*"
    text = {"text": "/document/merged_content"}
    return {
        "name": f"{index}-skillset",
        "description": "Margie's Travel: OCR, image tags/categories, entities and phrases.",
        # Omitting cognitiveServices selects the limited free enrichment allowance.
        "skills": [
            skill("Vision.OcrSkill", "ocr", {"image": image}, {"text": "text"},
                  context=image, defaultLanguageCode="en",
                  detectOrientation=True),
            skill("Text.MergeSkill", "merge",
                  {"text": "/document/content",
                   "itemsToInsert": f"{image}/text",
                   "offsets": f"{image}/contentOffset"},
                  {"mergedText": "merged_content"},
                  insertPreTag=" ", insertPostTag=" "),
            skill("Text.KeyPhraseExtractionSkill", "phrases", text,
                  {"keyPhrases": "keyPhrases"}, defaultLanguageCode="en"),
            skill("Text.V3.EntityRecognitionSkill", "entities", text,
                  {"persons": "persons", "locations": "locations"},
                  categories=["Person", "Location"], defaultLanguageCode="en"),
            skill("Vision.ImageAnalysisSkill", "images", {"image": image},
                  {"tags": "tags", "categories": "categories"}, context=image,
                  defaultLanguageCode="en", visualFeatures=["tags", "categories"]),
        ],
    }


def datasource_definition(index, storage_id, container):
    return {
        "name": f"{index}-datasource",
        "type": "azureblob",
        "credentials": {"connectionString": f"ResourceId={storage_id};"},
        "container": {"name": container},
    }


def indexer_definition(index):
    return {
        "name": f"{index}-indexer",
        "dataSourceName": f"{index}-datasource",
        "targetIndexName": index,
        "skillsetName": f"{index}-skillset",
        "parameters": {
            "maxFailedItems": 0,
            "maxFailedItemsPerBatch": 0,
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "imageAction": "generateNormalizedImages",
                "indexedFileNameExtensions": ".pdf",
            },
        },
        "fieldMappings": [
            {"sourceFieldName": "metadata_storage_path", "targetFieldName": "id",
             "mappingFunction": {"name": "base64Encode"}},
            {"sourceFieldName": "metadata_storage_name", "targetFieldName": "title"},
        ],
        "outputFieldMappings": [
            {"sourceFieldName": f"/document/{name}", "targetFieldName": name}
            for name in ("merged_content", "locations", "persons", "keyPhrases")
        ] + [
            {"sourceFieldName": f"/document/normalized_images/*/{source}/*/name",
             "targetFieldName": target}
            for source, target in (("tags", "imageTags"),
                                   ("categories", "imageCategories"))
        ],
    }


def storage_settings():
    resource_id = required_setting("STORAGE_RESOURCE_ID").rstrip("/")
    match = re.fullmatch(
        r"/subscriptions/[^/]+/resourceGroups/[^/]+/providers/"
        r"Microsoft\.Storage/storageAccounts/([a-z0-9]{3,24})",
        resource_id, re.IGNORECASE,
    )
    if not match:
        raise ValueError("STORAGE_RESOURCE_ID must identify an Azure storage account.")
    return resource_id, match.group(1).lower(), required_setting("BLOB_CONTAINER")


def upload_documents(account, container, credential):
    with ZipFile(LAB_DIR / "documents.zip") as archive:
        files = {
            Path(item.filename).name: item
            for item in archive.infolist() if item.filename.lower().endswith(".pdf")
        }
        if set(files) != set(EXPECTED_DOCUMENTS) or any(
            files[name].file_size != size
            for name, size in EXPECTED_DOCUMENTS.items()
        ):
            raise ValueError("documents.zip must contain the six original lab PDFs.")
        with BlobServiceClient(
            f"https://{account}.blob.core.windows.net", credential=credential
        ) as blobs:
            target = blobs.get_container_client(container)
            existing = {item.name: item for item in target.list_blobs()}
            for name, item in files.items():
                data = archive.read(item)
                if name in existing:
                    with target.get_blob_client(name) as blob:
                        if blob.download_blob().readall() != data:
                            raise ValueError(
                                f"Blob {name} differs from the lab sample; not overwriting."
                            )
                    print(f"Already uploaded: {name}")
                    continue
                target.upload_blob(
                    name, data, overwrite=False,
                    content_settings=ContentSettings(content_type="application/pdf"),
                )
                print(f"Uploaded: {name}")


def wait_for_indexer(rest, index, timeout, previous_start=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = rest.call("GET", f"indexers/{index}-indexer/status")
        result = status.get("lastResult") or {}
        if result.get("startTime") != previous_start and result.get("status") in (
            "success", "transientFailure", "persistentFailure", "reset",
        ):
            return status
        time.sleep(5)
    raise TimeoutError(f"Indexer did not finish within {timeout} seconds.")


def configure_pipeline(rest, index, storage_id, container, timeout):
    existing = rest.call("GET", "indexers")["value"]
    previous_start = None
    indexer_exists = any(item["name"] == f"{index}-indexer" for item in existing)
    if indexer_exists:
        status = rest.call("GET", f"indexers/{index}-indexer/status")
        result = status.get("lastResult") or {}
        if result.get("status") == "inProgress":
            status = wait_for_indexer(rest, index, timeout)
        previous_start = (status.get("lastResult") or {}).get("startTime")

    for kind, body in (
        ("indexes", index_definition(index)),
        ("datasources", datasource_definition(index, storage_id, container)),
        ("skillsets", skillset_definition(index)),
        ("indexers", indexer_definition(index)),
    ):
        rest.call("PUT", f"{kind}/{body['name']}", body)
        print(f"Configured {kind}: {body['name']}")
    if indexer_exists:
        # Creation runs automatically; updates of an existing indexer do not.
        rest.call("POST", f"indexers/{index}-indexer/run")
    return wait_for_indexer(rest, index, timeout, previous_start)


def check(condition, message):
    if not condition:
        raise ValueError(message)


def validate_search(endpoint, index, credential):
    with SearchClient(endpoint, index, credential) as client:
        all_results = client.search(
            "*", include_total_count=True, order_by=["title"]
        )
        documents = list(all_results)
        check(all_results.get_count() == 6 and len(documents) == 6,
              f"Expected six indexed PDFs; found {len(documents)}.")
        check({d["title"] for d in documents} == set(EXPECTED_DOCUMENTS),
              "Indexed titles do not match the six lab PDFs.")
        for document in documents:
            title = document["title"]
            check(document["metadata_storage_size"] == EXPECTED_DOCUMENTS[title],
                  f"Incorrect blob size for {title}.")
            check(document["metadata_storage_last_modified"] is not None,
                  f"Missing last-modified metadata for {title}.")
            check(bool(document["merged_content"].strip()),
                  f"No merged text for {title}.")
            for name in ("locations", "persons", "keyPhrases",
                         "imageTags", "imageCategories"):
                check(isinstance(document[name], list),
                      f"{title}: {name} is not a collection.")
            check(bool(document["locations"]) and bool(document["keyPhrases"]),
                  f"Missing location/phrase enrichment for {title}.")
        for name in ("persons", "imageTags", "imageCategories"):
            check(any(d[name] for d in documents),
                  f"No {name} enrichment in any document.")

        cases = [
            ("all_titles_locations", "*", ["title", "locations"], None),
            ("new_york", "New York", ["title", "keyPhrases"], None),
            ("new_york_under_380000", "New York", ["title", "keyPhrases"],
             "metadata_storage_size lt 380000"),
            ("london", "London", ["title", "locations", "persons", "keyPhrases"], None),
            ("flights", "flights", ["title", "locations", "persons", "keyPhrases"], None),
        ]
        queries = {}
        for name, text, select, filter_text in cases:
            result = client.search(
                text, select=select, filter=filter_text,
                include_total_count=True, order_by=["title"],
            )
            hits = [dict(hit) for hit in result]
            check(bool(hits), f"Guide query {name} returned no documents.")
            check(all(set(select).issubset(hit) for hit in hits),
                  f"Guide query {name} omitted requested fields.")
            if filter_text:
                check(all(EXPECTED_DOCUMENTS[h["title"]] < 380000 for h in hits),
                      "The 380000-byte filter returned an oversized document.")
            queries[name] = {"search": text, "filter": filter_text,
                             "count": result.get_count(), "results": hits}
            print(f"{name}: {result.get_count()} documents")
        check("New York Brochure.pdf" in
              {hit["title"] for hit in queries["new_york"]["results"]},
              "New York search did not return the New York brochure.")
        check("London Brochure.pdf" in
              {hit["title"] for hit in queries["london"]["results"]},
              "London search did not return the London brochure.")

        semantic = list(client.search(
            "travel destinations and flights", query_type="semantic",
            semantic_configuration_name="margies-semantic",
            select=["title"], top=3,
        ))
        check(bool(semantic) and any(
            hit.get("@search.reranker_score") is not None for hit in semantic
        ), "Semantic ranker did not return reranker scores.")
        return {"document_count": len(documents), "guide_queries": queries,
                "semantic_results": [dict(hit) for hit in semantic],
                "enrichment_counts": {
                    name: sum(len(d[name]) for d in documents)
                    for name in ("locations", "persons", "keyPhrases",
                                 "imageTags", "imageCategories")
                }}


def main():
    parser = argparse.ArgumentParser(
        description="Upload the six lab PDFs, create Search enrichment objects, and validate."
    )
    parser.add_argument("--validate-only", action="store_true",
                        help="Check the existing index without uploading or reindexing.")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Indexer wait limit in seconds (default: 600).")
    args = parser.parse_args()
    report_path = LAB_DIR / "validation-results.json"
    report = {"success": False}
    try:
        check(args.timeout > 0, "--timeout must be positive.")
        endpoint, index = load_search_config()
        report.update({"endpoint": endpoint, "index": index})
        with DefaultAzureCredential() as credential, requests.Session() as session:
            rest = SearchRest(endpoint, credential, session)
            if not args.validate_only:
                storage_id, account, container = storage_settings()
                upload_documents(account, container, credential)
                status = configure_pipeline(rest, index, storage_id, container, args.timeout)
            else:
                status = rest.call("GET", f"indexers/{index}-indexer/status")

            report["indexer_status"] = status
            result = status.get("lastResult") or {}
            for warning in result.get("warnings") or []:
                print(f"Indexer warning: {json.dumps(warning)}", file=sys.stderr)
            check(result.get("status") == "success",
                  f"Indexer not successful: {json.dumps(result, default=str)}")
            check(result.get("itemsFailed") == 0 and not result.get("errors"),
                  f"Indexer reported failures: {json.dumps(result, default=str)}")
            report.update(validate_search(endpoint, index, credential))
            report["success"] = True
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"Validated six documents, all guide queries and semantic ranking. {report_path}")
        return 0
    except (AzureError, requests.RequestException, OSError, ValueError,
            RuntimeError, BadZipFile, TimeoutError) as exc:
        report["error"] = str(exc)
        try:
            report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        except OSError as write_error:
            print(f"Could not save validation report: {write_error}", file=sys.stderr)
        print(f"Setup/validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
