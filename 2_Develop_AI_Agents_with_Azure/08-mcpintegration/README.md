# Lab 8 - Connect Foundry agents to MCP tools

[Agent labs](../README.md) | [Repository setup](../../README.md)

Model Context Protocol (MCP) lets applications discover and call tools exposed by a server. This lab demonstrates two paths: Foundry calls a public remote MCP server, or your Python client calls a local MCP server and returns its results to the agent.

| Script | What it does |
|---|---|
| [agent.py](agent.py) | Creates a prompt-agent version that retrieves public documentation from the Microsoft Learn MCP endpoint. |
| [client.py](client.py) | Starts the local inventory server, discovers its tools, and bridges Foundry function requests to MCP calls. |
| [server.py](server.py) | Exposes fixed sample inventory and last-week sales through two FastMCP tools. |

Neither example deploys infrastructure, changes inventory, places orders, or connects to a live commerce system. Agent/model calls may incur charges.

## Table of contents

- [1. Configure the project and model](#1-configure-the-project-and-model)
- [2. Install dependencies separately](#2-install-dependencies-separately)
- [3. Run the remote agent](#3-run-the-remote-agent)
- [4. Run the local inventory conversation](#4-run-the-local-inventory-conversation)
  - [Check the recommendations against the sample data](#check-the-recommendations-against-the-sample-data)
- [Troubleshooting, privacy, and cleanup](#troubleshooting-privacy-and-cleanup)
- [Offline checks](#offline-checks)
- [Validation and conclusion](#validation-and-conclusion)
- [How the examples work](#how-the-examples-work)
  - [Remote MCP: `agent.py`](#remote-mcp-agentpy)
  - [Local tools: `server.py`](#local-tools-serverpy)
  - [Local bridge: `client.py`](#local-bridge-clientpy)
  - [Ownership and lifecycle](#ownership-and-lifecycle)
- [Captured output](#captured-output)
  - [1. Configuration and authentication precheck](#1-configuration-and-authentication-precheck)
  - [2. Install command and its automatic hosted Learn request](#2-install-command-and-its-automatic-hosted-learn-request)
    - [Automatic prompt and approvals](#automatic-prompt-and-approvals)
  - [3. Remote Learn MCP repeat: command, request, and returned answer](#3-remote-learn-mcp-repeat-command-request-and-returned-answer)
    - [Fixed prompt, automatic approvals, and final response](#fixed-prompt-automatic-approvals-and-final-response)
  - [4. Local inventory MCP: command and all documented inputs](#4-local-inventory-mcp-command-and-all-documented-inputs)
    - [Input 1: press Enter without typing](#input-1-press-enter-without-typing)
    - [Input 2: show all current inventory levels](#input-2-show-all-current-inventory-levels)
    - [Input 3: restocking recommendation](#input-3-restocking-recommendation)
    - [Input 4: clearance recommendation](#input-4-clearance-recommendation)
    - [Input 5: best sellers this week](#input-5-best-sellers-this-week)
    - [Input 6: quit and cleanup](#input-6-quit-and-cleanup)
  - [5. Offline-check command and results](#5-offline-check-command-and-results)
  - [6. Capture verification and limits](#6-capture-verification-and-limits)

## 1. Configure the project and model

Run commands in **PowerShell from the repository root**. Keep a working `.env`; create one from [.env.example](.env.example) only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env.example .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env
}
az login
```

Edit this lab's `.env`:

| Setting | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | An existing project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. Use the project endpoint, not the model-only `/openai/v1/` URL. |
| `MODEL_DEPLOYMENT_NAME` | The actual name of a model deployment in the configured project that supports the MCP/function-tool scenarios. |

Your identity needs permission to create, invoke, and delete agent versions. Both clients create their own versions; you do not need to create the lab agents in the portal first.

## 2. Install dependencies separately

After configuring access, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ agent.py -Install
```

**The launcher installs packages and then runs the remote Microsoft Learn example automatically.** It sends a fixed public-documentation question, handles MCP approvals, prints the answer, deletes the agent version it created, and exits. You do not type prompts or `quit` for this script.

This setup command therefore includes billable model calls, not just package installation. The following normal run commands reuse the environment and omit `-Install`. [requirements.txt](requirements.txt) includes the Foundry, MCP, and FastMCP dependencies.

## 3. Run the remote agent

Installation already ran this example. Use the following command if you want to repeat it without reinstalling; another run makes additional model calls:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ agent.py
```

The script automatically sends:

```text
Give me the Azure CLI commands to create an Azure Container App with a managed identity.
```

Follow the four numbered setup messages, then look for:

| Output | What it tells you |
|---|---|
| `[MCP] Foundry discovered ... tools` | Foundry discovered tools from `https://learn.microsoft.com/api/mcp`. |
| `[Approval] Automatically approving ...` | The application approved a request from its configured `api-specs` server. This demonstration does not ask you to approve each request interactively. |
| `[MCP] Completed remote tool call: api-specs / ...` | A remote MCP tool actually ran. A plausible documentation answer without this evidence does not demonstrate tool execution. |
| `Agent response:` | The answer should provide Container App and managed-identity guidance. Review the commands; the script does not execute them. |
| `[Cleanup]` and `[Complete]` | The created agent version was deleted and the clients closed. |

The client requests approval for every remote operation but automatically grants requests only for the configured server label. A request from an unexpected label is an error. In a production application, approval should reflect the operation's risk and your access policy.

Keep this example focused on public documentation. Printed deployment commands are not evidence that resources were created, and executing them is outside this walkthrough.

## 4. Run the local inventory conversation

Launch:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ client.py
```

**Do not start `server.py` separately.** The client launches it using the same Python interpreter over standard input/output (stdio), initializes MCP, discovers `get_inventory_levels` and `get_weekly_sales`, and creates an inventory-agent version.

At `USER:`, enter these inputs **one at a time inside the running client, not in PowerShell**. Press Enter after each input and wait for `Agent response:` and the next input prompt.

| Step | Input or action | What to look for |
|---|---|---|
| 1 | Press Enter without typing anything. | `No model request was sent.` |
| 2 | `Show me the current inventory levels for all products.` | A table/list of the **10 sample products**. The tool trace should show `get_inventory_levels` being called through the local MCP server. |
| 3 | `Are there any products that should be restocked?` | **Moisturizer, Shampoo, and Skin Serum**, using the rule inventory < 10 **and** last-week sales > 15. |
| 4 | `Which products would you recommend for clearance?` | **Body Spray and Cleanser**, using the rule inventory > 20 **and** last-week sales < 5. |
| 5 | `What are the best sellers this week?` | The agent should explain that only **last week's sample sales** are available. That period's top sellers are Moisturizer (22), Skin Serum (19), and Shampoo (18). |
| 6 | `quit` | The agent version is deleted, the local MCP session/server closes, and control returns to PowerShell. |

`[Tool]` identifies the requested local tool; `[Tool result]` shows the data returned through MCP. Later answers may reuse data from the conversation rather than call the same tool again. Old function outputs must not be resent as new results.

### Check the recommendations against the sample data

| Product | Sample inventory | Last-week sample sales | Rule-based recommendation |
|---|---|---|---|
| Moisturizer | 6 | 22 | Restock |
| Shampoo | 8 | 18 | Restock |
| Body Spray | 28 | 3 | Clearance |
| Hair Gel | 5 | 2 | Neither |
| Lip Balm | 12 | 14 | Neither |
| Skin Serum | 9 | 19 | Restock |
| Cleanser | 30 | 4 | Clearance |
| Conditioner | 3 | 1 | Neither |
| Setting Powder | 17 | 13 | Neither |
| Dry Shampoo | 45 | 17 | Neither |

Both conditions must hold. Low stock alone does not qualify Hair Gel or Conditioner for restocking, and high stock alone does not qualify Dry Shampoo for clearance. Recommendations are generated explanations, not orders or updates to the sample dictionaries.

## Troubleshooting, privacy, and cleanup

- **Project/model not found:** Use the actual project endpoint and deployed model name. Installing packages does not create a project or deployment.
- **Remote tool discovery or approval fails:** Check model support, project permissions, access to the public Microsoft Learn MCP endpoint, and any account/network restrictions. Do not treat a failed tool call as successful documentation retrieval.
- **Local server cannot start:** Use the shared environment and documented client command. The client starts the server itself; no separate terminal or HTTP port is required.
- **MCP tool error or empty result:** The client raises an explicit error rather than forwarding a success-shaped result. Unknown tool names are rejected.
- **Repeated or incomplete answers:** The client processes additional function/approval rounds until it gets final text, and builds a fresh result list for each round. Check actual tool messages and returned data.
- **Logs and stdio:** Server diagnostics go to stderr. Stdout is reserved for MCP protocol messages; adding ordinary print output there can break communication.
- **Cleanup:** Both programs attempt to delete only the agent version they created, even when a request fails. The local client also closes its MCP session, transport, and child server. Existing agent versions are not deleted.
- **Cloud conversations:** Ordinary runs leave their conversations in Foundry. Review and remove only your own disposable test conversations as appropriate.
- **Privacy and cost:** Questions go to the configured Foundry service. Use public/sample data, protect logs, and remember that model calls can be billed even when no infrastructure or inventory changes occur.

## Offline checks

Run from the repository root after installing dependencies:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $python = Join-Path (Get-Location) '.labenv\Scripts\python.exe'
    Push-Location .\2_Develop_AI_Agents_with_Azure\08-mcpintegration
    try {
        & $python -m unittest test_mcp_lab -v
        if ($LASTEXITCODE -ne 0) { throw 'MCP lab checks failed.' }
    } finally {
        Pop-Location
    }
}
```

**Nine checks passed**, including real local stdio initialization and both inventory tools, chained function results, approval IDs, unknown-tool rejection, error handling, and agent-version cleanup with mocked Azure clients. These tests make no Azure model calls.

## Validation and conclusion

The recorded installation command and both launcher examples passed with the project and model deployment configured for that test:

| Check | Observed result |
|---|---|
| Remote Learn MCP | Foundry discovered three tools; approved `microsoft_docs_search` and `microsoft_docs_fetch` calls completed and returned Container App/managed-identity guidance. No generated deployment commands were executed. |
| Local inventory MCP | The Python client started the stdio server and called both `get_inventory_levels` and `get_weekly_sales`. All 10 sample inventory values were returned. |
| Restock recommendation | Moisturizer, Shampoo, and Skin Serum matched the sample rule. |
| Clearance recommendation | Body Spray and Cleanser matched the sample rule. |
| Current-week question | The agent stated that current-week data was unavailable and reported last-week sellers instead. |
| Cleanup | Both launchers exited successfully and deleted their created agent versions. The validation harness also deleted only its two test conversations; ordinary runs leave conversations in Foundry. |

The nine offline checks also passed. The private test record is saved under `results\mcp-live-validation.json` and ignored by Git; ordinary client runs do not automatically save transcripts. These results demonstrate the tested MCP paths and sample rules, not production inventory freshness or deployment-command correctness in your environment.

**Conclusion:** The remote example lets Foundry call a public MCP endpoint after application approvals. The local example keeps MCP execution in your Python process and returns its results to the Foundry agent. Neither path makes infrastructure changes or live inventory transactions.

## How the examples work

This consolidated explanation describes the current scripts, including the fixes for stale result lists and additional tool-call rounds.

### Remote MCP: `agent.py`

`AIProjectClient` creates the prompt-agent version; its OpenAI-compatible client manages conversations and responses. `DefaultAzureCredential` authenticates the calls. Context managers close these clients when execution ends.

`MCPTool` gives Foundry the remote server URL, the `api-specs` label, and `require_approval="always"`. The model can request tools from that server. When a response contains `mcp_approval_request`, the application checks its label/ID and creates a `McpApprovalResponse` with the matching `approval_request_id`.

Approvals are returned using `previous_response_id`, linking them to the response that requested permission. The loop checks every response, reports discovery and actual MCP calls, and continues if more approvals are requested. It prints final text only after a completed response supplies an answer; remote errors are not ignored.

### Local tools: `server.py`

`FastMCP(name="Inventory")` supplies the local protocol server. The `@mcp.tool()` decorators advertise the two functions and their descriptions/input schemas. Both functions take no arguments and return fixed dictionaries.

The server supplies facts only. It does not decide what to restock or clear, call Foundry, or modify stock. The agent applies the business rules to the tool results. The server starts only when run as a program, with its banner disabled and diagnostics directed to stderr.

### Local bridge: `client.py`

`StdioServerParameters` launches the adjacent server with `sys.executable`, avoiding a different Python interpreter or a working-directory-dependent server path. `stdio_client` starts the process, and `ClientSession.initialize()` negotiates the MCP session.

The client uses `list_tools` to discover the schemas and builds matching Foundry `FunctionTool` definitions. Foundry cannot call a local stdio process directly. Instead, the model returns a normal `function_call`, and the application routes its name and decoded JSON arguments to `session.call_tool`.

Successful MCP structured data is serialized as JSON; if only text is supplied, all nonempty text parts are combined. Error results, unexpected result types, or empty data/text are explicit failures. The client wraps each result as `FunctionCallOutput` with the model's original `call_id`, then sends the current round's results back on the same conversation.

The output list is rebuilt for every tool round. It is not shared across user turns, and the client does not assume a single round is enough. When no function calls remain, it requires a nonempty final answer. Blank prompts, `quit`, and EOF are handled without sending unnecessary model requests.

### Ownership and lifecycle

| Path | Who calls MCP? | Transport | Cleanup |
|---|---|---|---|
| Remote Learn | Foundry runtime, after the application returns approvals | Public HTTPS | The script deletes its created agent version and closes SDK clients. |
| Local inventory | Python client, through `ClientSession.call_tool` | Child-process stdio | The client deletes its created agent version and closes the MCP session/server through `AsyncExitStack`. |

Agent-version deletion runs in `finally` blocks, so it is attempted on errors as well as normal exits. This cleanup does not delete unrelated versions or the cloud conversation.

## Captured output

These are new, actual runs from the repository root on the local date
**November 14, 2026 (UTC-05:00)**. The setup command, remote repeat, local
conversation, authentication precheck, and nine offline checks all exited with
code `0`. Each of the three live runs deleted only its created agent version;
their three cloud conversations were left intact.

The capture supplied each local input only after `USER:` appeared and inserted
that input into the transcript because piped stdin is not echoed by the client.
Configuration values, agent/version/conversation identifiers, package-index URL,
absolute repository paths, and user-profile paths are replaced with labeled
placeholders. Line endings are normalized for comparison; Unicode answer wording and
numerical results are preserved. Public canonical URLs and fictional CLI sample
names remain visible. All CLI commands inside **agent answers are returned text
only**: no infrastructure, identity, role-assignment, or inventory changes were
executed. No portal/editor steps were run, and the existing `.env` was not edited.

Full redacted console records, including output omitted from the excerpts below:

| Command/case | Complete transcript |
|---|---|
| Configuration/authentication precheck | [Precheck output](captured-output/captured-2026-11-14-precheck.txt) |
| `agent.py -Install`, including its hosted answer | [Setup and hosted output](captured-output/captured-2026-11-14-install-hosted.txt) |
| `agent.py` remote repeat | [Hosted repeat output](captured-output/captured-2026-11-14-hosted.txt) |
| `client.py`, all six documented inputs | [Local inventory conversation](captured-output/captured-2026-11-14-local.txt) |
| README offline-check command | [Nine offline checks](captured-output/captured-2026-11-14-offline-checks.txt) |

### 1. Configuration and authentication precheck

The documented conditional copy was evaluated and preserved the existing file:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env.example .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\.env
}
```

Both required settings were present without placeholders, and all lab imports
succeeded. Azure login was already valid, so interactive `az login` was not
rerun. This read-only token-expiry check succeeded without printing the token:

```powershell
az account get-access-token --resource https://ai.azure.com --query expiresOn --output tsv
```

```text
2026-11-14 23:46:30.000000
```

### 2. Install command and its automatic hosted Learn request

Every direct requirement was satisfied before running `-Install`, `pip check`
reported no broken requirements, and a read-only `--dry-run --no-index` install
plan required no package changes. The actual launcher emitted 87
`Requirement already satisfied` lines and no installation, upgrade, or uninstall
actions. It reused the shared `.labenv` without changing installed packages.

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ agent.py -Install
```

Actual package-check excerpt:

```text
Looking in indexes: [REDACTED_PACKAGE_INDEX]
Requirement already satisfied: python-dotenv in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 1)) (1.2.3)
Requirement already satisfied: azure-identity in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: uvicorn in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 3)) (0.54.0)
Requirement already satisfied: azure-ai-projects==2.3.0 in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 4)) (2.3.0)
Requirement already satisfied: openai<3 in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 7)) (2.54.0)
Requirement already satisfied: mcp<3,>=2.2.0 in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 8)) (2.2.0)
Requirement already satisfied: fastmcp in .\.labenv\Lib\site-packages (from -r [REPOSITORY_ROOT]\2_Develop_AI_Agents_with_Azure\08-mcpintegration\requirements.txt (line 9)) (4.0.10)
```

#### Automatic prompt and approvals

There were no stdin prompts for this script. It automatically sent the fixed
question and approved requests from its configured Microsoft Learn server:

```text
Prompt: Give me the Azure CLI commands to create an Azure Container App with a managed identity.
[Request] Waiting for the agent's response or MCP approval requests...
[MCP] Foundry discovered 3 tools from api-specs.
[Approval] Automatically approving microsoft_docs_search on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_search
[Approval] Automatically approving microsoft_docs_search on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_search
[Approval] Automatically approving microsoft_docs_fetch on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_fetch
```

The [complete setup transcript](captured-output/captured-2026-11-14-install-hosted.txt)
contains its actual returned answer: system-assigned and user-assigned
Container App examples, identity inspection, and optional storage RBAC examples.
The generated names are fictional examples, not deployed resources.

```text
[Cleanup] Deleting only the created agent version: [REDACTED]...
[Cleanup] Created agent version deleted.
[Complete] Hosted MCP example finished. The cloud conversation is not deleted.
```

Exit code: `0`.

### 3. Remote Learn MCP repeat: command, request, and returned answer

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ agent.py
```

This separate run also discovered three tools. Its four approved calls completed:
three `microsoft_docs_search` calls and one `microsoft_docs_fetch` call. Both
hosted captures show actual tool-completion evidence, not just a plausible answer.
The scripts do not print raw remote MCP payloads or search/fetch arguments; those
were not separately captured. The tool names/status and final returned answer
below are the console evidence.

#### Fixed prompt, automatic approvals, and final response

````text
[1/4] Loading the Foundry project and deployment configuration...
Selected deployment: [REDACTED_MODEL_DEPLOYMENT_NAME]
This example retrieves public documentation and prints commands; it does not run them or deploy resources.
[2/4] Connecting to Foundry with Microsoft Entra authentication...
[3/4] Creating an agent version with remote MCP server https://learn.microsoft.com/api/mcp...
Requests from this configured server are automatically approved for this demonstration.
Created agent version: [REDACTED]
[4/4] Creating a conversation and sending the fixed sample prompt...
Conversation created: [REDACTED]
Prompt: Give me the Azure CLI commands to create an Azure Container App with a managed identity.
[Request] Waiting for the agent's response or MCP approval requests...
[MCP] Foundry discovered 3 tools from api-specs.
[Approval] Automatically approving microsoft_docs_search on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_search
[Approval] Automatically approving microsoft_docs_fetch on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_fetch
[Approval] Automatically approving microsoft_docs_search on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_search
[Approval] Automatically approving microsoft_docs_search on the configured Microsoft Learn server.
[Request] Returning 1 approval(s). Waiting for tool execution and the next response...
[MCP] Completed remote tool call: api-specs / microsoft_docs_search

Agent response:
Below are Azure CLI commands for both common options: **system-assigned managed identity** and **user-assigned managed identity**. Replace the placeholder values before running.

## 1) Prerequisites / setup

```bash
az login

az extension add --name containerapp --upgrade

az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

Set variables:

```bash
RESOURCE_GROUP="rg-aca-demo"
LOCATION="eastus"
ENVIRONMENT="aca-env-demo"
APP_NAME="aca-mi-demo"
IMAGE="mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
```

Create the resource group and Container Apps environment:

```bash
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION"

az containerapp env create \
  --name "$ENVIRONMENT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"
```

---

## Option A: Create the Container App with a system-assigned managed identity

```bash
az containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$IMAGE" \
  --ingress external \
  --target-port 80 \
  --system-assigned
```

Get the managed identity principal ID:

```bash
PRINCIPAL_ID=$(az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "identity.principalId" \
  --output tsv)

echo "$PRINCIPAL_ID"
```

---

## Option B: Create the Container App with a user-assigned managed identity

Set an identity name:

```bash
IDENTITY_NAME="uami-aca-demo"
```

Create the user-assigned managed identity:

```bash
az identity create \
  --name "$IDENTITY_NAME" \
  --resource-group "$RESOURCE_GROUP"
```

Get the identity resource ID:

```bash
IDENTITY_ID=$(az identity show \
  --name "$IDENTITY_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "id" \
  --output tsv)

echo "$IDENTITY_ID"
```

Create the Container App and attach the user-assigned identity:

```bash
az containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$IMAGE" \
  --ingress external \
  --target-port 80 \
  --user-assigned "$IDENTITY_ID"
```

---

## Verify the identity on the Container App

```bash
az containerapp identity show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP"
```

## Important note

Creating the managed identity only gives the app an identity. To let it access another Azure resource, such as Key Vault, Storage, or SQL, you must also grant that identity the appropriate Azure RBAC role or resource permission.
[Cleanup] Deleting only the created agent version: [REDACTED]...
[Cleanup] Created agent version deleted.
[Complete] Hosted MCP example finished. The cloud conversation is not deleted.
````

Exit code: `0`. None of the returned deployment commands were executed.

### 4. Local inventory MCP: command and all documented inputs

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\08-mcpintegration\ client.py
```

The original client started its own `server.py` child over stdio; no standalone
server, HTTP listener, or port was used. Actual discovery/setup excerpt:

```text
[Discovery] Listing the inventory server's available tools...
Connected to server with tools: ['get_inventory_levels', 'get_weekly_sales']
[Bridge] Exposing get_inventory_levels as a Foundry function tool.
[Bridge] Exposing get_weekly_sales as a Foundry function tool.
[Connect] Connecting to Foundry with Microsoft Entra authentication...
[Agent] Creating an inventory-agent version using the discovered tools...
Created agent version: [REDACTED]
Conversation created: [REDACTED]
Follow-ups reuse this conversation; old function outputs are not resubmitted.
```

#### Input 1: press Enter without typing

```text
USER: 
[Input] Please enter a prompt. No model request was sent.
Enter a prompt for the inventory agent. Use 'quit' to exit.
```

#### Input 2: show all current inventory levels

```text
USER: Show me the current inventory levels for all products.
[Conversation] Adding your question to the current conversation...
[Request] Asking the agent to answer or request an inventory tool...
[Tool] Agent requested get_inventory_levels; calling the local MCP server...
[Server tool] Returning sample inventory levels for 10 products.
[Tool result] {"Moisturizer": 6, "Shampoo": 8, "Body Spray": 28, "Hair Gel": 5, "Lip Balm": 12, "Skin Serum": 9, "Cleanser": 30, "Conditioner": 3, "Setting Powder": 17, "Dry Shampoo": 45}
[Request] Returning 1 current tool result(s) to the agent. Waiting for the next response...
Agent response: Current inventory levels:

| Product | Units in stock |
|---|---:|
| Moisturizer | 6 |
| Shampoo | 8 |
| Body Spray | 28 |
| Hair Gel | 5 |
| Lip Balm | 12 |
| Skin Serum | 9 |
| Cleanser | 30 |
| Conditioner | 3 |
| Setting Powder | 17 |
| Dry Shampoo | 45 |
Enter a prompt for the inventory agent. Use 'quit' to exit.
```

All 10 returned values match the fixed dictionary in this lab's `server.py`.
Despite the prompt's word "current", these are **simulated sample values**, not
live commerce inventory.

#### Input 3: restocking recommendation

```text
USER: Are there any products that should be restocked?
[Conversation] Adding your question to the current conversation...
[Request] Asking the agent to answer or request an inventory tool...
[Tool] Agent requested get_inventory_levels; calling the local MCP server...
[Server tool] Returning sample inventory levels for 10 products.
[Tool result] {"Moisturizer": 6, "Shampoo": 8, "Body Spray": 28, "Hair Gel": 5, "Lip Balm": 12, "Skin Serum": 9, "Cleanser": 30, "Conditioner": 3, "Setting Powder": 17, "Dry Shampoo": 45}
[Tool] Agent requested get_weekly_sales; calling the local MCP server...
[Server tool] Returning sample last-week sales for 10 products.
[Tool result] {"Moisturizer": 22, "Shampoo": 18, "Body Spray": 3, "Hair Gel": 2, "Lip Balm": 14, "Skin Serum": 19, "Cleanser": 4, "Conditioner": 1, "Setting Powder": 13, "Dry Shampoo": 17}
[Request] Returning 2 current tool result(s) to the agent. Waiting for the next response...
Agent response: Yes. Based on the restock rule — **inventory < 10** and **last week’s sales > 15** — these products should be restocked:

| Product | Inventory | Units sold last week | Recommendation |
|---|---:|---:|---|
| Moisturizer | 6 | 22 | Restock |
| Shampoo | 8 | 18 | Restock |
| Skin Serum | 9 | 19 | Restock |

Other low-inventory items like **Hair Gel** and **Conditioner** do not meet the sales threshold, so I would not recommend restocking them based on this rule.
Enter a prompt for the inventory agent. Use 'quit' to exit.
```

The sample rule selects Moisturizer, Shampoo, and Skin Serum. Hair Gel and
Conditioner correctly fail the sales condition.

#### Input 4: clearance recommendation

```text
USER: Which products would you recommend for clearance?
[Conversation] Adding your question to the current conversation...
[Request] Asking the agent to answer or request an inventory tool...
[Tool] Agent requested get_inventory_levels; calling the local MCP server...
[Server tool] Returning sample inventory levels for 10 products.
[Tool result] {"Moisturizer": 6, "Shampoo": 8, "Body Spray": 28, "Hair Gel": 5, "Lip Balm": 12, "Skin Serum": 9, "Cleanser": 30, "Conditioner": 3, "Setting Powder": 17, "Dry Shampoo": 45}
[Tool] Agent requested get_weekly_sales; calling the local MCP server...
[Server tool] Returning sample last-week sales for 10 products.
[Tool result] {"Moisturizer": 22, "Shampoo": 18, "Body Spray": 3, "Hair Gel": 2, "Lip Balm": 14, "Skin Serum": 19, "Cleanser": 4, "Conditioner": 1, "Setting Powder": 13, "Dry Shampoo": 17}
[Request] Returning 2 current tool result(s) to the agent. Waiting for the next response...
Agent response: Based on the clearance rule — **inventory > 20** and **last week’s sales < 5** — I recommend clearance for:

| Product | Inventory | Units sold last week | Recommendation |
|---|---:|---:|---|
| Body Spray | 28 | 3 | Clearance |
| Cleanser | 30 | 4 | Clearance |

**Dry Shampoo** has high inventory at 45 units, but it sold 17 units last week, so it does **not** meet the clearance criteria.
Enter a prompt for the inventory agent. Use 'quit' to exit.
```

The sample rule selects Body Spray and Cleanser; Dry Shampoo correctly fails the
low-sales condition.

#### Input 5: best sellers this week

```text
USER: What are the best sellers this week?
[Conversation] Adding your question to the current conversation...
[Request] Asking the agent to answer or request an inventory tool...
[Tool] Agent requested get_weekly_sales; calling the local MCP server...
[Server tool] Returning sample last-week sales for 10 products.
[Tool result] {"Moisturizer": 22, "Shampoo": 18, "Body Spray": 3, "Hair Gel": 2, "Lip Balm": 14, "Skin Serum": 19, "Cleanser": 4, "Conditioner": 1, "Setting Powder": 13, "Dry Shampoo": 17}
[Request] Returning 1 current tool result(s) to the agent. Waiting for the next response...
Agent response: I don’t have current-week sales data, so I can’t identify this week’s best sellers.

Using **last week’s sales**, the top sellers were:

| Rank | Product | Units sold last week |
|---:|---|---:|
| 1 | Moisturizer | 22 |
| 2 | Skin Serum | 19 |
| 3 | Shampoo | 18 |
| 4 | Dry Shampoo | 17 |
| 5 | Lip Balm | 14 |
Enter a prompt for the inventory agent. Use 'quit' to exit.
```

The response explicitly declined to claim current-week data. Its ranking matches
the owned sample last-week sales dictionary; no additional clarification was
requested by the agent.

#### Input 6: quit and cleanup

```text
USER: quit
Exiting chat.
[Cleanup] Deleting only the created agent version: [REDACTED]...
[Cleanup] Created inventory agent version deleted.
[Cleanup] Closing the MCP session, stdio transport, and local server process...
[Complete] Local MCP example finished. The cloud conversation is not deleted.
```

Exit code: `0`. No lab server remained running after the conversation and tests.
Across the four questions the local server actually returned three inventory
results and three last-week sales results; none were live source data.

### 5. Offline-check command and results

The exact PowerShell block in **Offline checks** was run from the repository
root without installing packages. All nine checks passed, including real local
stdio initialization and both sample tools. Azure clients were mocked for the
Azure-facing tests; these checks made no model calls.

```text
----------------------------------------------------------------------
Ran 9 tests in 3.026s

OK
```

Exit code: `0`. The [full test transcript](captured-output/captured-2026-11-14-offline-checks.txt)
also preserves an asyncio slow-task diagnostic and server INFO messages; neither
was a test failure.

### 6. Capture verification and limits

- Both hosted runs printed discovery, matching automatic approvals, completed
  remote calls, final answers, and successful created-version cleanup. No remote
  tool errors or failed requests were observed.
- Local MCP results were compared with the two literal dictionaries in
  `server.py`, including all 10 products, both two-condition recommendations, and
  the last-week ranking. The conversation remained sample-only and read-only.
- README console blocks were checked against the saved redacted transcripts;
  the complete transcript files were checked against the private capture after
  applying the declared redactions. Relative output links and Markdown fences
  were checked before the private capture files were removed.
- The original README content, existing `output.txt`, earlier
  `results\mcp-live-validation.json`, `.env`, runtime source, and shared setup
  files were preserved. Only this appended section and the five linked console
  output files were added.
- No login UI, configuration editing, resource provisioning, stock transactions,
  or execution of generated CLI guidance was performed. Raw hosted tool payloads
  are not available in the console records. Answers and timing can vary on
  future runs.
