# 03 - Develop language solutions with Azure AI

[All labs and shared setup](../README.md)

| Lab folder | Runtime folder or detailed guide |
|---|---|
| [12-analyze-text](12-analyze-text/) | [Text analysis](12-analyze-text/text-analysis/) |
| [13-text-analysis-agent](13-text-analysis-agent/) | [Existing-agent client](13-text-analysis-agent/text-analysis-agent/) |
| [14-use-speech-capable-genai-models](14-use-speech-capable-genai-models/) | [Generate](14-use-speech-capable-genai-models/generate-speech/) / [transcribe](14-use-speech-capable-genai-models/transcribe-speech/) |
| [15-recognize-and-synth-speech](15-recognize-and-synth-speech/) | [Voicemail client](15-recognize-and-synth-speech/voice-mail/) |
| [16-use-azure-speech-in-agent](16-use-azure-speech-in-agent/) | [Incomplete speech-client starter](16-use-azure-speech-in-agent/speech-client/) |
| [17-develop-voice-live-agent](17-develop-voice-live-agent/) | [Voice Live client and validation record](17-develop-voice-live-agent/chat-client/) |
| [z-translation](z-translation/) | [Text and speech translators](z-translation/translators/) |

## Shared setup

Copy the chosen **runtime folder's** `.env.example` to a local `.env`, configure
its endpoint, and sign in with `az login`. The numbered folders above are
navigation containers; pass their runtime subfolder to the launcher.

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis\ text-analysis.py -Install
```

Resource-root, project, and Azure OpenAI endpoints are different. Follow the
selected guide, especially when diagnosing API-version or authorization errors.

Speech playback and microphone scenarios require working local audio devices
and permissions. Previous API tests do not establish that physical audio
hardware works. Keep recordings and extracted personal data local; requests
can incur Azure charges.
