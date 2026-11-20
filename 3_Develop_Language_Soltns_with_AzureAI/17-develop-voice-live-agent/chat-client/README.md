# Voice Live agent: changes, fixes, and validation

This records the fixes made on October 29-30, 2026, for this lab.

## 1. Missing Voice Live SDK

**Reported error**

```text
ModuleNotFoundError: No module named 'azure.ai.voicelive'
```

The SDK was not installed in the shared `.labenv` environment. The original
[requirements.txt](requirements.txt) listed only `dotenv`, `aiohttp`, and
`pyaudio`, omitting both Azure packages imported by the client.

Added:

```text
azure-identity
azure-ai-voicelive[aiohttp]>=1.3.1,<2
```

Installed the lab requirements into the existing shared environment. The
installed Voice Live SDK version was **1.3.1**. The `[aiohttp]` extra supplies
the asynchronous transport used by the client.

The first dependency edit allowed `>=1.3.0b1,<2`; it was tightened to
`>=1.3.1,<2` after verifying the installed stable SDK's connection interface.
The three original requirements were retained.

## 2. Misspelled install flag

The original command used `-Isntall` instead of `-Install`, so it did not
activate the launcher's dependency-installation switch.

Run from the workspace root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\ -Install
```

After installation, `-Install` is optional:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\17-develop-voice-live-agent\chat-client\
```

The launcher itself was not changed.

## 3. SDK-compatible agent connection arguments

Updated [chat-client.py](chat-client.py) for the installed SDK.

Previously, the code imported and constructed `AgentConfig` and passed it as
`agent_config=` to `connect()`. SDK 1.3.1 expects the Foundry agent name and
project name as direct arguments; the legacy keyword was accepted through
`**kwargs` but ignored.

Changes:

- Removed the `AgentConfig` import.
- Replaced the model object with a dictionary holding the existing settings.
- Passed `agent_name` and `project_name` directly to `connect()`.

Current configuration construction:

```python
agent_config = {"agent_name": agent_name, "project_name": project_name}
```

Current connection:

```python
async with connect(
    endpoint=self.endpoint,
    credential=self.credential,
    api_version="2026-01-01-preview",
    agent_name=self.agent_config["agent_name"],
    project_name=self.agent_config["project_name"]
) as connection:
```

The API version, Azure CLI authentication, session settings, and microphone/
speaker implementation were not changed.

## 4. Missing remote agent and chat model

**Reported error**

```text
Agent chat-agent not found.
```

Live checks confirmed that the configured Foundry project contained **zero
agents**. It had only the `gpt-4o-mini-tts` and
`gpt-4o-mini-transcribe` model deployments. Neither can serve as the reasoning
model for a prompt agent.

After explicit approval to create the agent and deploy a chat model:

| Setting | Value |
| --- | --- |
| Resource group | `<resource-group>` |
| Foundry resource | `<speech-resource>` |
| Region | `eastus2` |
| Project | `<speech-project>` |
| New model deployment | `gpt-4.1-mini` |
| Model version | `2025-04-14` |
| Deployment SKU | `GlobalStandard` |
| Deployment capacity | `10` |
| New prompt agent | `chat-agent` |
| Agent version | `1` |

Model availability and regional quota were checked before deployment.
Deployment returned `Succeeded`; the agent was then created and retrieved
again to verify persistence.

Agent instructions:

```text
You are a helpful voice assistant. Respond conversationally and concisely.
Use plain spoken language and avoid markdown unless requested.
```

These are persistent Azure resources, not just local code changes. Model and
Voice Live usage can incur Azure charges. No existing model deployments were
removed or replaced.

## 5. Configuration used

The existing [.env](.env) Voice Live settings already pointed to the intended
resource and project; they were inspected, not changed:

```dotenv
AZURE_VOICELIVE_ENDPOINT=https://<speech-resource>.cognitiveservices.azure.com/
AZURE_VOICELIVE_PROJECT_NAME=<speech-project>
AZURE_VOICELIVE_AGENT_ID=chat-agent
```

Despite the environment variable's `AGENT_ID` name, its value is passed as the
**agent name**, not a classic `asst_...` agent ID.

The project endpoint used for agent creation and lookup was:

```text
https://<speech-resource>.services.ai.azure.com/api/projects/<speech-project>
```

## 6. Tests and confirmed outcome

### Dependency and interface checks

- Imported the actual client and its class definitions with `.labenv` Python.
- Verified that the startup method supplies supported `agent_name` and
  `project_name` parameters.
- Did not treat successful imports as proof of a working remote agent.

### Live Azure checks

1. Reproduced `Agent chat-agent not found` over a real Voice Live connection.
2. Confirmed the configured project had no agents.
3. Deployed the chat model and verified the created agent persisted.
4. Ran the actual `VoiceAssistant.start()`, session configuration, event
   handlers, and cleanup against live Azure.
5. Injected a short text message after session acceptance and verified:
   - Session accepted `chat-agent`.
   - Response status was `completed`.
   - A nonempty transcript arrived.
   - **231,600 bytes of PCM audio** arrived as SDK-decoded bytes.
   - Audio cleanup was called.

Final successful response:

```text
Hello! This voice agent is working. How can I help you today?
```

Only the local audio-device implementation was substituted during the final
test. Authentication, the WebSocket connection, session settings, agent
invocation, transcript, and generated audio were live.

**Validation boundary:** microphone capture, speech recognition from a real
microphone, physical speaker playback, echo cancellation, and interruption
quality were not tested. No microphone or speaker device was opened.

### Test-harness corrections, not application changes

Intermediate test attempts needed corrections before the final test passed:

- Used UTF-8 output because redirected Windows console output could not encode
  the client's existing emoji.
- Used SDK `UserMessageItem` and `InputTextContentPart` objects for the
  injected test message.
- Compared completion status with `ResponseStatus.COMPLETED`, rather than the
  string representation of the enum.
- Counted audio bytes directly; SDK 1.3.1 already decodes audio deltas, so
  decoding them as base64 again was incorrect.

These issues were in the temporary tests, not fixes applied to the client.
Tests were executed inline; no reusable test script was added to this folder.

## 7. Scope summary

- Modified [requirements.txt](requirements.txt).
- Modified [chat-client.py](chat-client.py).
- Installed dependencies into the shared `.labenv`.
- Created the Azure chat-model deployment and prompt agent listed above.
- Added this documentation.
- Did not modify [.env](.env), the launcher, or the audio-processing code.
- Earlier transcription-lab endpoint/API-version fixes were separate and are
  not part of this Voice Live change set.
