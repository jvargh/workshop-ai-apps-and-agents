# Lab 16 - Use Azure Speech in an agent

[Language labs](../README.md) | [Repository setup](../../README.md)

This folder is an **incomplete starter**, not a working speech-agent application.
The Python file has missing imports, client setup, and request/response handling;
its empty `else` block currently prevents it from running. The supplied audio
files are not read by the starter. No successful application run is claimed.
See the [speech-client starter notes](speech-client/README.md) for the code
status. For implemented voice scenarios, use the [Voice Live guide](../17-develop-voice-live-agent/)
or the [Azure Speech voicemail client](../15-recognize-and-synth-speech/).

## Table of contents

- [1. Inspect the starter](#1-inspect-the-starter)
- [2. Plan the missing implementation](#2-plan-the-missing-implementation)
- [3. Implement only after reviewing the plan](#3-implement-only-after-reviewing-the-plan)
- [4. Configure and run after the starter is complete](#4-configure-and-run-after-the-starter-is-complete)
- [Validation and limitations](#validation-and-limitations)
- [Captured output](#captured-output)

## 1. Inspect the starter

From the repository root, review the source, its local notes, and the declared
dependencies. These commands do not display the local `.env` file or audio data:

```powershell
Get-Content .\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\speech-client.py
Get-Content .\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\README.md
Get-Content .\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\requirements.txt
```

Ask your coding assistant to assess the scaffold before changing it:

> Review `speech-client/speech-client.py`, its README, and requirements. List
> the missing implementation pieces and the current syntax error, citing the
> relevant code. Do not edit files, read `.env`, inspect audio contents, or make
> Azure calls. Distinguish what the code currently does from what remains
> unimplemented.

## 2. Plan the missing implementation

The starter reads `FOUNDRY_ENDPOINT` and `AGENT_NAME` and contains a text-input
loop, but it does not initialize clients or send prompts. Before implementing
speech behavior, establish which supported Azure AI/Foundry APIs and agent
capabilities are actually available for this exercise.

Use this planning prompt:

> Using the checked-in starter and current official SDK documentation, propose
> a minimal design for connecting to an existing speech-capable agent. Identify
> the exact documented SDK calls, authentication requirements, and whether the
> proposed flow handles text, audio input, audio output, or some combination.
> Cite documentation for each API; if support cannot be verified, say so
> instead of guessing. Do not create or update Azure resources, access `.env`,
> or edit files.

Do not assume the presence of `speech_1.wav` or `speech_2.wav` means the
application consumes them, or that an existing agent has a particular speech
tool, model, or audio capability.

## 3. Implement only after reviewing the plan

The implementation work has **not** been completed in this lab. If you choose
to continue it, first review the proposed APIs and changes, then use a prompt
such as:

> Implement only the locally approved design in `speech-client.py`. Use the
> documented SDK APIs and this lab's existing-agent configuration; do not
> create, update, or delete Azure resources. Preserve existing files, never
> print credentials, handle errors clearly, and keep the interactive exit
> command working. Show the proposed diff before applying it, and do not claim
> it works until syntax checks and an explicitly approved runtime test pass.

The checked-in loop asks for text at `User prompt (or 'quit'):`, not microphone
input. Any audio capture or playback workflow must be separately designed and
documented rather than inferred from that prompt.

## 4. Configure and run after the starter is complete

After completing the implementation, create `speech-client\.env` from the
template only if it does not already exist. Set the values privately; do not
overwrite an existing configuration or print its contents:

```powershell
$runtime = '.\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client'
if (-not (Test-Path "$runtime\.env")) {
    Copy-Item "$runtime\.env.example" "$runtime\.env"
}
```

The template names `FOUNDRY_ENDPOINT` and `AGENT_NAME` must refer to the
intended project and agent. Verify their exact meaning against the completed
implementation. Never paste secret values into prompts or captured output.

The shared launcher accepts the lab directory followed by the script name.
After the implementation is reviewed and local prerequisites are approved, the
intended command from the repository root is:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\ speech-client.py
```

The current starter fails at Python parsing before any application behavior
can be tested. A launcher run without `-Install` returned the syntax error
shown under [Captured output](#captured-output). Once the implementation is
ready, install any missing dependencies from `speech-client\requirements.txt`;
the launcher's `-Install` option installs them and then starts the script.

After implementation and an approved run, a text-only smoke-test prompt could
be:

> Explain what speech capabilities this configured agent actually supports.
> If no audio input was supplied, say so; do not claim to have transcribed or
> generated audio.

Type `quit` only if the completed client reaches its input prompt. This is a
future test suggestion, not a result from the current starter.

## Validation and limitations

- The current source is syntactically invalid: Python reports an
  `IndentationError` for the empty `else` suite.
- No dependencies were installed, no Azure calls were made, and no microphone
  or audio playback was used.
- No cloud resources were created, updated, or deleted. No files were written
  by the dry run; this README is the only file changed for this task.
- There is no historical successful run in the inspected lab README/evidence.

## Captured output

This launcher run was from the repository root and did not install
dependencies. The absolute workspace prefix in Python's output is redacted as
`<repo-root>`; the excerpt otherwise preserves the reported error. The launcher
process exit code was 1.

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\ speech-client.py
```

```text
  File "<repo-root>\3_Develop_Language_Soltns_with_AzureAI\16-use-azure-speech-in-agent\speech-client\speech-client.py", line 35
    except Exception as ex:
IndentationError: expected an indented block after 'else' statement on line 30
PROCESS_EXIT_CODE=1
```
