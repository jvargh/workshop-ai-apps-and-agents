# Lab-z10b - Connect a Foundry agent to Work IQ

[Agent labs](../README.md) | [Repository setup](../../README.md)

[workiq_lab.py](workiq_lab.py) runs locally in Python and starts the installed **Work IQ CLI as an MCP server over stdio**. A temporary Foundry agent requests `ask_work_iq`; Python calls that local server and returns its result to the agent.

Unlike Lab-z10a's sample-policy index, Work IQ can retrieve information from your authorized Microsoft 365 sources. Access depends on your account, entitlement, tenant consent, and source permissions. This lab does not create a Teams app, configure a separate Foundry IQ knowledge base, grant permissions, or change workplace data.

## 1. Check Work IQ and sign-in prerequisites

Run commands in **PowerShell from the repository root**. You need Python, Azure CLI, an existing Foundry project with a function-capable chat deployment, and the Work IQ CLI.

```powershell
Get-Command az, workiq
workiq --version
```

If Work IQ is missing, install it explicitly using Node.js/npm, then check again:

```powershell
npm install -g @microsoft/workiq
workiq --version
```

Do not install it again when it is already available. The Python client resolves the installed executable; it does not silently download another copy through `npx`.

Complete the Work IQ sign-in and tenant consent required for your intended Microsoft 365 data. Azure sign-in and workplace-data access are separate. If Work IQ reports that its terms need acceptance, review them and personally run:

```powershell
workiq accept-eula
```

**The lab does not accept legal terms or diagnostic consent for you.** Only `ask_work_iq` is exposed to the agent; legal/diagnostic tools such as `accept_eula` and `get_debug_link` are excluded.

## 2. Configure the Foundry project and model

Keep a working `.env`; create one from [.env.example](.env.example) only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\.env.example .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\.env
}
az login
```

Edit the local configuration:

| Setting | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | Your existing project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. |
| `MODEL_DEPLOYMENT_NAME` | An available chat-model deployment that supports function calls. Use its deployment name, not merely the model family. |

The program creates a temporary agent version; it does not use an `AGENT_NAME` template value to retrieve a portal-created agent. Your Azure identity needs permission to create, invoke, and delete agent versions.

Successful agent creation is not proof that inference works. Model availability/quota is checked by the actual query. Model and Work IQ calls can incur charges.

## 3. Install Python dependencies separately

After configuring access, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\ workiq_lab.py -Install
```

**The launcher installs packages and then starts the application.** Startup checks the Work IQ CLI, discovers its tools, and creates a temporary Foundry agent version. Enter **`0`** at the menu to finish setup and wait for cleanup and the PowerShell prompt.

Selecting only `0` sends no workplace question, but startup has already created an agent version. Normal exit deletes that version and closes the SDK clients. [requirements.txt](requirements.txt) defines the dependencies; subsequent run commands omit `-Install`.

## 4. Start the lab and inspect capabilities

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\ workiq_lab.py
    if ($LASTEXITCODE -ne 0) { throw 'Work IQ connection, query, or cleanup failed. Review the errors before claiming success.' }
}
```

Follow `[1/4]` through `[4/4]` for configuration, CLI validation, connection setup, and temporary-agent creation. The `[MCP]` messages show local server/session initialization and tool discovery.

Select **`6`** to view capabilities. This prints guidance; it does not query emails or meetings. Press **Enter** at the return-to-menu prompt and again at the continue prompt.

You do not start a separate server or terminal for Work IQ MCP. The client starts and closes local stdio sessions during discovery and tool calls.

## 5. Validate the connection without searching workplace content

Select **`5`**, then paste the following as **one line** at the custom-query prompt:

```text
Use ask_work_iq to ask exactly: "Without accessing or searching any workplace content, reply with exactly WORKIQ_OK." Your final response must be exactly WORKIQ_OK and nothing else. Do not read emails, meetings, chats, or documents.
```

Wait for the agent to finish. Look for:

```text
Calling Work IQ tool: ask_work_iq
[MCP] Executing the requested tool and waiting for its result...
Response:
WORKIQ_OK
```

The actual output includes separator lines and progress messages. The important checks are that **the tool actually runs** and the final answer contains the expected diagnostic marker. A marker produced without the tool-call trace is not a successful end-to-end integration test.

This diagnostic requests no workplace-content retrieval. It checks Foundry inference, local MCP execution, and response continuation—not access to all Microsoft 365 sources or the accuracy of workplace answers.

Press **Enter** to return to the menu. If a call reports an authentication/consent error, complete the required sign-in yourself before retrying. Do not approve extra access merely to make a diagnostic pass.

## 6. Optional: choose an authorized workplace scenario

These scenarios use real account data, not the synthetic diagnostic. Only run them when you are authorized to retrieve that information and to send the retrieved content to the configured Foundry model.

| Option | What to enter | What to review |
|---|---|---|
| **1 - Meeting Prep** | A specific meeting topic/time. Blank defaults to the next meeting. | Meeting details, related communications, preparation points, and supporting sources. Confirm that the result refers to the intended meeting. |
| **2 - Project Status** | A project name. Blank defaults to current projects. | Source-supported decisions, blockers, updates, and next steps. |
| **3 - Action Items** | A time range. Blank defaults to the past week. | Actual assigned actions, deadlines, and sources. This summarizes tasks; it does not create or complete them. |
| **4 - Workplace Research** | A topic. | Research through **Work IQ only**. No separate Foundry IQ/AI Search tool is attached. |
| **5 - Custom Query** | Your own question. Blank returns without a query. | A supported answer and relevant sources, or an explicit error/access limitation. |
| **6 - Capabilities** | No workplace query. | Informational descriptions, not proof that every source is accessible. |

For example, a meeting topic can be entered as your own meeting's exact title, and a time range as `this week`. These are input examples, not promises that the account has matching data.

Each scenario uses its own cloud conversation. Tool-result rounds within that query share context, but selecting another scenario is not a continuation of the previous query. Work IQ may return sources/timestamps; compare the answer with information you can independently access.

If results are missing, distinguish “no relevant data found” from an explicit access or authentication failure. Do not invent decisions or treat generic text as proof of retrieval.

## 7. Exit and check the outcome

Return to the menu and enter **`0`**. Look for agent-version deletion, SDK/credential cleanup, and the final session-completion message.

Each query's temporary **Foundry** conversation is deleted in `finally`. The session deletes only the agent version it created. EOF/interruption also attempts cleanup; forcibly killing the process can still leave remote state behind. This does not purge Work IQ/Copilot history or remove your CLI authentication cache.

A failed query or cleanup makes the run return a nonzero status, even if you subsequently select `0`. A clean menu exit does not turn an earlier failure into a passing validation.

## Troubleshooting and privacy

- **Work IQ not found:** Verify `workiq --version` in the same environment and check PATH. Install the CLI explicitly only if missing.
- **Project/model unavailable:** Check this lab's endpoint, deployment, agent permissions, and inference capacity. This is separate from Microsoft 365 entitlement.
- **Workplace authentication or consent error:** Read the actual error and refresh the required account/consent through the supported Work IQ flow. The lab never accepts terms or grants access automatically.
- **MCP schema mismatch:** Use the declared dependencies. The adapter reads protocol schema aliases with `model_dump(by_alias=True)` and preserves optional fields using `strict=False`.
- **Tool errors or empty results:** They are reported as failures, not forwarded as successful empty answers. Unknown or non-allowlisted tool names are rejected.
- **Research mode:** Setting up Foundry IQ in another lab does not attach it here. Option 4 remains a Work IQ-only query.
- **Sensitive content:** Queries and retrieved results may contain internal information. Protect logs and review data-handling requirements before using real workplace scenarios.

## Offline checks

Run from the repository root:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\z10b-work-iq-integration\tests -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Work IQ regression checks failed.' }
}
```

