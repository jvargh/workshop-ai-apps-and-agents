# Speech client starter - incomplete

[Lab 16](../README.md) | [Language labs](../../README.md)

## Current status

[speech-client.py](speech-client.py) reads configuration and contains a prompt
loop, but its imports, project/OpenAI clients, and response-handling code are
missing. Its empty `else` block currently also prevents Python from parsing
the file. It is not a runnable speech-agent implementation.

The folder includes [.env.example](.env.example) and
[requirements.txt](requirements.txt) as preparation material. Copying the
configuration or installing requirements does not complete the code.

## Work still required

1. Implement the SDK imports and authenticated project/OpenAI clients.
2. Resolve `FOUNDRY_ENDPOINT` to the appropriate project endpoint and
   `AGENT_NAME` to an existing speech-capable agent.
3. Implement requests, responses, tool approval handling where required, and
   explicit error/cleanup behavior.
4. Validate the selected model/tools against Azure and any audio path used.

No working launcher command or completed live test is claimed for this starter.
Use the [Voice Live guide](../../17-develop-voice-live-agent/chat-client/) for the implemented
realtime voice-client scenario instead.
