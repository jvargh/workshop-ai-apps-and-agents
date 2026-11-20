from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from azure.core.exceptions import AzureError

# import namespaces
from azure.identity import DefaultAzureCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem

def main():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Loading text translation settings...", flush=True)
        load_dotenv(Path(__file__).with_name(".env"))
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        if not foundry_endpoint or "{foundry-resource}" in foundry_endpoint:
            raise ValueError("Set FOUNDRY_ENDPOINT in this lab's .env to your Foundry resource endpoint.")

        # Create client using endpoint and credential
        with DefaultAzureCredential() as credential, TextTranslationClient(
            credential=credential, endpoint=foundry_endpoint
        ) as client:
            # Choose target language
            print("Fetching supported target languages...", flush=True)
            languagesResponse = client.get_supported_languages(scope="translation")
            if not languagesResponse.translation:
                raise ValueError("Translator returned no supported languages.")
            print("{} languages supported.".format(len(languagesResponse.translation)))
            print("(See https://learn.microsoft.com/azure/ai-services/translator/language-support#translation)")
            print("Enter a target language code for translation (for example, 'en'; 'quit' to exit):")

            targetLanguage = "xx"
            supportedLanguage = False
            while not supportedLanguage:
                targetLanguage = input().strip()
                if targetLanguage.lower() == "quit":
                    return
                matching_language = next(
                    (code for code in languagesResponse.translation if code.lower() == targetLanguage.lower()),
                    None
                )
                if matching_language:
                    targetLanguage = matching_language
                    supportedLanguage = True
                else:
                    print("{} is not a supported language.".format(targetLanguage))

            print(f"Target language: {targetLanguage}")

            # Translate text
            while True:
                inputText = input("Enter text to translate ('quit' to exit): ").strip()
                if inputText.lower() == "quit":
                    return
                if not inputText:
                    print("Enter nonempty text to translate.")
                    continue
                input_text_elements = [InputTextItem(text=inputText)]
                print(f"Detecting the source language and translating to {targetLanguage}...", flush=True)
                translationResponse = client.translate(
                    body=input_text_elements,
                    to_language=[targetLanguage]
                )
                if len(translationResponse) != 1 or not translationResponse[0].translations:
                    raise ValueError("Translator returned no translation for the input text.")
                translation = translationResponse[0]
                sourceLanguage = translation.detected_language
                if sourceLanguage is None:
                    raise ValueError("Translator returned no detected source language.")
                for translated_text in translation.translations:
                    if translated_text.to != targetLanguage or not translated_text.text:
                        raise ValueError("Translator returned an invalid target language or empty translation.")
                    print(
                        f"'{inputText}' was translated from {sourceLanguage.language} "
                        f"to {translated_text.to} as '{translated_text.text}'."
                    )
    except (AzureError, ValueError) as ex:
        print(f"Translation failed: {ex}", file=sys.stderr)
        raise SystemExit(1) from ex


if __name__ == "__main__":
    main()