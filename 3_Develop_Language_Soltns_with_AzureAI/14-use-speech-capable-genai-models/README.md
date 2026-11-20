# Lab 14 - Use speech-capable generative AI models

[Language labs](../README.md) | [Repository setup](../../README.md)

This lab uses two Azure OpenAI deployments: one generates speech from text and
the other transcribes a supplied WAV recording. It does not record from a
microphone. The scripts use Entra authentication through
`DefaultAzureCredential`; they do not accept API keys.

| Runtime folder | Exercise |
|---|---|
| [generate-speech](generate-speech/) | Generate speech from a fixed text prompt, save an MP3, and attempt local playback. |
| [transcribe-speech](transcribe-speech/) | Play the included WAV, send it to a transcription deployment, and print the transcript. |

## Table of contents

- [1. Configure Azure access](#1-configure-azure-access)
- [2. Install the lab dependencies](#2-install-the-lab-dependencies)
- [3. Generate speech](#3-generate-speech)
- [4. Transcribe the sample recording](#4-transcribe-the-sample-recording)
- [How the prompts and files work](#how-the-prompts-and-files-work)
- [Troubleshooting, costs, and privacy](#troubleshooting-costs-and-privacy)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Read-only dry-run checks](#1-read-only-dry-run-checks)
  - [2. Live transcription run](#2-live-transcription-run)
  - [3. Historical live results](#3-historical-live-results)

## 1. Configure Azure access

Before calling a model, make sure you have access to an Azure OpenAI resource
with compatible speech-generation and transcription deployments. Sign in with
the Azure account that has permission to use those deployments:

```powershell
az login
```

From the repository root, create each local `.env` file only if it is missing.
These guarded commands preserve any existing configuration:

```powershell
$generateEnv = '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\.env'
if (-not (Test-Path -LiteralPath $generateEnv)) {
    Copy-Item -LiteralPath '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\.env.example' -Destination $generateEnv
}

$transcribeEnv = '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\.env'
if (-not (Test-Path -LiteralPath $transcribeEnv)) {
    Copy-Item -LiteralPath '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\.env.example' -Destination $transcribeEnv
}
```

Edit each `.env` locally and provide:

| Variable | Value |
|---|---|
| `MODEL_ENDPOINT` | The HTTPS endpoint for your Azure OpenAI resource, such as `https://<resource>.openai.azure.com/`. Use the resource endpoint, **not** a Foundry project URL. |
| `MODEL_NAME` | The exact deployment name for that step: a speech-generation deployment in `generate-speech\.env`, and a transcription deployment in `transcribe-speech\.env`. |

Keep these files private and do not paste or print their contents. The two
clients use API version `2025-04-01-preview`; the generation client requests an
Entra token for `https://cognitiveservices.azure.com/.default`, while the
transcription client uses `https://ai.azure.com/.default`.

## 2. Install the lab dependencies

The shared launcher uses a repository-root `.labenv` virtual environment. Create
it if needed, then install the requirements for both runtime folders:

```powershell
if (-not (Test-Path -LiteralPath '.\.labenv\Scripts\python.exe')) {
    python -m venv .labenv
}

.\.labenv\Scripts\python.exe -m pip install -r .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\requirements.txt
.\.labenv\Scripts\python.exe -m pip install -r .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\requirements.txt
```

The launcher’s `-Install` switch installs requirements **and then immediately
runs the selected script**. Use the separate installation commands above if
you want to install packages without making a model request.

## 3. Generate speech

First protect any existing `generate-speech\speech.mp3`: the script always
writes to that fixed filename and a successful run replaces it. For example,
make a uniquely named backup from the repository root:

```powershell
$output = '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\speech.mp3'
if (Test-Path -LiteralPath $output) {
    $backup = '.\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\speech.' + [guid]::NewGuid().ToString('N') + '.mp3'
    Copy-Item -LiteralPath $output -Destination $backup
    Write-Host "Backed up the existing audio to $backup"
}
```

Run the generation script from the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\ generate-speech.py
```

The client sends the text `My voice is my passport!` with voice `alloy` and the
instruction `Speak in a serious tone.` It saves the generated MP3 beside the
script and then attempts to play it. The console shows the generation step,
the saved MP3 path, and playback progress. The generated MP3 is intentionally
excluded from Git. Be present and set a comfortable volume before starting
playback.

## 4. Transcribe the sample recording

The included [speech.wav](transcribe-speech/speech.wav) is played first and
then sent to the configured transcription deployment. No microphone or typed
prompt is required. Set a comfortable volume and run:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\ transcribe-speech.py
```

The terminal shows playback and transcription progress, then prints the result
under `Transcript:`. The script does not save a separate transcript file. If
local playback fails, the script's exception handler prints the error and
transcription may not start.

## How the prompts and files work

| Exercise | Input sent to Azure | Local behavior |
|---|---|---|
| Speech generation | Fixed text `My voice is my passport!`, voice `alloy`, serious-tone instruction. There is no interactive prompt. | Writes `generate-speech\speech.mp3`, replacing that file if it already exists, then attempts playback. |
| Speech transcription | The bytes in `transcribe-speech\speech.wav`. There is no typed prompt. | Plays the included recording, requests text transcription, and prints the returned text. |

To try different spoken text, change the `input` string in
[generate-speech.py](generate-speech/generate-speech.py) before running it. The
task's transcription input remains the included WAV unless you intentionally
change the script or sample file.

## Troubleshooting, costs, and privacy

- **Authentication or authorization error:** Sign in with `az login`, confirm
  the active account and resource access, and check that the deployment is
  available to that resource.
- **Unsupported API version or endpoint:** Confirm that `MODEL_ENDPOINT` is
  the Azure OpenAI resource endpoint, not a Foundry project endpoint. The
  checked-in clients use API version `2025-04-01-preview`.
- **Deployment not found:** `MODEL_NAME` must be the deployment name, not just
  a model family name. Check the generation and transcription `.env` files
  independently.
- **Playback error:** Check the local audio device and playback permissions.
  Transcription plays the WAV before making the API call, so a playback failure
  can prevent the request.
- **Charges:** Each successful generation or transcription request can incur
  Azure usage charges. Installing the Python packages does not call Azure.
- **Privacy:** Do not send sensitive recordings or disclose endpoint,
  configuration, or credential values. The supplied sample is the input shown
  in this lab.

## Validation and conclusion

The two scripts create an `AzureOpenAI` client using `DefaultAzureCredential`
and the configured deployment. Speech generation streams audio to a local MP3;
transcription submits the supplied WAV and requests text output. A local syntax
check does not verify Azure access. A live transcription returned nonempty text
in the run below. The documented launcher always plays the WAV before its API
request and has no playback-disable option, so that launcher was not used for
the headless live check. This did not test physical speaker playback.

## Captured output

The read-only checks below were run on November 15, 2026, from the repository
root. They parsed the scripts without executing them and confirmed that the
launcher and required local inputs existed. A subsequent live transcription
used the configured deployment. No resources were created or changed, and no
files were modified. The first live attempt did invoke the script's original
playback function because the initial in-memory patch did not reach the
function's globals; it returned text but is not treated as playback-free
validation. One corrected live request skipped playback successfully.

### 1. Read-only dry-run checks

The preflight parsed both Python source files without importing or executing
them. This was the Python syntax-check command, run from the repository root:

```powershell
$python = '.\.labenv\Scripts\python.exe'
& $python -c "import ast, pathlib; files=[pathlib.Path(r'3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\generate-speech.py'), pathlib.Path(r'3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\transcribe-speech.py')]; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in files]; print(f'PASS: parsed {len(files)} Python scripts without executing them')"
```

The excerpt below is verbatim from the successful check; the file-existence
checks that followed also passed.

```text
PASS: parsed 2 Python scripts without executing them
PASS: found run-lab.ps1
PASS: found 3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\README.md
PASS: found 3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\generate-speech.py
PASS: found 3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\requirements.txt
PASS: found 3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\transcribe-speech.py
PASS: found 3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\speech.wav
```

An initial attempt to pass the file list through PowerShell's automatic `$args`
variable failed with a Python `SyntaxError` and exit code `1`; the corrected
read-only check above passed. This was a test-command quoting issue, not a lab
script failure. The corrected syntax check and README link/command validation
exited with code `0`.

### 2. Live transcription run

The local configuration contained both required settings; their values were
not displayed. The included WAV was 194,444 bytes. The documented
`run-lab.ps1` command was not used because the script unconditionally plays the
recording before sending it to Azure and does not provide a playback-disable
switch. Instead, an in-memory harness called the script's `main()` with its
`playsound` function replaced by a no-op; it did not edit the script or write
the transcript to disk. The first harness attempt did not correctly replace
the function and may have played the WAV; after verifying the function's
globals, the corrected run skipped playback.

The corrected transcription request returned the following output verbatim:

```text
[Playback skipped; no playback device used.]
Oh, man. On the other side of the screen, it all looks so easy.
```

The client does not print an HTTP status; the nonempty text confirms that this
request returned a transcript. Two live transcription requests were made in
total during this check, so Azure usage charges may apply. No API credentials,
endpoint, deployment name, or transcript file were printed or saved.

The first attempt, which did not suppress playback, returned:

```text
Oh man, on the other side of the screen, it all looks so easy.
```

It is recorded for completeness, not as evidence of playback-free execution.

### 3. Historical live results

These are earlier outcomes recorded in the individual runtime guides, not
results from the live request above:

- A previous speech-generation API validation produced a 38,400-byte MP3.
  Playback was skipped, so that run did not verify physical speakers.
- A previous transcription validation using the resource endpoint and the
  documented API version returned HTTP 200 with a nonempty transcript. The
  transcript text is not reproduced here.

Speech generation was not repeated for this README update, so the existing
`speech.mp3` was not replaced. Consult [Generate speech](generate-speech/README.md) and
[Transcribe speech](transcribe-speech/README.md) for the recorded historical
context and implementation details.
