# Lab 20 - Analyze media with Content Understanding

[Microsoft Learn lab guide](https://microsoftlearning.github.io/mslearn-ai-vision/Instructions/Exercises/04-content-understanding.html) | [Vision labs](../README.md) | [Repository setup](../../README.md)

This walkthrough runs the repository's Python client against a **previously
published** Content Understanding analyzer and one of the supplied images. It
does not create or publish an analyzer. The Azure resource and compatible
analyzer must already exist.

## Table of contents

- [1. Verify prerequisites](#1-verify-prerequisites)
- [2. Configure the client](#2-configure-the-client)
- [3. Run the analysis client](#3-run-the-analysis-client)
- [4. Choose an image](#4-choose-an-image)
- [Configuration reference](#configuration-reference)
  - [What each `.env` setting means](#what-each-env-setting-means)
  - [Choose the published analyzer](#choose-the-published-analyzer)
- [Historical Azure setup](#historical-azure-setup)
- [Alignment with the guide](#alignment-with-the-guide)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [Live launcher run: November 15, 2026](#live-launcher-run-november-15-2026)
  - [Historical live tests: October 30, 2026](#historical-live-tests-october-30-2026)
    - [Historical Studio result: lion image](#historical-studio-result-lion-image)
    - [Historical simulated error tests](#historical-simulated-error-tests)

## 1. Verify prerequisites

Before you run the client, confirm that you have:

- Access to a Foundry resource with Content Understanding enabled.
- An analyzer already published in that resource. It must return a string
  field named `Description` and an array-of-strings field named `Tags`.
- This lab's `.env` settings and an authenticated identity. The client uses
  `DefaultAzureCredential`; for local Azure CLI authentication, sign in if
  necessary:

  ```powershell
  az login
  ```

The script sends the selected local image to Azure for analysis. Each analysis
is a live service request and may incur charges. The script does not create an
Azure resource, analyzer, model deployment, or role assignment.

## 2. Configure the client

From the repository root, open this lab's `.env`. The command below creates it
from the example only when it is missing, so it will not overwrite an existing
configuration:

```powershell
$lab = '.\4_Extract_Insights_From_Visual_Data_On_Azure\20-analyze-media-with-content-understanding'
if (-not (Test-Path "$lab\.env")) {
    Copy-Item "$lab\.env.example" "$lab\.env"
}
notepad "$lab\.env"
```

Set the resource root endpoint and the exact ID of your already-published
analyzer:

```dotenv
ENDPOINT="https://<foundry-resource>.services.ai.azure.com/"
ANALYZER="<your-published-analyzer-id>"
```

Save the file and close the editor. Do not replace the endpoint with a project
URL or an OpenAI URL ending in `/openai/v1/`. The analyzer ID is not a key,
deployment name, file path, or project name.

## 3. Run the analysis client

From the repository root, start the script with the shared launcher:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\20-analyze-media-with-content-understanding analyze-image.py
```

The normal command does not install packages. If this lab's dependencies are
missing from the shared `.labenv`, the install option installs the requirements
and then starts the client; enter anything other than `1`, `2`, or `3` at its
prompt to exit without submitting an image:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\20-analyze-media-with-content-understanding -Install
```

The validated Content Understanding SDK version is **1.1.0**; the requirements
allow `>=1.1.0,<2`.

## 4. Choose an image

At the client prompt, enter one of the following numbers and press Enter:

```text
Choose a file (1, 2, or 3), or anything else to exit:
```

| Input | Image |
| --- | --- |
| `1` | Giraffe: [image1.jpg](images/image1.jpg) |
| `2` | Elephant: [image2.jpg](images/image2.jpg) |
| `3` | Lion: [image3.jpg](images/image3.jpg) |

Wait for the client to print **Description** and **Tags**. It then displays the
same prompt again; enter another number to analyze another image, or enter
anything else (for example, `x`) to exit. You can also activate the shared
environment and run `python analyze-image.py` from this folder. Configuration
and image paths are resolved relative to the script, not the terminal's
current directory.

## Configuration reference

Use [.env.example](.env.example) as the template; the client loads the lab's
`.env` for its resource endpoint and published analyzer ID:

```dotenv
ENDPOINT="https://<foundry-resource>.services.ai.azure.com/"
ANALYZER=<your-published-analyzer-id>
```

This is the **Foundry resource root endpoint**, as required by the guide.
It is not the OpenAI URL ending in `/openai/v1/` and not a project URL ending
in `/api/projects/<project>`.

### What each `.env` setting means

| Variable | Meaning |
| --- | --- |
| `ENDPOINT` | The Azure resource that hosts Content Understanding and the published analyzer. It tells the client **where to send requests**. |
| `ANALYZER` | The ID of a published Content Understanding analyzer in that resource. It tells the service **which analysis definition to run**. |

### Choose the published analyzer

Replace `ANALYZER` with the exact ID of an analyzer published in the configured
resource. It is not an API key, model deployment name, file path, or project name.

The analyzer's saved schema, not its name, defines its behavior. This client
expects a **Description** and a list of **Tags** from an image-analysis schema.

The application reads and uses the setting as follows:

```python
analyzer_id = os.getenv("ANALYZER")
poller = client.begin_analyze(
    analyzer_id=analyzer_id,
    inputs=[AnalysisInput(data=file_bytes)]
)
```

In other words: **send this image to the configured resource and run the
published analyzer identified by `ANALYZER`**. The application then polls
for completion and prints the returned `Description` and `Tags`.

The analyzer already exists in Azure; setting this variable does not create
or publish it. Its ID is scoped to the resource specified by `ENDPOINT`.
Changing the endpoint to another resource requires an analyzer with that ID
in the new resource.

If you select another analyzer through Studio or the SDK, use its exact ID and ensure
its schema still returns `Description` as a string and `Tags` as an array of
strings. Otherwise, requests may fail with an analyzer-not-found error or the
application may reject the returned fields.

The script uses `DefaultAzureCredential` with Microsoft Entra authentication
and API version **2025-11-01**. API keys remain disabled. Existing environment
variables take precedence over `.env`, following `load_dotenv` defaults.

## Historical Azure setup

Reused the existing resource rather than provisioning another:

| Setting | Value |
| --- | --- |
| Resource group | `<resource-group>` |
| Foundry resource | `<foundry-resource>` |
| Region | The configured resource's region |
| Analyzer ID | The published analyzer selected by `ANALYZER` |
| Base analyzer | `prebuilt-image` |
| Completion model | `gpt-5.5` |
| Existing completion deployment | Your configured completion deployment |

Content Understanding previously had no model defaults or custom analyzers.
The recorded setup configured resource-level defaults. In this example,
model identifiers are retained but deployment values are placeholders;
substitute the actual deployment names from your resource:

```json
{
  "modelDeployments": {
    "gpt-5.5": "<your-completion-deployment>",
    "text-embedding-3-large": "<your-embedding-deployment>"
  }
}
```

Published the custom analyzer with this guide-aligned schema:

```json
{
  "baseAnalyzerId": "prebuilt-image",
  "description": "Lab image analysis: generate an image description and searchable tags.",
  "models": {
    "completion": "gpt-5.5"
  },
  "fieldSchema": {
    "name": "image_metadata",
    "fields": {
      "Description": {
        "type": "string",
        "method": "generate",
        "description": "Image description"
      },
      "Tags": {
        "type": "array",
        "method": "generate",
        "description": "Image tags",
        "items": {
          "type": "string"
        }
      }
    }
  }
}
```

Analyzer creation completed with status `ready`, and its saved schema was
retrieved to verify persistence. The service rejected an initial hyphenated
analyzer ID; the published analyzer ID used for this lab uses underscores.

No new model deployment, Azure resource, API key, or role assignment was
created. The defaults and analyzer are persistent Azure-side changes.
Content Understanding analysis and the underlying models incur usage charges.

## Alignment with the guide

[analyze-image.py](analyze-image.py) implements the guide's:

- **Add references** imports for the client, analysis models, Azure errors,
  and `DefaultAzureCredential`.
- **Set up Content Understanding client** with the configured endpoint and API version.
- File selection for images `1`, `2`, and `3`.
- **Analyze the file** call using
  `client.begin_analyze(analyzer_id=analyzer_id, inputs=[AnalysisInput(data=file_bytes)])`.
- Polling with `poller.result()` and displaying generated descriptions and tags.

Additional safeguards validate configuration and returned fields, close the
credential/client, and report configuration, file, and Azure errors with a
nonzero exit code.

### Studio and storage distinction

The guide teaches analyzer creation through **Content Understanding Studio**,
using a storage account for Studio project assets. This setup created and
published the equivalent analyzer through the SDK instead.

**No Studio project or storage account was created, and no browser UI was
automated.** The working Python client submits local image bytes directly, so
it does not require Blob Storage. If you need to complete every portal step,
follow the guide's storage/project creation and upload steps separately.

The existing supported GPT-5.5 model was used instead of deploying the guide's
example GPT-5.2 model. The live `prebuilt-image` analyzer explicitly listed
GPT-5.5 as supported.

## Validation and conclusion

| Evidence | What it establishes |
|---|---|
| Current live launcher run, November 15, 2026 | The actual workspace launcher ran the Python client, analyzed image 1, printed a nonempty description and ten tags, and exited with code `0`; the sanitized output is below. |
| Historical live tests, October 30, 2026 | Earlier runs analyzed all three images and the separate `lion.jpg`; these results are summarized below and are not results from the November 15 run. |
| Code and paths | `analyze-image.py` reads `images/image1.jpg` through `images/image3.jpg`, prompts as documented, and requires `Description` and `Tags` in the analyzer response. |
| Limits | The current run tests one live image request, not the Studio workflow or all three images. It does not create or modify Azure resources or analyzer configuration. |

**Conclusion:** With an existing resource and published analyzer configured, the client sends a selected image to Content Understanding and displays the returned description and tags. Review the schema and results for your own analyzer; future outputs may differ.

## Captured output

### Live launcher run: November 15, 2026

This is the actual output from a run of the command above, from the repository
root. The launcher exited with code `0`; input `1` selected the giraffe image,
and `x` exited at the next prompt. The input values are not echoed by the
client. The analyzer ID and absolute workspace path are redacted; the
description and tags are unchanged.

The launcher was invoked as:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\20-analyze-media-with-content-understanding analyze-image.py
```

```text
Choose a file (1, 2, or 3), or anything else to exit: Analyzing with <analyzer-id> analyzer...
  File: <workspace-path>\4_Extract_Insights_From_Visual_Data_On_Azure\20-analyze-media-with-content-understanding\images\image1.jpg

Description:
A giraffe stands in a dry golden savanna grassland under a vivid blue sky with large white clouds in the background.

Tags:
  - giraffe
  - savanna
  - wildlife
  - Africa
  - grassland
  - animal
  - nature
  - blue sky
  - clouds
  - safari

Choose a file (1, 2, or 3), or anything else to exit:
```

### Historical live tests: October 30, 2026

The actual workspace launcher ran the actual script with inputs `1`, `2`,
`3`, and `quit`. All three live Azure analyses passed:

| Image | Verified description and tags |
| --- | --- |
| Giraffe | Giraffe in dry golden savanna grassland; tags included giraffe, savanna, wildlife |
| Elephant | Front-facing African elephant with tusks in tall grass; tags included elephant, tusks, grassland |
| Lion | Male lion with a dark mane in golden grass; tags included lion, mane, big cat |

Assertions checked three nonempty descriptions, three tag lists, recognition
of each expected animal, and exit code `0`.

The guide's separate [lion.jpg](lion.jpg) was also analyzed live. It returned
a male lion sitting in tall savanna grass, with tags including lion, male lion,
savanna, grassland, and wildlife.

These were real Content Understanding requests, not mocked responses.

#### Historical Studio result: lion image

The user-provided local lion analysis screenshot shows
the configured analyzer processing [lion.jpg](lion.jpg) in the Studio
**Test** tab. The **Fields** pane displays the generated `Description` and
**12 tags**, including lion, male lion, savanna, grassland, wildlife, and big cat.

The description shown is:

> A male lion with a full mane sits in tall grass on an open savanna.
> The background is softly blurred, showing a lone tree and expansive
> grassland under a pale sky.

The screenshot is kept locally as `lion-cu-analysis.jpg` and intentionally
excluded from Git because Studio screenshots may expose account information.

This screenshot documents the Studio analysis result supplied by the user;
it is separate from the SDK and launcher tests described above.

#### Historical simulated error tests

Separate simulated error tests verified:

- OpenAI endpoint paths are rejected with an explicit configuration error.
- Placeholder analyzer IDs are rejected.
- Azure service errors are printed and exit with code `1`.

Historical note: the October 30 implementation work was limited to this lab's
code, configuration, requirements, and README; other labs and supplied images
were not modified. The November 15 documentation update changed only this
README.
