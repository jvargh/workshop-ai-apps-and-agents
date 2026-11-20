# Supplemental lab - Knowledge mining with Azure AI Search

[Official exercise](https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/04-knowledge-mining.html) | [Visual-data labs](../README.md) | [Repository setup](../../README.md)

Build an enrichment pipeline for six sample travel brochures, then use an
interactive Python client to search the index and display extracted fields.

**Recorded status: blocked by storage network policy.** Azure accepted the
Search pipeline definitions, but the PDFs could not be uploaded. The recorded
index contains 0 of 6 documents, so end-to-end enrichment and semantic ranking
remain unverified. Do not run setup until approved storage connectivity is
available.

## Table of contents

- [1. Verify prerequisites and storage access](#1-verify-prerequisites-and-storage-access)
- [2. Configure the lab and sign in](#2-configure-the-lab-and-sign-in)
- [3. Install dependencies](#3-install-dependencies)
- [4. Set up and validate the Search pipeline](#4-set-up-and-validate-the-search-pipeline)
- [5. Run the interactive search client](#5-run-the-interactive-search-client)
- [How the client and pipeline work](#how-the-client-and-pipeline-work)
- [Troubleshooting, privacy, and costs](#troubleshooting-privacy-and-costs)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Historical Azure and launcher results](#1-historical-azure-and-launcher-results)
  - [2. Historical local checks](#2-historical-local-checks)

## 1. Verify prerequisites and storage access

Use an authorized Azure AI Search service and a private Blob container. The
setup identity needs permission to manage Search objects (for example,
**Search Service Contributor**), read index data (**Search Index Data
Reader**), and upload blobs (**Storage Blob Data Contributor**). The
interactive client only needs index read access. The Search service's
system-assigned managed identity separately needs **Storage Blob Data Reader**
on the source container.

Role assignments do not override network restrictions. Before setup, verify
that your machine can upload to the container and that Search can read it
through approved network paths.

## 2. Configure the lab and sign in

Run the commands in this guide from the **repository root**. Copy the
template only if the lab's `.env` does not already exist.

```powershell
$searchLab = '.\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search'
if (-not (Test-Path (Join-Path $searchLab '.env'))) {
    Copy-Item (Join-Path $searchLab '.env.example') (Join-Path $searchLab '.env')
}
```

Edit the local `.env` using [`.env.example`](.env.example) as a reference:

| Variable | Value |
|---|---|
| `SEARCH_ENDPOINT` | Search service root, such as `https://<search-service>.search.windows.net`. Do not use a Foundry project endpoint or an index URL. |
| `INDEX_NAME` | The index to configure and query, such as `margies-index`. Setup also uses it as the prefix for the other Search objects. |
| `STORAGE_RESOURCE_ID` | Storage account ARM ID: `/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Storage/storageAccounts/<storage-account>`. Setup derives the Blob endpoint from it. |
| `BLOB_CONTAINER` | Private container for the six brochures, such as `documents`. |

Both scripts use `DefaultAzureCredential` with Microsoft Entra ID. Sign in
with Azure CLI if needed and select the intended subscription:

```powershell
az login --tenant '<tenant-id>'
az account set --subscription '<subscription-id>'
```

The official guide's `QUERY_KEY` is not used. Keep the populated `.env` local
and out of source control.

## 3. Install dependencies

The shared launcher uses `.labenv` at the repository root. To install this lab's
[dependencies](requirements.txt) without running setup:

```powershell
if (-not (Test-Path '.\.labenv\Scripts\python.exe')) {
    python -m venv .labenv
}
.\.labenv\Scripts\python.exe -m pip install -r .\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search\requirements.txt
```

The launcher's `-Install` switch installs dependencies **and then runs the
named script**. Do not use it with `setup-search.py` unless you intend to
upload data, create or update Search objects, and run the indexer.

## 4. Set up and validate the Search pipeline

After confirming approved storage connectivity, check that the configured
object names belong to this lab. Then run:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search setup-search.py
```

The first launcher argument is the **folder**; the second is the **script
name**. Setup reads the six sample PDFs from [documents.zip](documents.zip)
without manual extraction, uploads them, configures the Search pipeline, and
validates the resulting index.

To recheck an existing index without uploading files or rerunning the indexer:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search setup-search.py --validate-only
```

Both modes write `validation-results.json` in the lab folder and exit nonzero
on failure. An indexer run that reports `success` but processes zero documents
does not pass lab validation.

## 5. Run the interactive search client

After setup and validation pass, run:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search search-app.py
```

Enter the following queries one at a time, then type `quit` to exit:

```text
London
flights
quit
```

Once indexing is complete, results should show document titles, locations,
people, and key phrases. Individual person collections can be empty when no
person is detected.

## How the client and pipeline work

- [setup-search.py](setup-search.py) reproduces the official portal wizard's
  pipeline setup with Search REST API `2026-04-01`. The data source uses the
  storage resource ID so the Search managed identity can authenticate.
- [search-app.py](search-app.py) uses Search SDK 12.x and retains the guide's
  selected result fields and title ordering.
- [lab_config.py](lab_config.py) loads configuration relative to the scripts,
  not the terminal's current directory.

The skillset performs OCR on normalized embedded images, merges OCR output
with document text, extracts key phrases and **Person** and **Location**
entities, and extracts image tags and categories. The index stores original
and merged text, file metadata, `title`, `locations`, `persons`, `keyPhrases`,
`imageTags`, and `imageCategories`. The `title` is the PDF file name, not a
generated summary. The pipeline also defines a semantic configuration.

There is no recurring schedule. A new indexer runs on creation; setup starts
an existing indexer without resetting it. Identical sample blobs are skipped,
and differing blobs are not silently overwritten.

## Troubleshooting, privacy, and costs

- **`AuthorizationFailure` on upload or list:** The recorded account's
  `publicNetworkAccess` remained `Disabled` even after a management operation
  reported success. The activity log recorded an Azure Policy `modify`
  action. An administrator must arrange policy-compliant connectivity, such
  as an approved private endpoint with working routing and DNS. No private
  endpoint was provisioned and no policy exemption or bypass was attempted.
- **`KeyBasedAuthenticationNotPermitted`:** Shared keys are disabled. Use
  Entra ID and the roles in step 1; changing credentials does not resolve a
  network-policy restriction. Anonymous Blob access is also disabled.
- **Zero results:** Check that the source actually contains the six PDFs and
  that the indexer can read them. Access to the empty source was observed;
  access to the PDFs and actual enrichment were not verified.
- **Privacy and costs:** Upload only authorized sample files and redact
  resource details before sharing validation reports. The skillset uses the
  guide's limited free enrichment allowance (up to 20 documents or
  transactions per indexer per day), but normalized-image extraction,
  storage, serverless Search, semantic queries, and private networking can
  incur additional charges.
- **Cleanup:** Do not delete the shared resource group. Review and remove
  only this lab's Search objects, storage account, and role assignments when
  they are no longer needed.

## Validation and conclusion

The lab is complete only when validation finds all six indexed brochures and
records `success: true` in `validation-results.json`. The recorded report
instead shows `success: false`. Validation checks:

- Exactly the six expected PDF titles, correct byte sizes, and populated modified timestamps.
- Nonempty merged text, locations and key phrases; collection types for all enriched fields.
- At least some person, image-tag, and image-category extraction across the corpus.
- The guide's `*`, selected `title,locations`, `New York`, and `metadata_storage_size lt 380000` queries.
- Nonempty `London` and `flights` results, and the appropriate London/New York brochures.
- Real semantic reranker scores, not merely the existence of a semantic configuration.

Run the local regression tests without contacting Azure:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\4_Extract_Insights_From_Visual_Data_On_Azure\zcreate-knowledge-mining-with-azureai-search -p test_lab.py -v
```

## Captured output

These are historical results from the earlier setup attempt, not a fresh run.

### 1. Historical Azure and launcher results

The attempt reused a serverless Search service in West US 3 and created a
StorageV2 Standard LRS account with a private `documents` container. The
container was created through the management plane because data-plane access
was blocked. Approved Blob roles were scoped to that container; a default-deny
firewall with an outbound-IP rule and the trusted Azure services exception
was configured. The effective public endpoint remained disabled. Review the
IP rule if an administrator later approves a connectivity change.

The configured objects were `margies-index`, `margies-index-datasource`,
`margies-index-skillset`, and `margies-index-indexer`, with semantic
configuration `margies-semantic`.

| Check | Result |
|---|---|
| Live pipeline API requests | All four object definitions accepted. |
| Persisted schema | All 13 fields matched their configured attributes, including the six from the guide's field-attribute table; semantic configuration present. |
| Indexer initial execution | `success`, 0 processed, 0 failed; empty source, not lab completion. |
| Actual launcher: setup | Exit 1, storage `AuthorizationFailure`. |
| Actual launcher: validate-only | Exit 1, `Expected six indexed PDFs; found 0.` |
| Actual launcher: `London`, `flights`, `quit` | Authentication/query/exit worked; both queries returned 0 documents. |
| Existing Search objects | Three prior indexes and one prior indexer were preserved. |
| Six-document AI enrichment and semantic ranking | **Blocked / not yet validated**. |

### 2. Historical local checks

- The archive contained six PDFs with matching byte sizes and PDF signatures.
- **20 offline tests passed**, including a mocked six-document validation
  path. Python compilation also passed.
- `pip check` reported an unrelated pre-existing conflict:
  `agent-framework-foundry 1.10.3` required
  `azure-ai-projects>=2.2.0,<2.4.0`, but `2.0.0b4` was installed.
  No unrelated packages were changed.
