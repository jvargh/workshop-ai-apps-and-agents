# Lab 21 - Extract information from multimodal content

[Official Microsoft Learn exercise](https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/01-content-understanding.html) | [Visual-data labs](../README.md) | [Repository setup](../../README.md)

This exercise explores Azure Content Understanding with an invoice, a slide
image, a voicemail, and a video. **This folder is an incomplete starter, not a
runnable application.** It has no Python entry point, dependency list, or
configuration template. The `content` folder currently contains local sample
files, but those files are not tracked in Git. No analyzer, Azure resource, or
end-to-end application is supplied here.

## Table of contents

- [1. Read-only local preflight](#1-read-only-local-preflight)
- [2. Prepare the Azure exercise safely](#2-prepare-the-azure-exercise-safely)
- [3. Inspect a document with prebuilt analyzers](#3-inspect-a-document-with-prebuilt-analyzers)
- [4. Build and test custom analyzers](#4-build-and-test-custom-analyzers)
  - [4.1. Invoice documents](#41-invoice-documents)
  - [4.2. Slide images](#42-slide-images)
  - [4.3. Voicemail audio](#43-voicemail-audio)
  - [4.4. Conference video](#44-conference-video)
- [5. Captured output](#5-captured-output)
  - [5.1. Read-only inventory](#51-read-only-inventory)
  - [5.2. Launcher preflight](#52-launcher-preflight)
- [6. Validation and conclusion](#6-validation-and-conclusion)
- [7. Privacy, costs, and cleanup](#7-privacy-costs-and-cleanup)

## 1. Read-only local preflight

Run these checks in **PowerShell from the repository root**. They list file
names only; they do not open or upload the sample content.

```powershell
$lab = '.\4_Extract_Insights_From_Visual_Data_On_Azure\21-extract-info-from-mm-content'
Write-Output 'Top-level files:'
Get-ChildItem -LiteralPath $lab -File | ForEach-Object Name
Write-Output 'Python/dependency/config files:'
$candidates = Get-ChildItem -LiteralPath $lab -Recurse -File |
    Where-Object { $_.Extension -in '.py', '.ps1' -or $_.Name -in 'requirements.txt', '.env.example' } |
    ForEach-Object Name
if ($candidates) { $candidates } else { '(none)' }
Write-Output 'Local content files:'
if (Test-Path -LiteralPath (Join-Path $lab 'content') -PathType Container) {
    Get-ChildItem -LiteralPath (Join-Path $lab 'content') -File | ForEach-Object Name
} else {
    Write-Output '(content folder not present)'
}
```

The shared launcher is useful here only as a **negative preflight**. From the
repository root, it checks for a Python entry point and is expected to stop
with “No Python scripts were found.” The launcher creates the shared `.labenv`
when it is missing, so run this check only if that environment already exists.
Do not add `-Install`.

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\21-extract-info-from-mm-content\
```

This folder has no `requirements.txt`. Do not create a placeholder script or
`.env` and treat it as a working client.

## 2. Prepare the Azure exercise safely

The official exercise is a **portal-based walkthrough**, not code that can be
started with `run-lab.ps1`.

1. Read the [official exercise](https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/01-content-understanding.html)
   before preparing Azure. It covers Foundry, Content Understanding Studio,
   analyzer schemas, and the four sample modalities.
2. Use an authorized Foundry resource and project in a supported region. Check
   the exercise's current model, quota, and region requirements against your
   subscription. The official flow also uses a storage account in the same
   resource group and a `content-understanding` container. Check for existing
   resources and containers first; do not create a second resource or project
   unless you have approval.
3. Use the existing local `content` files when they are available. For a fresh
   clone, obtain the sample archive from the official exercise and extract it
   into a **new, empty directory**; do not overwrite this folder's existing
   files. The media and documents can contain personal or identifying details.
4. Before connecting a resource in Content Understanding Studio, check its
   existing model defaults and storage configuration. The exercise may require
   a storage account/container and model deployments. Review permissions and
   cost before creating or enabling anything.

This README records the local preflight only. No Azure sign-in, project setup,
storage setup, analyzer creation, or content upload was performed.

## 3. Inspect a document with prebuilt analyzers

In the Foundry portal, use the **Services** area and open the Content
Understanding **Document Layout Analyzer** playground. Upload the authorized
`invoice-1234.pdf` sample and run the analyzer. Review the formatted view and
raw result for text, tables, and document structure. If available, compare
with the **OCR/Read** analyzer; Read focuses on text, while Layout also returns
structural information.

This is a manual portal exercise; there is no corresponding local command.
Do not infer specific extracted values from this README. Compare the output
with the source invoice yourself.

## 4. Build and test custom analyzers

Content Understanding Studio uses schema field names, types, and natural
language field descriptions to specify what to extract. The descriptions below
are **schema guidance**, not prompts sent by a local chat application. The
Studio steps create or update persisted cloud projects and analyzers; first
check for existing names and use a distinct name if necessary.

For each modality:

1. Create a custom-schema project in Content Understanding Studio and confirm
   that it uses the intended Foundry resource and storage.
2. Upload the indicated first sample, choose the matching template, define and
   save the fields below, then run analysis.
3. Review both the Fields view and the raw result. Compare values with the
   source; treat missing, low-confidence, or uncertain values as needing
   review.
4. Build an analyzer only after checking that its name will not replace an
   existing analyzer. Test it with the indicated second sample and review the
   result again.

### 4.1. Invoice documents

1. Create an invoice-analysis project and upload `invoice-1234.pdf`.
2. Select the **Invoice** template. Review its suggested schema; remove fields
   that are not needed and use schema suggestions only after checking whether
   they will replace your current edits.
3. Add a string field named `TotalQuantity`, with a description that asks for
   the total number of items on the invoice.
4. Save the schema, run analysis, and compare the extracted fields with
   `invoice-1234.pdf`.
5. If approved and the analyzer name is unused, build the example
   `invoiceanalyzer`. Test it with `invoice-1235.pdf` and compare the output
   with that invoice.

### 4.2. Slide images

1. Create a slide-analysis project and upload `slide-1.jpg`. Choose the
   **Image analysis** template.
2. Define these fields and natural-language descriptions:

   | Field | Type | Description to enter |
   |---|---|---|
   | `Title` | String | Identify the slide title. |
   | `Summary` | String | Summarize the slide's main message. |
   | `Charts` | Integer | Count the charts shown on the slide. |
   | `QuarterlyRevenue` | List of objects | Extract revenue for each quarter. Include `Quarter` (String) and `Revenue` (Number). |
   | `ProductCategories` | List of objects | Extract product categories and their revenue share. Include `ProductCategory` (String) and `RevenuePercentage` (Number). |

3. Save and run analysis on `slide-1.jpg`. Review the values against the chart;
   do not treat generated descriptions or numbers as verified facts.
4. If approved and the name is unused, build the example `slideanalyzer`.
   Test it with `slide-2.jpg`. The exercise notes that this second slide has no
   product-category revenue breakdown, so an absent value is not by itself a
   failure.

### 4.3. Voicemail audio

1. Create a voicemail-analysis project and upload `call-1.mp3`. Choose the
   **Audio analysis** template and review the transcription preview.
2. Define these fields and natural-language descriptions:

   | Field | Type | Description to enter |
   |---|---|---|
   | `Caller` | String | Identify the person who left the message. |
   | `Summary` | String | Summarize the message. |
   | `Actions` | String | Identify any requested actions. |
   | `CallbackNumber` | String | Extract the return-call phone number. |
   | `AlternativeContacts` | List of strings | Extract any alternative contact details. |

3. Save and run analysis. Compare the transcription and extracted details
   with the audio, especially names and phone numbers.
4. If approved and the name is unused, build the example
   `voicemailanalyzer`. Test it with `call-2.mp3` and review the result.

### 4.4. Conference video

1. Create a conference-video project and upload `meeting-1.mp4`. Choose the
   **Video analysis** template and review the transcription preview.
2. Define these fields and natural-language descriptions:

   | Field | Type | Description to enter |
   |---|---|---|
   | `Summary` | String | Summarize the discussion. |
   | `Participants` | Integer | Count the meeting participants. |
   | `ParticipantNames` | List of strings | Identify the meeting participants by name. |
   | `SharedSlides` | List of strings | Describe slides presented during the meeting. |
   | `AssignedActions` | List of objects | Extract tasks assigned during the meeting; each object has `Task` (String) and `AssignedTo` (String). |

3. Save and run analysis. Review the results for each video segment and
   compare names, slides, and action assignments with the recording.
4. If approved and the name is unused, build the example `meetinganalyzer`.
   Test it with `meeting-2.mp4`. Video analysis can take longer than the
   document or image tests.

The example analyzer names above come from the exercise. They are not created
by this repository. Do not replace an existing analyzer to reuse a name.

## 5. Captured Output

The output below is from local commands actually run in this workspace. Paths
are shown relative to the repository or have the workspace root redacted.
Media contents, extracted values, credentials, and Azure identifiers were not
read or captured.

### 5.1. Read-only inventory

The read-only inventory command in section 1 exited with code `0`.

```text
Top-level files:
README.md
Python/dependency/config files:
(none)
Local content files:
call-1.mp3
call-2.mp3
invoice-1234.pdf
invoice-1235.pdf
meeting-1.mp4
meeting-2.mp4
slide-1.jpg
slide-2.jpg
```

### 5.2. Launcher preflight

Executed from the repository root; the shared `.labenv` already existed. The
command did not use `-Install`, run Python code, or contact Azure. This excerpt
replaces the absolute workspace path with `<workspace-root>`; the omitted
PowerShell diagnostic lines only identify the launcher line and exception
category.

```text
Command: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\21-extract-info-from-mm-content\
No Python scripts were found in <workspace-root>\4_Extract_Insights_From_Visual_Data_On_Azure\21-extract-info-from-mm-content\
ProcessExitCode=1
```

This is a failed local preflight, not a failed Azure analysis. No analyzer
outputs are available from this starter, and no Azure command or resource
mutation was performed.

## 6. Validation and conclusion

| Check | Result |
|---|---|
| Folder contents | README and local content files; no Python script, dependency file, or `.env.example` was found. |
| Shared launcher | Exited with code `1` because the folder contains no Python entry point. |
| Azure exercise | Not run. No Azure authentication, content upload, analyzer creation, or service request was attempted. |
| Dependencies | None installed. The launcher was not given `-Install`. |
| Resource changes | None. |

**Conclusion:** Lab 21 is currently a design walkthrough for the official
portal exercise, not a completed or runnable local app. Use the official
exercise for the hands-on Azure workflow. A local implementation and its
requirements/configuration must be added and validated before this folder can
claim an end-to-end run.

## 7. Privacy, costs, and cleanup

- Review source files and permissions before uploading documents, audio, or
  video. Do not publish transcripts, extracted contact details, or raw
  responses.
- Creating projects, storage, model deployments, and analyzers can change
  Azure resources and may incur charges. Use only approved resources, check
  existing objects first, and avoid enabling automatic deployments without
  cost and permission review.
- The official exercise includes cleanup guidance. Do not delete a shared
  resource group or resources that predate your exercise; follow your
  organization's cleanup process for resources you created yourself.
