# 07 - Translation

[Language labs](../README.md) | [Repository setup](../../README.md)

The [translators runtime guide](translators/) covers configuration, installation,
text-translation results, and the distinction between text and speech services.

Run from the repository root with an explicit script name:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\z-translation\translators\ translate-text.py -Install
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\z-translation\translators\ translate-speech.py -Install
```

- **Text:** choose a supported target-language code, enter text, and type `quit`
  to exit. The console reports language lookup, target selection, and translation
  progress. Earlier live text tests are recorded in the runtime guide.
- **Speech:** recognizes one English utterance from the default microphone,
  translates it to French, Spanish, and Hindi, and synthesizes the translations
  through the default speaker. The console shows when to speak, what was
  recognized, and which translation is playing.

The shared `FOUNDRY_ENDPOINT` must support the service used by the selected
script. Microphone/speaker permissions and device availability are additional
prerequisites for speech; prior text tests do not validate that hardware.
