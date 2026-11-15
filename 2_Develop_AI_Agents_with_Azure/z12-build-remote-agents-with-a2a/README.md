# Lab-z12 - Remote agents with A2A

[Agent labs](../README.md) | [Repository setup](../../README.md)

## Components

| Folder or script | Purpose |
|---|---|
| [title_agent](title_agent/) | Generates a title. |
| [outline_agent](outline_agent/) | Builds an outline using a title. |
| [routing_agent](routing_agent/) | Discovers agent cards and routes work to both remote agents. |
| [client.py](client.py) | Sends requests to the router. |
| [run_all.py](run_all.py) | Starts all three servers, checks their health, and runs the client. |

## Configure

Copy [.env.example](.env.example) to `.env` and configure:

- `PROJECT_ENDPOINT`: full Foundry project URL.
- `MODEL_DEPLOYMENT_NAME`: an available model deployment name.
- `SERVER_URL`: local bind hostname/IP, such as `127.0.0.1`, **without** `http://`.
- `ROUTING_AGENT_PORT`, `TITLE_AGENT_PORT`, `OUTLINE_AGENT_PORT`: three unused,
  distinct local ports.

Sign in with `az login`. Stop a previous copy before restarting so new
configuration is loaded; do not terminate unrelated processes.

## Run

From the repository root:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z12-build-remote-agents-with-a2a\ run_all.py -Install
```

Wait for the three health checks, then request a title and outline, for example
for an introductory React article. The router should invoke both remote
services. Keep the launcher running during the session; it manages its server
subprocesses on normal client completion.

## Compatibility, validation, and cleanup

The implementation uses versioned Foundry prompt agents and the Responses API,
with `azure-ai-projects>=2.3,<3`. It deliberately omits `temperature` and `top_p`
because the previously configured reasoning deployment rejected sampling
parameters supplied by the classic runs API.

Earlier live validation completed a React title/outline request and observed
A2A calls to both services. The isolated test servers were stopped afterward.
That is a historical result, not a new deployment check for this documentation
update.

Run local regression tests:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\z12-build-remote-agents-with-a2a -p "test_*.py" -v
```

Agent versions and router conversations can remain in the project after the
session. Review those resources separately; local server shutdown is not cloud
resource cleanup. Model calls incur usage charges.
