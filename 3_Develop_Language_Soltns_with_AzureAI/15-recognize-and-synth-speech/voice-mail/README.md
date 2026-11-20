# Voicemail with Azure Speech

[Lab 15](../README.md) | [Language labs](../../README.md)

## Configure

Copy [.env.example](.env.example) to a local `.env`. Set `FOUNDRY_ENDPOINT`
to your Speech-capable resource endpoint and sign in with `az login`.
[voice-mail.py](voice-mail.py) passes `DefaultAzureCredential` to the Speech
SDK; the legacy `FOUNDRY_KEY` read in the script is not used for authentication.

The configured synthesis voice is `en-US-Serena:DragonHDLatestNeural`.
Its availability depends on the service/region; a configured endpoint alone
does not prove voice support.

## Run

From the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\15-recognize-and-synth-speech\voice-mail\ voice-mail.py -Install
```

| Menu option | Actual behavior |
|---|---|
| `1` | Prompts for text and synthesizes it to `greeting.wav`; no microphone recording. |
| `2` | Plays WAV files from [messages](messages/) and recognizes each once. |
| `3` | Exits. |

The launcher sets the working directory required by the relative `messages`
path. Local playback needs working audio support.

## Privacy and validation

The generated greeting is ignored by Git. Transcription output can reveal
message contents; use authorized sample recordings, not private voicemail.
This documentation update did not live-test recognition, voice availability,
or physical playback. Speech requests can incur usage charges.
