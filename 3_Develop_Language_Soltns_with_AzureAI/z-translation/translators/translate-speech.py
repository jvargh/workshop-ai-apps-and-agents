import os
from dotenv import load_dotenv


# Import namespaces
from azure.identity import DefaultAzureCredential
import azure.cognitiveservices.speech as speech_sdk



def main():
    try:

        # Clear the console 
        os.system('cls' if os.name == 'nt' else 'clear')

        # Get Configuration Settings
        print("Loading speech translation settings...", flush=True)
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')

        # Configure translation
        credential = DefaultAzureCredential()
        translation_cfg = speech_sdk.translation.SpeechTranslationConfig(
                token_credential=credential,
                endpoint=foundry_endpoint
        )
        translation_cfg.speech_recognition_language = 'en-US'
        translation_cfg.add_target_language('fr')
        translation_cfg.add_target_language('es')
        translation_cfg.add_target_language('hi')
        audio_in_cfg = speech_sdk.AudioConfig(use_default_microphone=True)
        translator = speech_sdk.translation.TranslationRecognizer(
            translation_config=translation_cfg,
            audio_config=audio_in_cfg
        )
        print(f"Source language: {translation_cfg.speech_recognition_language}")
        print("Target languages: French (fr), Spanish (es), Hindi (hi)")

        # Configure speech for synthesis of translations
        speech_cfg = speech_sdk.SpeechConfig(
            token_credential=credential, endpoint=foundry_endpoint)
        voices = {
            "fr": "fr-FR-HenriNeural",
            "es": "es-ES-ElviraNeural",
            "hi": "hi-IN-MadhurNeural"
        }
        
        # Translate user speech
        print("Listening on the default microphone. Speak now...", flush=True)
        translation_results = translator.recognize_once_async().get()
        if translation_results.text:
            print(f"Recognized speech: {translation_results.text}")
        
        # Print and speak the translation results
        translations = translation_results.translations
        if not translations:
            print(f"No speech translations returned ({translation_results.reason}).")
        for translation_language in translations:

            print(f"{translation_language}: '{translations[translation_language]}'")

            speech_cfg.speech_synthesis_voice_name = voices.get(translation_language)
            audio_out_cfg = speech_sdk.audio.AudioOutputConfig(use_default_speaker=True)
            speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_cfg, audio_out_cfg)
            print(f"Playing the {translation_language} translation...", flush=True)
            speak = speech_synthesizer.speak_text_async(translations[translation_language]).get()
            
            if speak.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
                print(f"Playback did not complete for {translation_language}: {speak.reason}")

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()
