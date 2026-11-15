# Lab-z10a - Explore policy search, Teams, and Microsoft 365 integration

[Agent labs](../README.md) | [Repository setup](../../README.md)

This lab combines a working document-search agent with educational Teams and Microsoft Graph walkthroughs. [m365_teams_lab.py](m365_teams_lab.py) runs locally in Python. Its live options let a Foundry agent request a Python function that queries your configured Azure AI Search index.

**This is not a deployed Teams or Microsoft 365 integration.** The application does not read calendars, send email, search live SharePoint, create a Teams bot, or provision a managed Foundry IQ knowledge base. The policies are fictional Contoso sample documents.

| Menu option | What runs |
|---|---|
| **1 - Document-grounded Knowledge Agent** | Three automatic policy questions with real Foundry and Azure AI Search calls. |
| **2 - Microsoft Teams Deployment Concepts** | A display-only explanation of Teams components and deployment steps. |
| **3 - Microsoft 365 / Graph API Integration** | Display-only API examples, authentication concepts, and permissions. |
| **4 - Interactive Policy Chat** | Live, multi-turn policy questions using the same Python Search function. |
| **5 - Architecture & Deployment Guide** | A display-only production architecture and checklist. |
| **0 - Exit** | Ends the local application. |

## 1. Configure access

Run commands in **PowerShell from the repository root**. You need Python, Azure CLI, an existing Foundry project/model deployment, and an existing Azure AI Search service connected to that project. Docker, azd, Teams Toolkit, and Graph consent are not required for the working local flow.

Keep a working `.env`; create one from [.env.example](.env.example) only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\.env.example .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\.env
}
az login
```

Edit the local configuration:

| Setting | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | Your existing project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. |
| `MODEL_DEPLOYMENT_NAME` | An actual chat-model deployment in that project, not a model-family name. |
| `SEARCH_INDEX_NAME` | The intended dedicated lab index. Do not point setup at an unrelated production index. |
| `SEARCH_ENDPOINT` / `SEARCH_PROJECT_CONNECTION_ID` | The intended existing Search connection, when explicit selection is needed. Leave unused values blank or remove them to allow discovery. |
| `AZURE_RESOURCE_GROUP` / `AZURE_SUBSCRIPTION_ID` / `AZURE_LOCATION` / `SEARCH_SERVICE_NAME` | Actual service settings if supplied; otherwise leave them unset for discovery. Do not leave `your-...` or `<...>` placeholders in optional settings. |

The main application creates its own temporary agent versions; an `AGENT_NAME` template value is not used to select an existing agent here.

Your identity needs agent-version creation/invocation/deletion permissions, access to discover the Search connection/resource, and Search query access. Setup additionally needs permission to manage the configured index and upload documents. Typical Search roles are **Search Service Contributor** plus **Search Index Data Contributor** for setup, and **Search Index Data Reader** for queries.

The scripts do not grant roles or retrieve/save admin keys. Normally `SEARCH_KEY` is unnecessary because the SDK uses your signed-in identity; protect any explicitly configured credentials and do not publish `.env`.

## 2. Install dependencies separately

After configuring access, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\ m365_teams_lab.py -Install
```

**The launcher installs packages and then starts the menu application.** Enter **`0`** at `Select an option (0-5):` to finish this setup step. Wait for the exit/cleanup messages and the PowerShell prompt.

Selecting only `0` makes no model request and creates no agent version. This installation command does not prepare the Search index. [requirements.txt](requirements.txt) defines the dependencies; the following commands omit `-Install`.

## 3. Prepare and validate the Search index

[setup_search.py](setup_search.py) reuses the project's connected Search service. It creates/updates only the configured lab index and uploads the four supplied documents. It does not create a new Search service, change the service tier/authentication, or delete unrelated documents.

Run the entire block:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\ setup_search.py
    if ($LASTEXITCODE -ne 0) { throw 'Search setup failed. Resolve the error before running the live agent options.' }
}
```

You do not type questions during setup. Watch connection discovery, service verification, index preparation, `[Upload 1/4]` through `[Upload 4/4]`, indexing readiness, and the three retrieval checks.

Expected output includes:

```text
Uploaded 4 documents: ...
PASS: remote work -> remote_work_policy.txt (verified '25 Mbps')
PASS: expense reports -> expense_report_guide.md (verified 'concur.contoso.com')
PASS: laptop security -> it_security_policy.txt (verified 'BitLocker')
Search setup and all three retrieval checks passed.
```

The uploaded files are:

- [Company handbook](sample_documents/company_handbook.md)
- [Remote work policy](sample_documents/remote_work_policy.txt)
- [Expense submission guide](sample_documents/expense_report_guide.md)
- [IT security policy](sample_documents/it_security_policy.txt)

Require **exit 0 and all three checks** before continuing. Setup checks each upload, waits for indexing, and saves only the verified Search configuration in the local `.env`, preserving unrelated settings.

Rerunning the same setup command updates the configured index and the same sample-document IDs. If multiple Search connections are discovered, select the intended one through the optional settings rather than creating another service to bypass the error.

## 4. Start the application

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration\ m365_teams_lab.py
    if ($LASTEXITCODE -ne 0) { throw 'One or more lab operations failed. Review the errors before treating this run as successful.' }
}
```

