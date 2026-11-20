# Lab 13 - Develop a text analysis agent with the Azure Language MCP server

[Language labs](../README.md) | [Repository setup](../../README.md)

This lab's Python client sends one prompt to an existing Foundry agent and
prints the full response as JSON, followed by a plain-text analysis summary.
The agent, its Language MCP tool, and any required
tool connection or authorization must already be configured in the Foundry
project. The client does not create an agent, attach tools, or continue an
approval-required tool call.

## Table of contents

- [1. Prepare the existing Foundry agent](#1-prepare-the-existing-foundry-agent)
- [2. Configure the project endpoint and sign in](#2-configure-the-project-endpoint-and-sign-in)
- [3. Install dependencies](#3-install-dependencies)
- [4. Run the text-analysis prompt](#4-run-the-text-analysis-prompt)
- [How the client works](#how-the-client-works)
- [Troubleshooting, privacy, and cleanup](#troubleshooting-privacy-and-cleanup)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Live sample prompt](#1-live-sample-prompt)
  - [2. Startup-only dry run](#2-startup-only-dry-run)
  - [3. Historical live-tool result](#3-historical-live-tool-result)

## 1. Prepare the existing Foundry agent

In the Foundry project you intend to use:

1. Confirm that the agent named by `AGENT_NAME` already exists.
2. Confirm that it is configured with the Azure Language MCP tool and that its
   connection is authorized for your identity.
3. If the tool requires user approval, be prepared to review it in the
   configured Foundry experience. This Python client prints the response JSON
   but does not implement an approval-continuation flow.

The client uses the **project endpoint**, not a resource-root Language
endpoint. It sends a single user prompt to the existing agent; it does not
provision Azure resources or configure the agent.

## 2. Configure the project endpoint and sign in

Run these commands in **PowerShell from the repository root**. The first
command preserves an existing `.env`; it copies the template only when the
file is missing:

```powershell
if (-not (Test-Path .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\.env)) {
    Copy-Item .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\.env.example .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\.env
}
az login
```

Open the nested runtime's `.env` in an editor and set the following values.
Do not paste endpoint or credential values into this README or captured
terminal output.

| Variable | Required value |
|---|---|
| `FOUNDRY_ENDPOINT` | Full project URL, such as `https://<foundry-resource>.services.ai.azure.com/api/projects/<project>`. Replace both placeholders with your project details. |
| `AGENT_NAME` | Exact name of the existing agent in that project. |

Complete the interactive `az login` flow if your Azure CLI session is not
already signed in. Your identity must be able to invoke the agent and use its
configured Language tool.

## 3. Install dependencies

The runtime dependencies are listed in
[requirements.txt](text-analysis-agent/requirements.txt). If you intentionally
want to install or update them in the repository's shared `.labenv` and then
launch the client, run:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\ text-agent.py -Install
```

The launcher installs the requirements and then starts the client; it is not
an install-only command. When the client displays `User prompt:`, continue to
[step 4](#4-run-the-text-analysis-prompt). This command can modify the shared
Python environment, so omit `-Install` when the dependencies are already
available.

## 4. Run the text-analysis prompt

From the repository root, launch the client without `-Install`:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\ text-agent.py
```

At `User prompt:`, enter this synthetic example and press Enter:

```text
Analyze this synthetic review. Return its sentiment, key phrases, and named entities: "The Northwind Cafe delivered my order promptly, but the support representative did not resolve my billing issue."
```

Read `Analysis Summary` below the JSON for the requested results. Review the
full JSON for tool calls, errors, or approval requests. Judge the analysis
against the synthetic sentence; the summary alone does not prove that the
Language MCP tool ran.

The program accepts one prompt per launch and then exits. To try another
prompt, run the command again with a different synthetic sentence, for example:

```text
Extract the organizations and locations from this synthetic note: "Aster Labs will meet Contoso Research in Redmond on Thursday."
```

The summary below the JSON looks like this:

```text
Analysis Summary
================
Organizations:
  - Aster Labs
  - Contoso Research

Locations:
  - Redmond
```

Each prompt can invoke a model and hosted tool and may incur charges. Use only
non-sensitive sample text.

## How the client works

[text-agent.py](text-analysis-agent/text-agent.py) loads the two settings from
`.env`, creates an `AIProjectClient` with `DefaultAzureCredential`, obtains an
OpenAI-compatible client, and calls the Responses API with an `agent_reference`
containing `AGENT_NAME`. It asks the agent to use plain-text headings for only
the requested categories, then prints the full JSON followed by the agent's
answer with indented bullets under recognized headings. If the agent returns
no text, the client points to the response details.
It does not create or update an agent or continue an approval-required tool call.

## Troubleshooting, privacy, and cleanup

- If the endpoint or agent cannot be found, verify that both `.env` values
  refer to the same Foundry project and that the agent already exists there.
- If authentication or authorization fails, verify the signed-in identity and
  its project, agent-invocation, and tool-connection permissions. Do not copy
  credentials into the source tree or terminal captures.
- If the response contains an approval request, the client cannot resume that
  request. Review or approve it through the configured Foundry experience, then
  retry only if appropriate.
- The client does not save the prompt or response to a local output file.
  Nevertheless, avoid real customer data and redact private project or account
  details before sharing output.
- The client itself has no resource-provisioning or deletion code. An attached
  agent tool can still have side effects, so inspect its configuration before
  prompting if it can create or update resources. There is no lab cleanup
  command.

## Validation and conclusion

This repository walkthrough is complete when the existing agent returns a
response appropriate to the prompt and the response shows that any required
tool use completed rather than remaining approval-pending. The dry run
recorded below checks local startup only. The separate live sample prompt
also returned a completed response with completed MCP calls.

## Captured output

### 1. Live sample prompt

The documented launcher was run from the repository root without `-Install`.
The harness sent the prompt below to standard input and closed it after that
single line, allowing the one-shot client to finish without further input:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\ text-agent.py
```

```text
Analyze this synthetic review. Return its sentiment, key phrases, and named entities: "The Northwind Cafe delivered my order promptly, but the support representative did not resolve my billing issue."
```

Sanitized excerpt of the actual assistant message text from the response JSON
(surrounding response metadata is omitted):

```json
{
  "sentiment": {
    "overall": "mixed",
    "positive_aspect": "Order was delivered promptly",
    "negative_aspect": "Support representative did not resolve the billing issue"
  },
  "key_phrases": [
    "Northwind Cafe",
    "order",
    "delivered promptly",
    "support representative",
    "billing issue"
  ],
  "named_entities": [
    {
      "text": "Northwind Cafe",
      "category": "Organization"
    }
  ]
}
```

The response JSON reported status `completed` and contained three completed
`mcp_call` items and one `mcp_list_tools` item. The launcher process exited
with code `0`; the one-shot client finished after returning the response.
This confirms a successful live inference and completed MCP calls for this
synthetic prompt only. No Azure resource was provisioned or deleted; the
invocation may incur model or tool charges.

### 2. Startup-only dry run

The following command was run from the repository root with standard input
redirected to `NUL`, so the client could reach its prompt without submitting a
user request:

```powershell
& $env:ComSpec /c 'powershell -NoProfile -ExecutionPolicy Bypass -File .\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\13-text-analysis-agent\text-analysis-agent\ text-agent.py < NUL'
```

Output excerpt (the script's initial console-clear control character is not
shown):

```text
User prompt: EOF when reading a line
```

The process exit code was `0`. The client caught the end-of-input exception
and printed it; this is **not** evidence of a successful Azure request or
response. The input ended before the code reached `responses.create`, so no
prompt was submitted and no model or tool call was made. This run verified the
launcher path and local startup through the prompt only.

### 3. Historical live-tool result

The existing nested [runtime guide](text-analysis-agent/README.md) records an
earlier Language-tool test that received HTTP `401 PermissionDenied`. That is
historical evidence from a prior run, not a result of this documentation
update; its original date and full command are not recorded here. It indicates
that the earlier test did not validate successful tool use. Recheck the
current project's connection and authorization before relying on the tool.
