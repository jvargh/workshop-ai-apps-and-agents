# Lab 17 - Develop a Voice Live Agent

[Language labs](../README.md) | [Repository setup](../../README.md)

This lab runs a local Python client that connects Azure Voice Live to an
existing Foundry project and prompt agent. It captures speech from your
microphone, sends it to the service, and plays the agent's audio response.
The client does not create the project, agent, or model deployment.

## Table of contents

- [What you will build](#what-you-will-build)
- [1. Check prerequisites and configure the client](#1-check-prerequisites-and-configure-the-client)
- [2. Install dependencies if needed](#2-install-dependencies-if-needed)
- [3. Start the voice conversation](#3-start-the-voice-conversation)
- [How the client works](#how-the-client-works)
- [Troubleshooting, privacy, and costs](#troubleshooting-privacy-and-costs)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Local import dry run](#1-local-import-dry-run)
  - [2. Historical live-session evidence](#2-historical-live-session-evidence)

## What you will build

The client in [chat-client](chat-client/) uses the Azure Voice Live SDK and
Azure CLI credentials. It configures a text-and-audio session with PCM16 audio,
multilingual semantic voice activity detection, echo cancellation, and noise
reduction. A successful connection is not enough on its own: you also need an
existing Voice Live resource, Foundry project, prompt agent, and compatible
agent model deployment.

## 1. Check prerequisites and configure the client

Run these commands in **PowerShell from the repository root**. The first
command preserves an existing local `.env`; it copies the example only when
the file is absent:

```powershell
if (-not (Test-Path -LiteralPath .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\.env)) {
    Copy-Item -LiteralPath .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\.env.example -Destination .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\.env
}
```

Open `chat-client\.env` and set the values for your own resources:

| Variable | Value |
|---|---|
| `AZURE_VOICELIVE_ENDPOINT` | The endpoint for your Azure Voice Live resource. Use the resource endpoint, not the Foundry project URL. |
| `AZURE_VOICELIVE_PROJECT_NAME` | The name of the existing Foundry project. |
| `AZURE_VOICELIVE_AGENT_ID` | The existing prompt agent's **name**. Despite the variable name, the code passes this value as `agent_name`, not as an agent ID. |

The client uses `AzureCliCredential`. If you are not already signed in, run:

```powershell
az login
```

Do not paste endpoint values, tokens, or other credentials into a shared
transcript. Keep `.env` private.

## 2. Install dependencies if needed

The shared launcher installs this runtime's `requirements.txt` only when you
pass `-Install`. It uses the repository's shared `.labenv`; the command can
change that environment, so run it only when the dependencies are missing.
It then starts the voice client, so prepare your audio devices and
configuration before running it:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\ -Install
```

This README update did not install or change dependencies. The local import
check recorded below confirmed the current shared environment can import the
client and its required modules.

## 3. Start the voice conversation

Connect a working microphone and speakers/headphones, then launch the client
from the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\ chat-client.py
```

Wait for `Ready! Start speaking...` and speak naturally; **there is no
keyboard text prompt**. For example, try saying:

- “Hello. Please introduce yourself.”
- “What can you help me with today?”

These are suggested test utterances, not quoted results from the captured
session. The client prints recognized speech as `You:`, the agent's response
transcript as `Agent:`, and `Response complete` when its audio response ends.
Press **Ctrl+C** to stop. The client then closes the audio streams; it does
not delete the Foundry project, agent, or model deployment.

## How the client works

The `VoiceAssistant` connects to the configured existing agent and updates the
session. Once Voice Live reports the session is ready, `AudioProcessor` starts
microphone capture. Audio is sent in 24 kHz, mono, 16-bit PCM chunks; response
audio events are queued for speaker playback. Transcription and response
transcript events are printed to the console. The application opens actual
audio devices, so a module-import check does not validate microphone access,
speech recognition, or playback.

## Troubleshooting, privacy, and costs

- **Authentication fails:** Sign in with `az login` and confirm the signed-in
  identity can use the configured resource and project.
- **Connection or agent not found:** Check the Voice Live resource endpoint,
  exact project name, existing agent name, and access. This client does not
  provision a missing project, model, or agent.
- **No microphone or playback:** Check the operating system's device selection
  and microphone permissions. A live run requires usable local audio devices.
- **Keep audio private:** Microphone input is sent to Azure Voice Live, and
  recognized speech and responses may be processed by configured cloud
  resources. Do not speak sensitive information.
- **Costs:** A live Voice Live session and the configured model may incur
  Azure charges. Stop the client with Ctrl+C when finished.

## Validation and conclusion

| Evidence | What it establishes |
|---|---|
| Client source | Implements Voice Live connection, session settings, audio capture/playback, transcription display, and Ctrl+C cleanup. |
| Local import dry run, November 15, 2026 | The installed Python environment imported the client and defined both main classes without starting the app or contacting Azure. |
| Historical live-session test, October 29–30, 2026 | The separate validation record reports a completed response and returned PCM audio using substituted audio input/output. Physical microphone and speaker behavior was not tested. |
| This documentation update | No Azure calls, resource creation or updates, dependency installation, or audio-device access were performed. |

**Conclusion:** This lab connects local audio I/O to an already configured
Voice Live agent. The local dry run verifies imports only; use the live steps
with your own configured resources and audio devices to exercise the full
conversation.

## Captured output

The following local check was actually run from the repository root on
November 15, 2026. `runpy` loaded the client module under a non-main name, so
the guarded `main()` entry point was not called. This verifies importability,
not Azure connectivity or an end-to-end voice conversation.

### 1. Local import dry run

```powershell
& .\.labenv\Scripts\python.exe -B -c "import runpy; ns = runpy.run_path(r'3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\chat-client.py', run_name='lab17_import_check'); print('Imported lab client module without starting main()'); print('VoiceAssistant available:', 'VoiceAssistant' in ns); print('AudioProcessor available:', 'AudioProcessor' in ns)"
```

```text
Imported lab client module without starting main()
VoiceAssistant available: True
AudioProcessor available: True
```

The standard launcher was not run because it starts the microphone and speaker
interfaces and requires someone present to speak. No Azure command or live
session was run for this update.

### 2. Historical live-session evidence

The separate [chat-client validation record](chat-client/README.md) documents
a live test from October 29–30, 2026. It reports a completed Voice Live
response, a nonempty transcript, and 231,600 bytes of PCM audio received from
the SDK. Its recorded response excerpt was:

> Hello! This voice agent is working. How can I help you today?

That earlier test substituted audio input/output and did **not** validate a
physical microphone, real microphone transcription, speaker playback, echo
cancellation, or interruption quality. This excerpt is historical evidence;
it was not produced by the local import dry run above.