Restart after setup or configuration changes. The three startup messages show settings loading, client preparation, and menu readiness. Client initialization is not proof that Azure/model access works; that is checked when the live operations call their services.

At the menu, type the option number, not a PowerShell command. After each demonstration, press **Enter** at its return-to-menu prompt.

## 5. Follow the menu samples

### Option 1: automatic policy questions

Enter **`1`**. Do not type the questions yourself; the application asks these three:

| Automatic question | What to confirm |
|---|---|
| `What is our remote work policy?` | Requirements such as six months' employment and 25 Mbps internet, with `remote_work_policy.txt` cited. |
| `How do I submit expense reports?` | Submission through Concur and relevant receipt rules, with `expense_report_guide.md` cited. |
| `What are the company's security guidelines for laptops?` | BitLocker and other requirements, with `it_security_policy.txt` cited. |

Look for `[Tool]` announcing local execution of `search_company_documents`, `[Search]` showing the query/results, retrieved filenames, and the final `Response:` text. Check the facts in the answer, not just that a filename appeared in a log.

The agent version created for this demonstration is deleted afterward. Press **Enter** to return to the menu.

### Option 2: Teams deployment concepts

Enter **`2`** and read the Teams app, bot registration, Adaptive Cards, authentication, testing, and publication walkthrough. Press **Enter** when finished.

**Expected outcome:** the text completes and returns to the menu. It does not create a Teams app, register a bot, provision resources, or test a Teams conversation. Those require a separate implementation and approved deployment.

### Option 3: Graph integration concepts

Enter **`3`** and review the SharePoint, calendar, email, and profile examples, plus the authentication flow and permission scopes. Press **Enter** when finished.

**Expected outcome:** illustrative snippets are displayed. They are not working Graph tools attached to this agent. No Graph consent is needed to view them, and no calendar is read or email sent.

### Option 4: interactive policy chat

Enter **`4`**. At **`YOU:`**, enter these inputs one at a time, waiting for the answer before continuing:

| Step | Input or action | What to confirm |
|---|---|---|
| 1 | Press Enter without typing anything. | `No model request was sent.` |
| 2 | `What are the eligibility requirements for remote work?` | Eligibility details from `remote_work_policy.txt`, including the six-month requirement. |
| 3 | `What amount requires a receipt for an expense report?` | Receipts are required for expenses **over $25**, with `expense_report_guide.md` cited. |
| 4 | `Which system do I submit those reports in?` | The follow-up keeps the expense context and identifies `concur.contoso.com`, citing the expense guide. |
| 5 | `What security settings are required on company laptops?` | BitLocker and other laptop requirements from `it_security_policy.txt`. |
| 6 | `What is Contoso's pet insurance reimbursement policy?` | The agent states that the policy was not found in the indexed documents instead of inventing one. |
| 7 | `quit` | The chat's temporary conversation and agent version are deleted. |

These policies are fictional examples, not your organization's rules. The client supplies retrieved content to the model and instructs it to cite source filenames; those are not native Foundry citation annotations.

`quit`, `exit`, or `q` ends this inner chat, not the whole menu application. Press **Enter** to return to the menu. This agent cannot access a live calendar, send email, or search SharePoint beyond the configured index.

### Option 5: architecture and checklist

Enter **`5`** to view the proposed architecture, rollout phases, and security/monitoring/operations considerations. Press **Enter** to return.

**Expected outcome:** guidance is displayed. No deployment readiness check or provisioning takes place.

### Option 0: exit

At the main menu, enter **`0`**. The SDK clients and credential close. The Search service/index remain available; exiting does not delete them.

If a live demonstration failed earlier, the application returns a nonzero exit code rather than claiming a successful validation just because you reached the menu exit.

## Troubleshooting, privacy, and cleanup

- **Missing or invalid configuration:** Replace required placeholders and clear unused optional ones. Restart after editing `.env`; do not assume another lab's endpoint/deployment is appropriate.
- **No matching or multiple Search connections:** Configure the intended existing connection and ensure your identity can discover it. A connection alone does not grant query/index permissions.
- **Search setup/query failure:** Check resource scope and permissions. Require all upload and source/fact checks to pass; a generic model answer is not a substitute.
- **Missing policy:** Inspect the returned filenames and source content. The pet-insurance sample intentionally tests an unsupported question.
- **Failed demonstration:** The error is shown, cleanup is attempted, and the session records failure even if you then view another menu option. Fix the issue and restart before claiming a passing run.
- **Private information:** Protect prompts, retrieved content, model answers, and any validation records. Keep credentials out of Git.
- **Resource retention:** Only temporary agent versions/conversations created by the live demonstrations are cleaned up. The configured Search index/service are retained. Do not use broad deployment cleanup to reset this local flow.

## Optional helpers: separate deployment workflows

