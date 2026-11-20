# Language agent client

[Lab 13](../README.md) | [Language labs](../../README.md)

## What it does

[text-agent.py](text-agent.py) creates a Foundry project client, asks for one
user prompt, references an existing agent in a Responses API call, and prints
the entire response as formatted JSON, followed by `Analysis Summary` with
indented bullets under the recognized analysis headings.

It does not create/configure the agent, upload documents, or attach Language
tools. Those prerequisites must already be configured in Foundry.

## Configure

Copy [.env.example](.env.example) to `.env`, then set:

| Variable | Required value |
|---|---|
| `FOUNDRY_ENDPOINT` | Full project URL including `/api/projects/<project>`. This client does not use a resource-root Language endpoint. |
| `AGENT_NAME` | Existing agent name in that project. |

Sign in with `az login` and ensure both invocation and attached-tool permissions
are available. Replace the endpoint template with the full project URL.

## Run

From the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\ text-agent.py -Install
```

Enter a prompt appropriate to your configured tools, such as a request to
extract entities from synthetic text. Inspect the returned JSON for response
status, tool calls, errors, or approval requests, not only generated text.

## Current limits and validation

The checked-in client is single-turn and does **not** implement an MCP approval
continuation loop. An approval request in the JSON is not a completed tool call.
An earlier Language-tool test also encountered HTTP 401 `PermissionDenied`;
the backing connection/identity authorization must be resolved separately.

No fresh live tool validation was performed for this documentation update.
Model/tool calls can be billable, and full response JSON can contain input data
or account metadata; do not commit captured responses.
