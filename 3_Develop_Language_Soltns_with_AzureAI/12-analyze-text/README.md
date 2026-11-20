# Lab 12 - Analyze text

[Language labs](../README.md) | [Repository setup](../../README.md)

This lab runs the checked-in Python client against the five sample reviews in
[`text-analysis/reviews`](text-analysis/reviews/). Azure AI Language detects
each review's language, named entities, and personally identifiable
information (PII), then returns a redacted version when PII is found.

## Table of contents

- [1. Prepare Azure AI Language access](#1-prepare-azure-ai-language-access)
- [2. Configure the endpoint and sign in](#2-configure-the-endpoint-and-sign-in)
- [3. Install dependencies](#3-install-dependencies)
- [4. Run the analysis](#4-run-the-analysis)
- [What the client does](#what-the-client-does)
- [Privacy, costs, and troubleshooting](#privacy-costs-and-troubleshooting)
- [Captured output](#captured-output)
- [Validation and conclusion](#validation-and-conclusion)

## 1. Prepare Azure AI Language access

Use an existing Azure AI resource whose endpoint supports the Language service.
The signed-in identity must be allowed to submit Language analysis requests.
This lab's Python script does not create or update Azure resources.

The client uses `DefaultAzureCredential` and Azure CLI sign-in. It does not use
an API key or a Foundry project endpoint. Requests are sent to the configured
resource and may incur service charges.

## 2. Configure the endpoint and sign in

Run these commands in **PowerShell from the repository root**. The first
command preserves an existing local `.env`; copy the template only when the
file is missing:

```powershell
$runtime = '.\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis'
if (-not (Test-Path "$runtime\.env")) {
    Copy-Item "$runtime\.env.example" "$runtime\.env"
}
az login
```

Open `text-analysis\.env` locally and set `FOUNDRY_ENDPOINT` to the endpoint
for the Azure AI resource supporting Language, for example
`https://<resource>.services.ai.azure.com/`. Do not use a Foundry project URL
or share the `.env` contents. If you are already signed in, you do not need to
run `az login` again.

To check Azure CLI authentication without printing a token, run:

```powershell
az account get-access-token --resource https://cognitiveservices.azure.com --query expiresOn --output tsv
```

## 3. Install dependencies

The dependencies are listed in
[`text-analysis/requirements.txt`](text-analysis/requirements.txt). When they
are not already installed in the repository's shared `.labenv`, use:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis\ text-analysis.py -Install
```

The `-Install` option installs the requirements and then starts the analysis;
it is not an install-only command. Confirm the endpoint and sign-in first.
Package installation is not needed on subsequent runs.

## 4. Run the analysis

From the repository root, start the client without `-Install`:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis\ text-analysis.py
```

The launcher sets `text-analysis` as the working directory so the script can
find the relative `reviews` folder. There is no interactive prompt: wait while
the application processes each review. For every file, it prints the original
text, detected language, named entities and categories, PII entities, and
redacted text when PII was detected. Review the categories and redaction, but
do not copy raw output into a public report or issue.

## What the client does

[`text-analysis.py`](text-analysis/text-analysis.py) uses
`TextAnalyticsClient` to make separate language-detection, entity-recognition,
and PII-recognition calls for each review. It prints results to the console;
it does not ask a question, request sentiment or key phrases, or write a
results file. The endpoint template is
[`text-analysis/.env.example`](text-analysis/.env.example).

## Privacy, costs, and troubleshooting

- The program prints each **unredacted review and detected PII before** it
  prints the service's redacted version. Treat the full console output as
  sensitive; use only approved sample text and redact any captured output.
- Processing the five reviews submits up to 15 analysis operations (language,
  entities, and PII per review). Azure AI Language usage may be billable.
- If authentication fails, sign in with `az login` and confirm that the active
  identity can use the configured resource.
- If the endpoint is missing or invalid, check `FOUNDRY_ENDPOINT` in this
  lab's `text-analysis\.env`. The endpoint must support Language; a Foundry
  project URL is not interchangeable.
- The script catches exceptions and prints them, but does not set a failure
  exit code when it catches one. Check that results were printed for all five
  reviews rather than relying on the process exit code alone.

## Captured output

The following is a **redacted excerpt** from a real run of the command in
section 4 on November 15, 2026. Original review text, entity values, and
redacted review bodies are replaced or omitted to avoid exposing sample
content. Category names and language results are retained from the captured
output.

```text
-------------
review1.txt
[original review text omitted]

Language: English

Entities
    [entity text redacted] (Location)
    ...

PII Entities
    [PII value redacted] (PersonType)
    ...
Redacted Text: [review text redacted]

-------------
review5.txt
[original review text omitted]

Language: French

Entities
    [entity text redacted] (Location)
    ...

PII Entities
    [PII value redacted] (PersonType)
Redacted Text: [review text redacted]
```

In the same run, `review1.txt` through `review4.txt` were detected as English
and `review5.txt` as French. The launcher process exited with code `0`, and
the output included analysis results for all five files. Azure CLI token
precheck also exited with code `0`; the token itself was not printed. The
captured categories above are an excerpt, not a complete transcript.

## Validation and conclusion

The analysis command completed against the configured Azure AI Language
resource and returned results for all five reviews. It made no resource
creation or update. The run did submit language, entity, and PII analysis
requests, which may incur charges; the output was filtered before being
recorded here to omit review contents and entity values.

This client demonstrates language detection, named-entity recognition, and
PII recognition/redaction on text files. It does not establish that the same
results will be returned for other text or future service versions.
