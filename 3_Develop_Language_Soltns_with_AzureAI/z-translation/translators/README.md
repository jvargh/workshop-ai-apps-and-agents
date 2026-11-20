# Text translation lab

## Setup

[.env](.env) uses the existing Foundry resource endpoint:

```dotenv
FOUNDRY_ENDPOINT=https://<speech-resource>.cognitiveservices.azure.com/
```

The client uses `DefaultAzureCredential` with Microsoft Entra authentication.
API keys remain disabled; no new resource, model deployment, or permission
change was needed. Translator usage can incur Azure charges.

The requirements were installed into the workspace's shared `.labenv`.
The text translation SDK is pinned to `azure-ai-translation-text==1.0.1`.

## Run from the workspace root

Sign in with `az login` if needed, then run:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\07-translation\translators\ translate-text.py -Install
```

The script name is required because the folder contains two Python scripts.
After installing dependencies, `-Install` is optional.

For subsequent runs:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\07-translation\translators\ translate-text.py
```

Pass the **folder first** and the **script name as a separate argument**.
Keep the space before `translate-text.py`. Do not pass the full Python file
path as the first argument: the launcher expects a folder there and will report
`Lab folder not found` if given a file.

1. Choose a target language code, such as `es`, `fr`, or `de`.
2. Enter `Hello world!` or other text. The source language is detected automatically.
3. Enter more text for the same target language, or `quit` to exit.
4. Restart the script to choose another target language.

Unsupported language codes and empty input prompt for another entry. Service
and configuration errors are printed to standard error and exit with code 1.

## Alignment with the exercise guide

The code uses the guide's section markers, variable names, authentication,
language discovery, `InputTextItem`, and
`client.translate(body=input_text_elements, to_language=[targetLanguage])`.
The source language is detected automatically and the printed result follows
the guide's format.

Intentional safety differences from a literal copy:

- Imports `TextTranslationClient` explicitly instead of using a wildcard.
- Uses context managers to close the client and credential.
- Loads this folder's `.env` even when launched from another directory.
- Handles `quit` case-insensitively before making a translation request.
- Accepts language codes case-insensitively and rejects empty text.
- Reports configuration, service, and invalid-response errors explicitly.

You can also run `python translate-text.py` directly from this folder with
the shared environment activated, as shown in the guide.

## Live validation results

On October 30, 2026, the actual [translate-text.py](translate-text.py) script
authenticated to Azure, listed 138 supported languages, and translated
`Hello world!`:

| Target | Translation |
| --- | --- |
| Spanish (`es`) | ¡Hola mundo! |
| French (`fr`) | Bonjour le monde ! |
| German (`de`) | Hallo Welt! |

These were live Translator requests, not mocked translation responses.

## Portal equivalent

In the Foundry portal, open this resource/project, navigate to the AI services
playgrounds, and select **Azure Translator - Text translation**. Portal labels
can vary by portal version. Use `Hello world!`, select a target language, and
choose **Translate**.

The resource endpoint above is the endpoint described in the exercise
screenshot; it is not the Foundry project endpoint or an OpenAI deployment URL.
Portal UI interaction was not part of the automated validation.

## Scope

- Implemented the text translation template and configured this folder's endpoint.
- Installed the existing lab requirements without changing their versions.
- Left [translate-speech.py](translate-speech.py) as an exercise template.
- Did not change Voice Live configuration or code.
