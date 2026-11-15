# Lab-z10c - Run a Microsoft Foundry workflow

[Agent labs](../README.md) | [Repository setup](../../README.md)

[workflow.py](workflow.py) runs locally in Python and invokes an existing, published **remote Foundry workflow** through the Responses API. Python sends `Start`, waits for the streamed response, formats returned ticket classifications and support drafts, and deletes its temporary conversation.

The workflow—not this script—owns the ticket list, routing, agent instructions, model deployments, and tools. The inspected sample processes three synthetic support tickets, drafts answers for technical/general questions, and returns an escalation sentence for billing. That sentence is conversation output, **not evidence that a human was contacted or a business record changed**. The client does not create, publish, or deploy the workflow.

## 1. Configure access and inspect the remote workflow

Use **PowerShell from the repository root**. You need Python, Azure CLI, an existing Foundry project, and permission to invoke the workflow and create/delete conversations. Keep your existing `.env`; copy the template only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\.env.example .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\.env
}
az login
```

Edit this lab's `.env`, using your own values:

| Setting | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | Required full project URL: `https://<foundry-resource>.services.ai.azure.com/api/projects/<project>`. |
| `WORKFLOW_NAME` | Optional existing published workflow name: `<published-workflow-name>`. Omit this setting to retain the sample name already selected in `workflow.py`. |

No local model-deployment key is needed: the remote workflow's referenced agents select their own models and tools. Environment variables already set in PowerShell take precedence over `.env`. Azure authentication uses `DefaultAzureCredential`; `az login` is the usual local sign-in path.

**Before running either command below, review the published workflow and every referenced agent's tools in Foundry.** `Start` can execute the entire workflow immediately, including its preconfigured actions. The inspected definition uses synthetic tickets, classification/resolution agents with web-search tools, and conversation messages. Do not assume another workflow is equally safe; stop if it would send email/messages externally, update records, make payments, or perform other unapproved actions.

Model inference and any configured tool calls can incur charges. Use synthetic data, and do not send real customer issues or secrets.

## 2. Install Python dependencies separately

After configuration and the action review, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\ workflow.py -Install
```

**`-Install` installs [requirements.txt](requirements.txt) into the shared `.labenv` and then starts the selected program. It is not install-only.** This command immediately sends `Start`; there is no menu or confirmation prompt. Wait for conversation cleanup and the PowerShell prompt. Do not run installation while other labs are using or modifying that shared environment.

The dependencies include `azure-ai-projects==2.3.0` and `openai<3`. Subsequent runs omit `-Install`.

## 3. Run the initial sample

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\ workflow.py
```

There is **nothing to type into Python**. The exact initial input is sent automatically to the remote workflow:

```text
Start
```

Follow `[1/6]` through `[6/6]`: load configuration, open clients, create a conversation, submit `Start`, retrieve/format the completed response, and delete the conversation. `[Workflow] Response accepted` confirms response creation, not completion of every remote node. The client waits for the completed response rather than printing each generated token.

For the inspected workflow, the remote ticket list contains these exact synthetic inputs; do not paste them into PowerShell or Python:

| Remote ticket | Expected route and visible result |
|---|---|
| `The API returns a 403 error when creating invoices, but our API key hasn't changed.` | **Technical** classification and a troubleshooting draft. |
| `Is there a way to export all invoices as a CSV?` | **General** classification and a CSV-export guidance draft. |
| `I was charged twice for the same invoice last Friday and my customer is also seeing two receipts. Can someone fix this?` | **Billing** classification and `Escalate billing issue to human support team.` |

The verified run printed `Ticket 1: Technical (98% confidence)`, `Ticket 2: General (99% confidence)`, and `Ticket 3: Billing (100% confidence)`, followed by `Formatted ticket records: 3`, `Conversation deleted`, and `Workflow run finished; SDK clients and credential closed.` Generated wording, confidence, and paraphrased issues may vary. Draft product instructions are model output, not independently verified product documentation.

## 4. Follow-up sample: repeat a fresh run

