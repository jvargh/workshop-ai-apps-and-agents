# Generate speech

[Lab 14](../README.md) | [Language labs](../../README.md)

## Behavior

[generate-speech.py](generate-speech.py) sends the text `My voice is my passport!`
to a deployed speech-generation model with voice `alloy` and a serious-tone
instruction. It saves `speech.mp3` beside the script, then attempts playback
with `playsound3`.

## Configure

Copy [.env.example](.env.example) to `.env` and set:

- `MODEL_ENDPOINT`: compatible Azure OpenAI resource endpoint, such as
  `https://<resource>.openai.azure.com/`; not `/api/projects/<project>`.
- `MODEL_NAME`: the deployed speech-model **deployment name**.

Sign in with `az login`. The client uses `DefaultAzureCredential`, token scope
`https://cognitiveservices.azure.com/.default`, and API version
`2025-04-01-preview`.

## Run

From the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\14-use-speech-capable-genai-models\generate-speech\ generate-speech.py -Install
```

There is no prompt loop; edit the sample input in the script to synthesize
different authorized text. The generated MP3 is intentionally excluded from Git.

## Validation and costs

Earlier live validation produced a 38,400-byte MP3 using the configured
deployment. Playback was skipped in that test, so it did not validate speakers.
This documentation update did not repeat synthesis or playback. Speech/model
usage can incur charges.
