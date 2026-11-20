# Transcribe speech

[Lab 14](../README.md) | [Language labs](../../README.md)

## Behavior

[transcribe-speech.py](transcribe-speech.py) plays [speech.wav](speech.wav), sends
the same file to the deployed transcription model, and prints a text transcript.

## Configure

Copy [.env.example](.env.example) to `.env`:

- `MODEL_ENDPOINT`: the Azure OpenAI resource endpoint, such as
  `https://<resource>.openai.azure.com/`.
- `MODEL_NAME`: the transcription deployment name.

Sign in with `az login`. The implementation uses `AzureOpenAI`, API version
`2025-04-01-preview`, and Entra token scope `https://ai.azure.com/.default`.

## Run

From the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\transcribe-speech\ transcribe-speech.py -Install
```

The script attempts playback before the API call; a local playback failure can
prevent transcription from starting. No headless/playback-disable option is
implemented in the script.

## API-version fix and validation

The reported `400: API version not supported` was not resolved merely by changing
the version string. The configured URL was a **Foundry project endpoint**, which
is incorrect for this `AzureOpenAI` client. Setting the resource endpoint and
the documented API version resolved the earlier live request: HTTP 200 and a
nonempty transcript were observed.

That test substituted playback; physical audio hardware was not validated.
No live request was repeated for this documentation update. Keep recordings
and transcripts containing personal data local; transcription is billable.