There is no interactive follow-up prompt or conversation-resume feature. To check repeatability, enter the same command **at the PowerShell prompt after the first run finishes**:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\ workflow.py
```

This sends `Start` again in a **new conversation** and reprocesses the remote ticket list. It does not continue the deleted conversation. The repeated live run again returned three ticket records in Technical, General, Billing order and the same billing escalation sentence; its confidence values were 98%, 99%, and 100%. Both updated-client runs deleted their conversations and returned exit 0.

Changing the remote tickets, node routing, or tools is a separate workflow-authoring task. This client has no free-text ticket-entry prompt.

## 5. Errors, privacy, and cleanup

After a launcher command returns, check its exit status in PowerShell:

```powershell
$LASTEXITCODE
```

| Status | Meaning |
|---|---|
| `0` | A completed response with nonempty text was processed, conversation deletion succeeded, and clients closed. This alone does not establish answer accuracy or an external action. |
| `1` | Configuration, authentication, workflow invocation, response processing, or cleanup failed. Read `Workflow run failed:` and any cleanup error. |
| `130` | Python handled Ctrl+C; cleanup was attempted for any conversation already created. Forced process termination can bypass cleanup. |

Missing/placeholder endpoint or workflow settings fail before remote invocation. For authentication/403 errors, check the selected identity's project and tool permissions without granting new access automatically. For a missing workflow, confirm `WORKFLOW_NAME` and that the definition is published in the configured project. Failed/incomplete response events, a stream ending without completion, and empty completed output all fail rather than reporting success.

The response stream closes on exit, and `finally` attempts to delete **only this run's conversation**, including on response errors or Ctrl+C. Cleanup failure prints the conversation ID for authorized, targeted manual investigation and makes an otherwise successful run fail. If invocation and cleanup both fail, the original invocation error is retained and the cleanup error is also printed. The project/OpenAI clients and credential close through context managers.

The lab leaves the existing workflow, agents, model deployments, tools, and authentication cache unchanged. Conversation deletion is not a promise to purge service telemetry, response retention, web-search records, or any external side effects. Do not delete the workflow or run broad resource cleanup to finish this lab.

## Offline regression checks

These tests use synthetic fixtures and mocked SDK clients; they neither invoke Foundry nor search the web:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\z10c-build-workflow-ms-foundry\tests -p 'test_*.py' -v
```

All **21 tests passed** with exit 0. They cover ticket formatting (including nested/quoted braces and unexpected JSON), stream failures, empty/missing completion, conversation cleanup, cleanup-error preservation, client closure, and application exit statuses.

## Validation and conclusion

The live observations below are retained from earlier validation; the supplemental folder/label update did not rerun the remote workflow.

| Check | Observed result |
|---|---|
| Read-only safety inspection | Retrieved the workflow definition and both referenced agents' instructions/tool definitions before invocation. The inspected ticket list is synthetic; web-search tools are configured, but this validation does not establish that a search was called. |
| Normal launcher and repeat run | Both updated-client runs completed through `run-lab.ps1` without `-Install`, formatted three records in Technical/General/Billing order, printed the billing escalation sentence, deleted their conversations, and exited 0. |
| Shared Python environment | Used Python 3.13 with `azure-ai-projects` 2.3.0, `azure-identity` 1.25.3, `openai` 2.54.0, and `python-dotenv` 1.2.3. No packages were installed, upgraded, or removed for this validation. |
| Offline checks | 21 tests passed, exit 0. |
| Invalid configuration | The actual launcher with a temporary blank endpoint failed before opening clients and returned exit 1; `.env` was not changed. |

The installation command is documented but was deliberately **not executed**, because the environment is shared. Live validation exercised the existing remote workflow, not deployment or workflow creation. Billing escalation was observed only as returned text; no human notification, customer-data integration, refund, or product guidance accuracy was verified. Fault/interrupt/cleanup-failure cases were checked offline, not induced against the service.

**Conclusion:** The local client successfully invoked the inspected remote workflow and formatted its three synthetic ticket results with cleanup. It saves no result files; progress and answers are console output. Review any different published definition before running it, and protect any console logs you choose to retain.

## How the client works

`main()` loads this lab's `.env` without overriding existing environment variables, validates the configuration, and opens `DefaultAzureCredential`, `AIProjectClient`, and its OpenAI-compatible client. `run_workflow()` creates a temporary conversation and calls `responses.create` with an `agent_reference`, `input="Start"`, and `stream=True`. It retrieves the final response after `response.completed`, checks its status/text, and formats the result.

`print_workflow_output()` uses JSON decoding rather than a brace-matching regular expression, so quoted braces inside ticket fields do not break parsing. Recognized records need string category/issue fields and finite numeric confidence in `[0, 1]`; intervening response text is preserved. Unrecognized or malformed output prints as raw text instead of crashing. `Formatted ticket records: 0` therefore means inspect the raw response, not that three tickets passed validation.

The remote workflow sets the ticket list, loops over it, classifies each issue, and branches on confidence/category. In the inspected definition, confidence above 0.6 routes billing to a conversation message and other categories to a resolution agent; the low-confidence branch requests more details in conversation output. The Python client does not implement these business rules, attach tools, or send external escalations.
