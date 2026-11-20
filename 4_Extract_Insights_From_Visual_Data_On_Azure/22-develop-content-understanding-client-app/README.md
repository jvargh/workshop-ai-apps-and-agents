# Lab 22 - Develop a Content Understanding client application

[Official exercise](https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/02-content-understanding-api.html) | [Visual-data labs](../README.md) | [Repository setup](../../README.md)

Build a custom business-card analyzer, submit local card images to Azure AI
Content Understanding, print the extracted contact fields, and save each full
analysis response as JSON.

## Table of contents

- [1. Prepare configuration and authentication](#1-prepare-configuration-and-authentication)
- [2. Install dependencies](#2-install-dependencies)
- [3. Review the analyzer schema](#3-review-the-analyzer-schema)
- [4. Create the analyzer only if it does not exist](#4-create-the-analyzer-only-if-it-does-not-exist)
- [5. Analyze the business cards](#5-analyze-the-business-cards)
  - [5.1. Analyze the first card](#51-analyze-the-first-card)
  - [5.2. Analyze the second card](#52-analyze-the-second-card)
- [6. Review and protect the JSON output](#6-review-and-protect-the-json-output)
- [How the client works](#how-the-client-works)
- [Troubleshooting, privacy, and costs](#troubleshooting-privacy-and-costs)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Reader help (November 15, 2026)](#1-reader-help-november-15-2026)
  - [2. Missing-image dry run (November 15, 2026)](#2-missing-image-dry-run-november-15-2026)
  - [3. Isolated synthetic live run (November 15, 2026)](#3-isolated-synthetic-live-run-november-15-2026)
  - [4. Historical Azure output (October 30, 2026)](#4-historical-azure-output-october-30-2026)

## 1. Prepare configuration and authentication

Run these commands from the **repository root**. The conditional copy preserves
an existing `.env`; then edit the local file without pasting its contents into
chat, documentation, or a terminal transcript.

```powershell
$lab = '.\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app'
if (-not (Test-Path (Join-Path $lab '.env'))) {
    Copy-Item (Join-Path $lab '.env.example') (Join-Path $lab '.env')
}
```

Configure these values in the lab's `.env`:

| Variable | Value |
|---|---|
| `ENDPOINT` | The Foundry resource root, such as `https://<resource>.services.ai.azure.com/`. Do not use a project URL ending in `/api/projects/...` or an OpenAI URL ending in `/openai/v1/`. |
| `ANALYZER_NAME` | The analyzer ID used for both creation and analysis. Keep it consistent with the analyzer in your resource. |

The scripts use `DefaultAzureCredential` with Microsoft Entra ID. Sign in with
Azure CLI if you do not already have an active session:

```powershell
az login
```

No API key is read by these scripts. Your signed-in identity must be authorized
to use Content Understanding in the configured resource.

## 2. Install dependencies

The shared launcher uses the repository-root `.labenv`. If that environment
does not exist, create it once, then install this lab's declared packages:

```powershell
if (-not (Test-Path '.\.labenv\Scripts\python.exe')) {
    python -m venv .labenv
}
.\.labenv\Scripts\python.exe -m pip install -r .\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app\requirements.txt
```

The launcher's `-Install` switch installs packages **and then runs the
requested script**; it is not an
install-only mode. In particular, do not use `-Install` with
`create-analyzer.py` unless you intend to run its Azure-side create/replace
operation. The local validation recorded below used the existing environment
and did not install or update packages.

## 3. Review the analyzer schema

Open [biz-card.json](biz-card.json). It defines an analyzer based on
`prebuilt-document`, requests detailed output, and extracts five string fields:
`Company`, `Name`, `Title`, `Email`, and `Phone`. Its model identifiers are
`gpt-5.5` and `text-embedding-3-large`; check that the configured resource
supports the schema before creating an analyzer.

The analyzer ID is resource-scoped. Before creating it, check the configured
resource for an analyzer with the same `ANALYZER_NAME`. The creation script
passes `allow_replace=True`: running it when that ID already exists replaces
its definition.

## 4. Create the analyzer only if it does not exist

Skip this step if the same analyzer ID already exists in the configured
resource. A previous live run recorded in this README created
`businesscardanalyzer`; do not rerun creation against that resource merely to
repeat the lab.

Only after verifying the ID is absent, run this command from the repository
root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app create-analyzer.py
```

The console shows the schema path, the analyzer ID being submitted, when the
script is waiting for Azure, and the final analyzer status. It exits with an error if the endpoint or
analyzer ID is missing, the request fails, or the analyzer does not reach
`ready`. Creation is a persistent Azure-side change; do not delete or replace
analyzers that may be shared by other work.

## 5. Analyze the business cards

There is no natural-language chat prompt in this client. Select an image by
passing its filename to `read-card.py`. The image is submitted to the analyzer,
and the console shows when the image is read, submitted, and waiting for
results. The script prints the extracted contact fields grouped by card and
reports where it saved the full JSON response.

The sample images `biz-card-1.png` and `biz-card-2.png` are local assets. A
fresh checkout may not include these untracked local files; obtain the exercise
images from the linked guide or use an authorized local test image.

### 5.1. Analyze the first card

From the repository root, choose a new output name. The GUID and existence
check avoid replacing a previous result:

```powershell
$lab = '.\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app'
$output1 = "results-lab22-card1-$([guid]::NewGuid().ToString('N')).json"
if (Test-Path (Join-Path $lab $output1)) { throw 'Choose another output name.' }
.\run-lab.ps1 $lab read-card.py biz-card-1.png --output $output1
```

### 5.2. Analyze the second card

Choose a separate output file for the second response:

```powershell
$output2 = "results-lab22-card2-$([guid]::NewGuid().ToString('N')).json"
if (Test-Path (Join-Path $lab $output2)) { throw 'Choose another output name.' }
.\run-lab.ps1 $lab read-card.py biz-card-2.png --output $output2
```

The reader accepts an optional image filename and defaults to
`biz-card-1.png`. Its `--output` argument is optional and defaults to
`results.json`; always choose a new output name if you want to preserve earlier
results.

## 6. Review and protect the JSON output

Each successful run writes the full Content Understanding response as UTF-8
JSON. You can confirm a saved file exists without printing its contact values:

```powershell
Get-Item (Join-Path $lab $output1) | Select-Object Name, Length
```

Open results locally only when needed. The JSON and console output can contain
personal contact information extracted from the cards. The result files are
Git-ignored, but that does not make their contents safe to publish. Do not
commit them or copy their values into this README.

## How the client works

[create-analyzer.py](create-analyzer.py):

1. Reads [biz-card.json](biz-card.json).
2. Loads `ENDPOINT` and `ANALYZER_NAME` from this folder's `.env`.
3. Creates an authenticated `ContentUnderstandingClient` using API version
   `2025-11-01`.
4. Calls `begin_create_analyzer(..., allow_replace=True)`, waits for the
   result, and checks that its status is `ready`.

[read-card.py](read-card.py):

1. Reads the selected local image bytes.
2. Calls `begin_analyze_binary` with the configured analyzer ID.
3. Waits for the analysis and checks that content and all five string-typed
   fields were returned.
4. Saves the full response using `result.as_dict()`.
5. Prints the extracted strings. An empty value is shown as
   `(not found on card)`; a missing field or non-string field is an error.

Relative image and output paths resolve against the lab folder; absolute paths
are accepted. Azure, file, and validation errors are reported to stderr with
exit code `1`.

## Troubleshooting, privacy, and costs

- **Missing endpoint or analyzer ID:** Set `ENDPOINT` and `ANALYZER_NAME` in
  this lab's `.env`. Never paste their values into a public transcript.
- **Authentication or authorization failure:** Confirm your Azure CLI session
  and that your identity has access to the configured Content Understanding
  resource.
- **Analyzer not found:** Confirm the resource endpoint and exact analyzer ID.
  Do not recreate an analyzer that already exists.
- **Image not found:** Check the filename and ensure the local image is in this
  lab folder, or pass an authorized absolute path.
- **Existing JSON result:** `results.json` is the default and is overwritten
  after a successful analysis. Use a new `--output` name as shown above.
- **Costs and cleanup:** Analyzer creation persists in Azure; analysis and
  model usage may incur charges. The isolated test created analyzer
  `lab22synthetic5c55dd8fc1d24509937d3ffef40f58da` in the configured
  resource; it was left in place. If no longer needed, verify the resource and
  analyzer ID, check for shared use, then delete **only that analyzer** in
  Content Understanding's analyzer management UI or with the SDK's
  `ContentUnderstandingClient.delete_analyzer(analyzer_id)` method. Do not
  delete the Foundry resource or its resource group.
- **Private data:** Card images, console output, and JSON results can contain
  personal information. The repository ignores `results.json` and
  `results-*.json`, but does not ignore the card PNGs. Check their status and
  contents before staging or sharing files; keep private data out of source
  control.

## Validation and conclusion

| Validation | Result |
|---|---|
| Reader help through `run-lab.ps1` | Completed with exit code `0`; confirmed the `image_file` and `--output` arguments without contacting Azure. |
| Missing-image dry run through `run-lab.ps1` | Returned exit code `1` as expected. The image read failed before client creation; no Azure request was made and no output file was created. |
| Existing shared Python environment | Python `3.13.17`, `azure-ai-contentunderstanding` `1.1.0`, `azure-identity` `1.25.3`, and `python-dotenv` `1.2.3` were present. No packages were installed or updated. |
| Isolated Azure live test | A later authorized test used a unique analyzer ID, forced `allow_replace=False` at the SDK boundary, and submitted an in-memory synthetic card. Both scripts completed; the result contained five nonempty string fields. The new analyzer remains in Azure. See the capture below. |
| Earlier live validation | The prior README recorded analyzer creation and successful analyses on October 30, 2026. That historical evidence is separated below and was not independently repeated during this update. |

The isolated run also established authentication, creation, and inference for
that unique analyzer at the time of the test. It did not validate the accuracy
of each extracted value or the availability of any existing analyzer.

## Captured output

The outputs below are from command runs on November 15, 2026, except where
explicitly marked historical. Local absolute paths are redacted. The failed
dry run is an intentional prerequisite check, not a successful analysis.

### 1. Reader help (November 15, 2026)

Command run from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app read-card.py --help
```

Captured output:

```text
usage: read-card.py [-h] [--output OUTPUT] [image_file]

Extract contact details from a business card.

positional arguments:
  image_file

options:
  -h, --help       show this help message and exit
  --output OUTPUT  JSON output path, relative to this lab folder unless
                   absolute.
HELP_EXIT_CODE=0
```

### 2. Missing-image dry run (November 15, 2026)

Command run from the repository root with a deliberately nonexistent image
and a new output name:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app read-card.py __dry_run_missing_image__.png --output __dry-run-output-not-created__.json
```

The merged stdout/stderr excerpt below has its channel order normalized; the
workspace path is redacted:

```text
Analyzing <workspace>\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app\__dry_run_missing_image__.png
Card analysis failed: [Errno 2] No such file or directory: '<workspace>\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app\__dry_run_missing_image__.png'
DRY_RUN_EXIT_CODE=1
DRY_RUN_OUTPUT_FILE_CREATED=no
```

The file read failed before credentials or an Azure client were used. The
specified output file was not created.

### 3. Isolated synthetic live run (November 15, 2026)

A one-off PowerShell/Python harness generated an image in memory with clearly
synthetic company, name, and title text, `TEST@EXAMPLE.INVALID`, and
`000-000-0000`. No existing business-card image was read. It used the existing
Python environment and configuration, generated the unique analyzer ID shown
below, and confirmed that ID returned HTTP 404 before creation.

The harness ran the actual `create-analyzer.py` and `read-card.py` entry
points. To eliminate the creation script's normal replacement behavior, it
overrode the SDK call in-process to send `allow_replace=False`; the checked-in
script itself was **not changed** and still uses `True` in normal use. It
intercepted the reader's image read and JSON output in memory, so no image or
result file was created or overwritten. The client console's field values were
withheld; the following is the harness's actual status output, not raw client
output:

```text
SYNTHETIC_PNG_BYTES=33081
SYNTHETIC_ANALYZER_ID=lab22synthetic5c55dd8fc1d24509937d3ffef40f58da
CARD_SOURCE=synthetic in-memory PNG; no existing card read
PREFLIGHT_ANALYZER=not found (HTTP 404)
create-analyzer.py=success
CREATE_ALLOW_REPLACE_ENFORCED=False
CREATE_READY_MESSAGE=True
read-card.py=success
ANALYSIS_SUCCESS_MESSAGE=True
SAVED_OUTPUT=in-memory JSON only
CONTENT_COUNT=1
FIELD_NAMES=Company,Name,Title,Email,Phone
STRING_FIELD_COUNT=5
NONEMPTY_FIELD_COUNT=5
PRINTED_FIELD_LABELS=5
FIELD_VALUES=withheld; only synthetic card was submitted
LIVE_RUN_EXIT_CODE=0
```

The result had all five string-typed fields and the client printed all five
labels; nonempty fields alone do not prove exact extraction accuracy. The test
made live Azure calls and created the persistent analyzer named above. It did
not replace an existing analyzer or alter local result files. The analyzer was
not deleted; see the cleanup guidance above.

A subsequent read-only SDK `get_analyzer` check of that ID returned:

```text
PERSISTED_ANALYZER_STATUS=ready
PERSISTED_BASE_ANALYZER=prebuilt-document
PERSISTED_FIELD_NAMES=Company,Email,Name,Phone,Title
READ_ONLY_CHECK_EXIT_CODE=0
```

### 4. Historical Azure output (October 30, 2026)

The previous version of this README recorded a live analyzer creation on
October 30, 2026. Its captured output was:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\22-develop-content-understanding-client-app create-analyzer.py -Install
```

This is a historical command only. The launcher's `-Install` switch continues
on to run the script, and the script uses `allow_replace=True`; do not rerun
this command when the analyzer ID already exists.

```text
Creating businesscardanalyzer
Analyzer 'businesscardanalyzer' created successfully.
Status: ready
```

This is historical output, not a result of the November 15 validation. The
earlier README also recorded successful live analyses of both cards and checks
of all five extracted values and saved JSON. Those contact values are
intentionally omitted. The local `results.json`,
`results-biz-card-1.json`, and `results-biz-card-2.json` files were checked
during this update only for JSON structure and field names, not for or against
their private contact values. The previous report's simulated failure tests
were not rerun.

The earlier record also reports that the resource's default Content
Understanding mappings were inspected, `prebuilt-document` supported the
schema, and the analyzer used `gpt-5.5` with `text-embedding-3-large`. Treat
those as historical resource-specific observations; verify current mappings
before creating anything.