**18 tests passed**, covering tool schemas and restrictions, complete MCP results, failed/empty responses, versioned agent references, query cleanup, failed-run status, EOF cleanup, and the Work IQ-only research scope. These tests use mocks, not private Microsoft 365 content.

## Validation and conclusion

The installation/launcher check and privacy-safe diagnostic both completed using the configured project and model:

| Check | Observed result |
|---|---|
| Installation and startup | Dependencies were ready, the installed Work IQ CLI was discovered, and the temporary agent was created. |
| Capabilities and exit | Options 6 and 0 completed through the actual launcher with cleanup and exit 0. |
| Live tool round trip | Option 5 called the real `ask_work_iq` tool. The tool's JSON reply contained `response: WORKIQ_OK`, and the Foundry agent returned exactly **`WORKIQ_OK`**. |
| Diagnostic scope | The request explicitly excluded workplace-content searches. Returned diagnostic content was checked before forwarding it to Foundry; no legal/diagnostic consent tools were invoked. |
| Foundry cleanup | The diagnostic conversation and the created agent version were deleted, and SDK clients closed. |
| Offline checks | All **18 tests** passed. |

The test record is saved in `results\workiq-validation.json` and ignored by Git. Normal user queries do not automatically save that file.

Meeting, project, action-item, and research scenarios were not live-tested against private workplace data. The diagnostic verifies the communication path—not access to every Microsoft 365 source, answer accuracy, or a separate Foundry IQ integration.

**Conclusion:** The Python client bridges a Foundry agent to the locally running Work IQ CLI. The synthetic diagnostic checks that round trip without searching workplace content. Real meeting, project, and task answers require separate, authorized source-level review.

## How the client works

### Local MCP and Azure connection

`validate_workiq_setup` checks the resolved CLI executable. `StdioServerParameters` launches that installed command with `mcp`; `ClientSession` initializes the protocol and lists tools. The client closes each stdio session when its discovery/tool call ends.

`AIProjectClient` manages the temporary agent version, while its OpenAI-compatible client manages responses and conversations. Azure authentication and Work IQ's Microsoft 365 sign-in are separate.

### Tool allowlist and schemas

Only `ask_work_iq` is converted into a Foundry `FunctionTool`. Consent and diagnostic tools are not exposed. The schema is serialized using MCP protocol aliases, so optional parameters are preserved rather than replaced with an empty or all-required schema.

The model requests a function by name with JSON arguments. Python checks that name against the allowlist, calls Work IQ through MCP, and returns the complete text/structured result as JSON with the original function `call_id`.

Work IQ text content can itself be a JSON envelope with `response` and `conversationId`, rather than plain answer text. The client preserves that envelope for the model to interpret. That Work IQ conversation ID is not the temporary Foundry conversation ID.

### Response rounds and errors

Each query creates a new conversation containing the user prompt. Responses reference the created agent version, avoiding a different latest version during the session. Fresh function outputs are collected per round and sent back using the same conversation.

The loop is bounded to ten tool-response rounds. It checks response status, MCP error flags, result content, and final text. A failed query is logged and marks the session as failed; it is not converted into a success-shaped answer.

### Lifecycle

Query conversations are removed in `finally`. The menu's outer `finally` attempts deletion of only the created agent version and closes all SDK clients/credential, including on EOF or interruption. Cleanup failures are reported and make the run fail.
