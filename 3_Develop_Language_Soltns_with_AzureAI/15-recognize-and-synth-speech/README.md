# Lab 15 - Recognize and synthesize speech

[Language labs](../README.md) | [Repository setup](../../README.md)

This lab runs the [voicemail client](voice-mail/voice-mail.py) with Azure
Speech. It synthesizes a greeting from text you type, or plays the supplied
WAV messages and sends them for speech recognition. The menu calls its first
option “Record a greeting,” but it does not record from a microphone.

## Table of contents

- [1. Prepare the runtime and configuration](#1-prepare-the-runtime-and-configuration)
- [2. Start the client](#2-start-the-client)
- [3. Synthesize a greeting](#3-synthesize-a-greeting)
- [4. Transcribe the sample messages](#4-transcribe-the-sample-messages)
- [How the client works](#how-the-client-works)
- [Troubleshooting, privacy, and cleanup](#troubleshooting-privacy-and-cleanup)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Local preflight](#1-local-preflight)
  - [2. Menu-exit dry run](#2-menu-exit-dry-run)
  - [3. Live recognition of one supplied sample](#3-live-recognition-of-one-supplied-sample)

## 1. Prepare the runtime and configuration

Run commands from the repository root in PowerShell. Keep an existing `.env`;
copy the example only when the runtime does not already have one:

```powershell
$runtime = '.\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail'
if (-not (Test-Path "$runtime\.env")) {
    Copy-Item "$runtime\.env.example" "$runtime\.env"
}
```

Open `voice-mail\.env` and set `FOUNDRY_ENDPOINT` to the endpoint for a
Speech-capable Azure AI resource. The example shows the expected URL shape:
`https://<speech-resource>.services.ai.azure.com/`. Do not paste credentials
or endpoint details into this README or captured output. The code creates a
`DefaultAzureCredential`; sign in with `az login` if your local Azure CLI
identity is not already authenticated and has access to the resource.

The script reads `FOUNDRY_KEY`, but does not use it to authenticate. It uses
the configured `FOUNDRY_ENDPOINT` and the credential chain instead. See the
[runtime guide](voice-mail/README.md) and
[`.env.example`](voice-mail/.env.example) for the configuration files.

## 2. Start the client

The launcher runs the script with `voice-mail` as its working directory, which
is needed for the relative `messages` folder. If the required packages are
already installed in the repository's shared `.labenv`, start without
installing:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail\ voice-mail.py
```

If you intentionally need to install the listed requirements into that shared
environment, use `-Install` instead. It installs packages and then launches
the client; it does not stop after installation:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail\ voice-mail.py -Install
```

At the menu, enter `3` to exit without synthesizing or transcribing. The
client returns to PowerShell without an exit message.

## 3. Synthesize a greeting

Start the client as described in section 2. At `Choose an option:`, enter
`1`. At `Enter your greeting message:`, type a short, non-sensitive message,
for example:

```text
Hello. We can't answer right now. Please leave a message after the tone.
```

The client sends that text to Speech synthesis using the configured
`en-US-Serena:DragonHDLatestNeural` voice and writes the result to
`voice-mail\greeting.wav`. The service must support this voice. **This path is
fixed and an existing `greeting.wav` can be overwritten.** Check and preserve
any existing file before selecting option 1; skip this step if you cannot
safely protect it. The script does not record microphone audio.

After synthesis completes, the menu appears again. Enter `3` to return to
PowerShell.

## 4. Transcribe the sample messages

Start the client and enter `2` at `Choose an option:`. There is no additional
text prompt: the client finds each `.wav` file in
[`voice-mail\messages`](voice-mail/messages/), plays it, and then performs
one-shot speech recognition. A working audio output device is required for
playback; the code does not request microphone input.

Review the transcripts locally, then enter `3` at the next menu prompt to
exit. Transcripts contain message content, so only process recordings you
are authorized to use and do not share private output. Both synthesis and
recognition send requests to Azure Speech and may incur charges.

## How the client works

`voice-mail.py` loads the runtime `.env`, constructs `DefaultAzureCredential`,
and initializes the Speech SDK with `FOUNDRY_ENDPOINT`. Option 1 synthesizes
the typed text to the fixed `greeting.wav` path. Option 2 enumerates the
sample WAVs, plays each file with `playsound3`, and calls
`SpeechRecognizer.recognize_once_async()` once per file. Option 3 exits the
menu loop. The launcher changes into the runtime folder before starting the
script so that the sample-message path resolves correctly.

## Troubleshooting, privacy, and cleanup

- **Authentication or endpoint error:** Verify the endpoint format and
  resource access. Authenticate with `az login` if needed. The script catches
  exceptions and prints them, but does not set a failure exit code; a `0`
  process status by itself does not prove a Speech request succeeded.
- **Unsupported voice:** The synthesis voice name is hard-coded. Check that
  `en-US-Serena:DragonHDLatestNeural` is available for the selected resource
  and region.
- **Message files not found:** Launch from the repository root with
  `run-lab.ps1`; it sets the working directory to `voice-mail`.
- **No playback:** Option 2 requires local audio output before it starts
  recognition. Check the device volume and output selection, or skip
  transcription if playback is unavailable.
- **Existing greeting:** Option 1 writes to `greeting.wav` without asking
  before replacing it. Preserve the existing file or skip synthesis.
- **Private data:** Do not use personal voicemail or include identifying
  details in typed greetings unless authorized. Keep transcripts private.

The code does not create or delete Azure resources. It writes the synthesized
audio locally when option 1 is selected; it does not save transcripts to a
file. No generated audio or cloud configuration needs cleanup after the
menu-exit check.

## Validation and conclusion

| Evidence | What it establishes |
|---|---|
| Source inspection | Confirms the menu options, fixed greeting output path, configured voice, supplied WAV inputs, and one-shot recognition flow. |
| Local preflight | Python 3.13.17 and all required imports were available; an endpoint value was configured without printing it. |
| Menu-exit dry run | The launcher started the client, accepted option `3`, and returned exit code `0`; no synthesis or transcription was requested. |
| Live recognition, November 15, 2026 | One supplied WAV was recognized through the Speech SDK using the documented launcher; the client printed a transcription and returned to the menu. The recognized name and phone-like sequence are redacted below. |
| Playback limitation | The client called `playsound3` before recognition and continued successfully. Audible output could not be independently confirmed in this noninteractive session. |
| Not tested | Speech synthesis and voice availability were not tested. No microphone was used. |

This lab demonstrates speech synthesis from typed text and recognition from
audio files. The menu-exit dry run checks local startup only; the later
one-sample recognition confirms that the configured resource accepted that
recognition request, but does not independently verify transcription accuracy
or speech synthesis.

## Captured output

The following output is from actual local checks. No dependencies were
installed and the `.env` endpoint value was not displayed. The existing
`greeting.wav` was present, so option 1 was not selected. A single recognition
request was sent to Azure Speech; no Azure resources were created or changed.

### 1. Local preflight

The local check verified package imports and whether the endpoint was
configured. The output is verbatim; it reveals only booleans, not the endpoint
or credentials:

```text
Python: 3.13.17
Imports: {'dotenv': True, 'playsound3': True, 'azure.identity': True, 'azure.cognitiveservices.speech': True}
FOUNDRY_ENDPOINT configured: True
Existing greeting.wav preserved: True
```

This did not obtain an Azure token or establish connectivity.

### 2. Menu-exit dry run

Command run from the repository root; `3` was sent to the client's standard
input. The launcher exited with code `0`, with no stderr. The initial
form-feed shown below represents the terminal-clearing `cls` control
character in the redirected capture:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail\ voice-mail.py
```

```text
[form-feed from cls]
Choose an option:
1: Record a greeting
2: Transcribe messages
3: Exit
```

The input itself was not echoed. No `Exiting...` line is printed for option
`3`: the `while` condition ends the loop before the corresponding inner
branch can run. The client returned normally, but this test exercised no
Azure operation. An initial harness attempt targeted a nonexistent
`powershell.exe` path before starting the client; rerunning with the active
PowerShell executable completed the dry run successfully.

### 3. Live recognition of one supplied sample

The client processes every `.wav` file in its working directory's `messages`
folder. To limit this run to one sample without moving or changing the
original recordings, a temporary folder in the repository contained a copy of
`message_1.wav`; the launcher ran the original script with that folder as its
working directory. The staging folder was removed after the run. From the
repository root, the launcher command was:

```powershell
.\run-lab.ps1 .\lab15-recognition-one-sample-20261115\ ..\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail\voice-mail.py
```

The inputs were `2` to start transcription, followed by `3` after it returned
to the menu. Option 2 played the sample through `playsound3` before making the
recognition request. The script does not use a microphone. The launcher
returned exit code `0` with no stderr, and the client printed a transcription.
In this noninteractive session, the playback call completed, but audible
output from a speaker could not be independently confirmed. The captured
transcript below redacts the recognized name and phone-like sequence; other
shown output is verbatim:

```text
[form-feed from cls]
Choose an option:
1: Record a greeting
2: Transcribe messages
3: Exit
Transcribing messages...

Transcribing message_1.wav...
Transcription: Hi, this is [name redacted]. Just calling to remind you about your appointment tomorrow. Call me back [phone-like sequence redacted] if you have any questions.
Choose an option:
1: Record a greeting
2: Transcribe messages
3: Exit
```

The original `message_1.wav` and the existing `greeting.wav` remained in
place. No greeting was synthesized and no other WAV was submitted.