These scripts are not needed for the working local Search/chat path:

| File | Purpose and limit |
|---|---|
| [check_prerequisites.py](check_prerequisites.py) | Checks a broader deployment toolchain, including Docker/azd. It is not the gate for the local policy examples. |
| [deploy_helper.py](deploy_helper.py) | An optional azd wizard that can provision billable resources. It is not run by the menu application. |
| [validate_deployment.py](validate_deployment.py) | Expects a separate azd deployment; it does not validate a project configured only through `.env`. |
| [agent.yaml](agent.yaml) | Configuration for the separate deployment path, not the menu application's agent definition. |
| [cleanup_all.py](cleanup_all.py) | Destructive deployment cleanup. Do not run it against shared resources or simply to fix a local chat error. |

The helpers already display their actions and now identify their separate mode on startup. They are syntax-checked here, not certified as working deployments, diagnostics, or safe teardown. Previous diagnostic failures do not invalidate the independently tested local Search flow.

## Offline checks

Run from the repository root:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\z10a-m365-teams-integration -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Lab regression checks failed.' }
}
```

**31 tests passed**, covering Search discovery, upload/indexing checks, policy function calls, conversation context, answer/source display, failed responses, bounded tool rounds, cleanup, and display-only walkthroughs. These checks use mocked Azure clients; they do not establish live service access.

## Validation and conclusion

The documented setup and application commands completed against the configured project, model deployment, and Search index:

| Check | Observed result |
|---|---|
| Search setup | Reused the existing service, uploaded **four sample documents**, and passed all **three** expected source/fact checks. Unrelated `.env` settings were preserved. |
| Option 1 | All **three automatic questions** returned document-specific answers with the expected filenames and facts, including 25 Mbps, Concur, and BitLocker. |
| Option 4 | All **five chat questions** completed. The expense follow-up retained context, and the pet-insurance question explicitly reported that the policy was not found. |
| Options 2, 3, and 5 | Each display-only walkthrough completed and returned to the menu. No Teams deployment, Graph call, or infrastructure provisioning was performed. |
| Cleanup and exit | The live demonstrations deleted their created agent versions and chat conversation; the application closed its SDK clients and returned exit **0**. Search service/index were retained. |
| Offline checks | All **31 tests** passed. |
| Optional deployment helpers | Syntax checked only. Their deployment, diagnostic, validation, and destructive-cleanup workflows were not run. |

The private live record is saved in `results\m365-local-validation.json` and ignored by Git. Normal application runs do not automatically save this transcript. These checks validate the implemented local Search/agent flow, not a live Teams or Microsoft 365 integration.

**Conclusion:** The working part is a local Python client connecting a Foundry agent to real Azure AI Search queries over sample documents. Teams and Graph remain educational integration patterns, not deployed capabilities.

## How the Python flow works

### Setup and configuration

`SearchSetup` discovers a project Search connection, verifies the existing service, defines the lab's `id`, `title`, `content`, `category`, and `source_file` fields, and uploads the four sample files. Stable document IDs come from filenames, so repeated uploads update those samples rather than creating new IDs.

Setup waits for the uploaded documents to be searchable and checks both the expected source filename and a policy fact for each topic. Configuration is saved only after those checks pass; it does not retrieve or persist admin keys.

### Agent-requested Search function

`M365TeamsLab` prepares `AIProjectClient` for agent management and an OpenAI-compatible client for responses. `knowledge_agent_definition` exposes one `FunctionTool`, `search_company_documents`, with a required nonempty query.

The model returns a function name, JSON arguments, and a call ID. Python accepts only the expected function and query shape, executes a keyword `SearchClient` query, and returns document titles, full content, and source filenames as JSON. The result is sent back as `FunctionCallOutput` with the matching call ID.

Each tool round uses current results, not a stale accumulated list. Responses are tied to the created agent version and, for option 4, the same cloud conversation. The handler limits Search rounds to five and treats failed/incomplete responses, invalid arguments, empty final text, and tool errors as failures.

### Grounding and limits

The agent instructions require answers from retrieved data and exact source filenames, prefer specific policy documents over the general handbook, and require an explicit missing-information response when evidence is absent. These instructions help guide answers but do not guarantee correctness; the sample checks verify concrete facts.

This implementation uses a locally executed Search function, not a managed Foundry IQ knowledge base or server-side `azure_ai_search` tool. It does not create embeddings or use a semantic ranker. The Python process must be running to execute its function, so this definition alone is not a functioning Teams bot.

### Menus, errors, and lifecycle

Options 1 and 4 execute live calls. Options 2, 3, and 5 print concepts and illustrative snippets without executing Graph/deployment operations. The old production/IQ terminology in method names is not evidence of those capabilities being deployed.

Live errors are logged and mark the session as failed. The menu can still be viewed, but the final process status is nonzero after a failed demonstration. Temporary-version cleanup runs in `finally`; option 4 also deletes its own conversation. The entry point closes SDK clients and the credential while preserving the Search service/index and unrelated agent versions.
