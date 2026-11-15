# Lab 10 - Prepare expense drafts with Agent Framework

[Agent labs](../README.md) | [Repository setup](../../README.md)

[agent-framework.py](agent-framework.py) runs locally in Python, reads [data.txt](data.txt), and sends your request and that expense text to a remote model in your existing Foundry project. The Agent Framework agent and its function tool run in your Python process; this lab does not deploy an application or create a service-managed agent.

The `submit_claim` tool **only prints an email draft** and returns the same recipient, subject, and body to the model. Despite its name, it does not send email, submit a claim, make a payment, upload receipts, or save a file. Use synthetic expenses and a sample recipient; inference can incur charges.

## Table of contents

- [1. Check prerequisites and configure](#1-check-prerequisites-and-configure)
- [2. Install dependencies separately](#2-install-dependencies-separately)
- [3. Run a printed-draft request](#3-run-a-printed-draft-request)
- [4. Follow through with analysis only](#4-follow-through-with-analysis-only)
- [5. Errors, privacy, and cleanup](#5-errors-privacy-and-cleanup)
- [Offline regression checks](#offline-regression-checks)
- [Validation and conclusion](#validation-and-conclusion)
- [How the code works](#how-the-code-works)
- [Captured output](#captured-output)
  - [1. Prerequisite commands and authentication](#1-prerequisite-commands-and-authentication)
  - [2. Install command and blank setup prompt](#2-install-command-and-blank-setup-prompt)
  - [3. Normal command - printed-draft prompt](#3-normal-command---printed-draft-prompt)
  - [4. New normal command - analysis-only prompt](#4-new-normal-command---analysis-only-prompt)
  - [5. Cancellation and configuration-error commands](#5-cancellation-and-configuration-error-commands)
  - [6. Offline regression command](#6-offline-regression-command)
  - [7. Observed exits, timing, and side effects](#7-observed-exits-timing-and-side-effects)

## 1. Check prerequisites and configure

Run the commands in **PowerShell from the repository root**. You need Python 3.11 or later, Azure CLI, an existing Foundry project, and a deployed chat model that supports function calls. Your Azure identity must be allowed to invoke that deployment.

```powershell
Get-Command python, az
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env.example .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env
}
az login
```

Keep an existing working `.env` rather than overwriting it. Edit this lab's local configuration with your existing targets:

| Environment key | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | `https://<resource>.services.ai.azure.com/api/projects/<project>` |
| `MODEL_DEPLOYMENT_NAME` | `<existing-function-capable-model-deployment>`; use its deployment name, not merely its model family. |
| `EXPENSE_CLAIM_EMAIL` | `recipient@example.com` for the synthetic printed draft; this is not a delivery address used by an email service. |

The program explicitly loads the `.env` beside the script and uses `AzureCliCredential`. Existing process environment variables take precedence over `.env`, so check for stale overrides if the wrong configuration appears to be selected. All three keys are required before the client is created, and a tool-generated recipient must match `EXPENSE_CLAIM_EMAIL`. Do not change your Azure target or resources merely to make the lab pass.

Review `data.txt` before any model call. The supplied synthetic CSV contains taxi **24.00**, dinner **65.50**, and hotel **125.90**, totaling **215.40**. No currency is specified; the draft should not invent one.

## 2. Install dependencies separately

After configuring access, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py -Install
```

**The launcher installs dependencies and then starts the program.** When it displays the expense data and asks `What would you like me to do with it?`, press **Enter** or type **`exit`** and press Enter. Wait for `Stopped before model inference; no draft was produced.` and the PowerShell prompt. This finishes setup without creating a client or sending your data to the model; installation itself still downloads packages.

[requirements.txt](requirements.txt) declares `agent-framework-core==1.12.1` and the specific Foundry provider, `agent-framework-foundry==1.10.3`, matching the [Microsoft Foundry provider pattern](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/model-providers/microsoft-foundry). The required import is `agent_framework.foundry.FoundryChatClient`; the `agent-framework` meta-package and an unrelated Azure provider are not required. The launcher shares `.labenv` with other labs, so coordinate dependency installation instead of running multiple `-Install` commands concurrently.

## 3. Run a printed-draft request

Start the application without installing again:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py
```

Follow `[1/5]` through `[5/5]`: local file reading, request entry, configuration/client preparation, remote inference, and client/credential cleanup. At **`What would you like me to do with it?`**, enter this exact request as one line and press Enter:

```text
Create a printed expense-claim email draft from these expenses. Use the configured recipient and subject Expense Claim. Include every item and the exact total, do not invent a currency, and clearly state that nothing was sent or submitted.
```

Look for the actual tool trace, not just the model's final sentence:

```text
[tool: submit_claim] PRINTED DRAFT ONLY - no email or claim was sent.
To: recipient@example.com
Subject: Expense Claim
```

The printed body should itemize taxi **24.00**, dinner **65.50**, and hotel **125.90**, with total **215.40**. Wording may vary, but compare these amounts with `data.txt` and verify that the final `# Agent:` response describes a draft rather than a successful send or submission. A final claim that a draft was printed without the tool trace is not proof that the tool ran.

The process handles **one request**, closes its SDK clients and credential, and exits. Inspect the draft in the terminal. No draft file, receipt, email-delivery record, or claim report is created, so there is no generated file to open or delete.

## 4. Follow through with analysis only

Run the same normal command again; this is a new request, not a continuation of the previous conversation:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py
```

At the same input prompt, enter:

```text
Summarize these expenses by category and give the exact total. Do not call submit_claim, create a draft, or claim that anything was sent or submitted.
```

Expect a model summary of the three supplied categories and total **215.40**, with **no `[tool: submit_claim]` trace** and no draft or delivery claim. Check the summary against the local CSV instead of assuming model arithmetic is correct. To stop a later run without inference, use a blank request or `exit`; EOF also stops safely at the request prompt.

## 5. Errors, privacy, and cleanup

- **Missing configuration:** The program names the missing environment key and exits nonzero before creating the client. Complete the local configuration rather than using an unrelated deployment.
- **Import/dependency failure:** Verify the declared Foundry provider and compatible SDK versions. The current provider import succeeds with `azure-ai-projects==2.3.0`, `azure-identity==1.25.3`, and `openai==2.54.0`; the earlier `AutoCodeInterpreterToolParam` import problem was not reproduced. Do not blindly upgrade the shared environment.
- **Authentication, deployment, or capacity error:** Review the actual error, your Azure CLI sign-in, deployment availability, permissions, and quota. A model failure is not a successful draft; it propagates to a nonzero exit after cleanup.
- **Unexpected recipient or output:** The tool rejects recipients that differ from local configuration. Review the actual printed body and final model text; neither is evidence of reimbursement approval or email delivery.
- **Privacy:** The request, CSV contents, and configured draft recipient are sent to the remote model. Do not use personal/financial receipts, real recipient addresses, or private claim data in this exercise. Console output can expose the same data.
- **Storage and cleanup:** The model request uses `store=False`, and no service-managed agent or conversation resource is created by this code. This is not a guarantee about provider logging or retention policies. SDK clients and the credential close on normal execution and model errors; this does not sign you out of Azure CLI. There are no generated claim files or remote lab resources to delete. Keep `.env`, `.labenv`, and Python caches out of Git; do not delete pre-existing files or shared resources as cleanup.

## Offline regression checks

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\10-agent-framework -p test_claim_privacy.py -v
```

The focused tests mock the Foundry boundary while exercising configuration validation, draft-only instructions, response storage options, safe cancellation, exception propagation, empty responses, SDK cleanup, recipient enforcement, and the tool's actual printed/returned content. These tests do not prove Azure authentication or live model behavior.

## Validation and conclusion

The documented normal launcher and both exact sample prompts were exercised against the existing configured project and model using only the supplied synthetic expense data. The recipient was overridden to `recipient@example.com` in the validation process environment; `.env` and Azure targets were not changed.

| Check | Observed result |
|---|---|
| Provider/API check | `FoundryChatClient` imported successfully with the declared core/Foundry packages and the installed SDK versions listed above. |
| Draft request | The real local tool printed `Expense Claim`, the sample recipient, all three items, and total **215.40**. The model's final text matched those amounts and explicitly said nothing was sent or submitted. Cleanup completed; exit **0**. |
| Analysis-only follow-through | The model returned taxi **24.00**, dinner **65.50**, hotel **125.90**, and exact total **215.40** without calling `submit_claim`. Cleanup completed; exit **0**. |
| Startup cancellation | Blank input, `exit`, and EOF each stopped before inference through the actual launcher; exit **0**. |
| Configuration failure | An empty process-only endpoint override reported `Set PROJECT_ENDPOINT` before inference and returned exit **1**. The local `.env` remained unchanged. |
| Regression suite | All **9 tests passed**, exit **0**, covering the mocked boundary and real local tool behavior described above. |

No package install or upgrade was performed because the required provider was already present in the shared environment. No draft files, emails, claims, payments, uploaded receipts, or service-managed agents were created. This verifies the exercised synthetic prompts, not reimbursement correctness, real email delivery, or arbitrary model output.

**Conclusion:** This is a local Agent Framework tool-calling exercise backed by a remote Foundry model. Its useful result is a reviewed, printed draft or expense summary—not a sent email, submitted claim, payment, or saved report.

## How the code works

`main` reads the script-relative UTF-8 CSV and accepts one request, stopping on blank input, `exit`, or EOF. `process_expenses_data` validates the three local settings, creates `FoundryChatClient` and `Agent`, and invokes the model with `store=False`. `AsyncExitStack` closes the provider's owned OpenAI/project clients and the Azure CLI credential, since the installed provider itself has no close/context-manager API. The typed `submit_claim` tool enforces the configured recipient, prints the draft, and returns a `draft_only` result containing the same fields so the agent can describe the actual tool output. The entry point returns nonzero for execution failures or interruption rather than masking them as success.

## Captured output

These are actual executions from the repository root, captured on the local date
**2026-11-14 (UTC-05:00)**. The existing `.env`, Azure CLI login, project endpoint,
and model deployment were reused. Only the child process's `EXPENSE_CLAIM_EMAIL`
was overridden to the fictional `recipient@example.com`; the private configured
recipient was not used in the model request or printed draft.

The private capture harness waited for `What would you like me to do with it?`
before supplying each request and added that input to the transcript because
piped input is not echoed by the program. It captured stdout/stderr before
printing or saving redacted output. `<configured-recipient>` replaces the
fictional process-only recipient; `<repository-root>` and `<user-profile>`
replace identifying local paths. Configured endpoints, deployment names, and
identifiers were also subject to redaction but did not appear in these answers.
Line endings are normalized to LF and terminal-color escape sequences are
removed; Unicode punctuation and answer wording are otherwise preserved.
These historical model answers can vary on later runs.

Both live prompts were repeated once to obtain a correctly UTF-8-encoded capture;
the final complete transcripts are shown below. Across both passes there were
**four successful model requests and two local printed-draft tool invocations**.
There were no model errors, clarification requests, or timeouts. No email, claim,
payment, uploaded receipt, saved draft, or service-managed agent/conversation was
created. No playground or other manual UI action was required by these steps.

### 1. Prerequisite commands and authentication

```powershell
Get-Command python, az | Format-Table Name, CommandType, Source -AutoSize
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env.example .\2_Develop_AI_Agents_with_Azure\10-agent-framework\.env
} else {
    'Existing lab .env preserved.'
}
az account get-access-token --resource https://ai.azure.com --query expiresOn --output tsv
```

```text

Name       CommandType Source
----       ----------- ------
python.exe Application <user-profile>\AppData\Local\Microsoft\WindowsApps\python.exe
az.cmd     Application C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd

Existing lab .env preserved.
2026-11-14 23:37:52.000000
```

Exit **0**. The token check printed only its expiry, never its value. Authentication
was already valid, so the interactive `az login` command was not rerun.

Before allowing `-Install`, installed metadata and every required import were
checked in `.labenv`. Selected exact preflight output:

```text
Python: 3.13.17
python-dotenv: installed 1.2.3; PASS
azure-identity==1.25.3: installed 1.25.3; PASS
pydantic<3,>=2: installed 2.13.5; PASS
agent-framework-core==1.12.1: installed 1.12.1; PASS
agent-framework-foundry==1.10.3: installed 1.10.3; PASS
IMPORT PASS: dotenv load_dotenv
IMPORT PASS: agent_framework tool, Agent
IMPORT PASS: agent_framework.foundry FoundryChatClient
IMPORT PASS: azure.identity AzureCliCredential
IMPORT PASS: pydantic Field
azure-ai-projects==2.3.0
openai==2.54.0
pydantic==2.13.5
python-dotenv==1.2.3
Constraint/import preflight: PASS
Recursive installed dependency audit: 82 active constraints; 45 package/extra nodes; 0 conflicts
```

Both checks exited **0**. The applicable Foundry skill's dependency check also
exited **0** with both required azd extensions already present; nothing was
installed. This lab uses `agent-framework-foundry`, not the absent umbrella or
unrelated Azure provider distribution.

### 2. Install command and blank setup prompt

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py -Install
```

**Prompt/input:** Press Enter at `What would you like me to do with it?`.
The child process used `PIP_NO_INDEX=1` and
`PIP_DISABLE_PIP_VERSION_CHECK=1` after the complete constraint/import audit.
The documented pip command therefore checked the already-satisfied installed
packages without contacting a package index, downloading, upgrading, or
uninstalling anything.

<details>
<summary>Captured setup output, including the complete dependency check</summary>

```text
Requirement already satisfied: python-dotenv in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 1)) (1.2.3)
Requirement already satisfied: azure-identity==1.25.3 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: pydantic<3,>=2 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 3)) (2.13.5)
Requirement already satisfied: agent-framework-core==1.12.1 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 4)) (1.12.1)
Requirement already satisfied: agent-framework-foundry==1.10.3 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.10.3)
Requirement already satisfied: azure-core>=1.31.0 in .\.labenv\Lib\site-packages (from azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (1.41.0)
Requirement already satisfied: cryptography>=2.5 in .\.labenv\Lib\site-packages (from azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (50.0.1)
Requirement already satisfied: msal>=1.35.1 in .\.labenv\Lib\site-packages (from azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (1.39.0)
Requirement already satisfied: msal-extensions>=1.2.0 in .\.labenv\Lib\site-packages (from azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (1.3.1)
Requirement already satisfied: typing-extensions>=4.0.0 in .\.labenv\Lib\site-packages (from azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (4.16.0)
Requirement already satisfied: opentelemetry-api<2,>=1.39.0 in .\.labenv\Lib\site-packages (from agent-framework-core==1.12.1->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 4)) (1.45.0)
Requirement already satisfied: agent-framework-openai<2,>=1.10.0 in .\.labenv\Lib\site-packages (from agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.11.0)
Requirement already satisfied: aiohttp<4,>=3.9 in .\.labenv\Lib\site-packages (from agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (3.14.5)
Requirement already satisfied: azure-ai-inference<1.0.0b10,>=1.0.0b9 in .\.labenv\Lib\site-packages (from agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.0.0b9)
Requirement already satisfied: azure-ai-projects<2.4.0,>=2.2.0 in .\.labenv\Lib\site-packages (from agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (2.3.0)
Requirement already satisfied: annotated-types>=0.6.0 in .\.labenv\Lib\site-packages (from pydantic<3,>=2->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 3)) (0.8.0)
Requirement already satisfied: pydantic-core==2.46.5 in .\.labenv\Lib\site-packages (from pydantic<3,>=2->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 3)) (2.46.5)
Requirement already satisfied: typing-inspection>=0.4.2 in .\.labenv\Lib\site-packages (from pydantic<3,>=2->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 3)) (0.4.4)
Requirement already satisfied: openai<3,>=2.25.0 in .\.labenv\Lib\site-packages (from agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (2.54.0)
Requirement already satisfied: aiohappyeyeballs>=2.5.0 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (2.7.1)
Requirement already satisfied: aiosignal>=1.4.0 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.4.0)
Requirement already satisfied: attrs>=17.3.0 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (26.1.0)
Requirement already satisfied: frozenlist>=1.1.1 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.8.0)
Requirement already satisfied: multidict<8.0,>=4.5 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (7.1.0)
Requirement already satisfied: propcache>=0.2.0 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.5.4)
Requirement already satisfied: yarl<2.0,>=1.25.1 in .\.labenv\Lib\site-packages (from aiohttp<4,>=3.9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.25.1)
Requirement already satisfied: isodate>=0.6.1 in .\.labenv\Lib\site-packages (from azure-ai-inference<1.0.0b10,>=1.0.0b9->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.7.2)
Requirement already satisfied: azure-storage-blob>=12.15.0 in .\.labenv\Lib\site-packages (from azure-ai-projects<2.4.0,>=2.2.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (12.31.0)
Requirement already satisfied: anyio<5,>=3.5.0 in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (4.15.1)
Requirement already satisfied: distro<2,>=1.7.0 in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.9.0)
Requirement already satisfied: httpx<1,>=0.23.0 in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.28.1)
Requirement already satisfied: jiter<1,>=0.10.0 in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.17.0)
Requirement already satisfied: sniffio in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.3.1)
Requirement already satisfied: tqdm>4 in .\.labenv\Lib\site-packages (from openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (4.70.1)
Requirement already satisfied: idna>=2.8 in .\.labenv\Lib\site-packages (from anyio<5,>=3.5.0->openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (3.20)
Requirement already satisfied: certifi in .\.labenv\Lib\site-packages (from httpx<1,>=0.23.0->openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (2026.7.22)
Requirement already satisfied: httpcore==1.* in .\.labenv\Lib\site-packages (from httpx<1,>=0.23.0->openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (1.0.9)
Requirement already satisfied: h11>=0.16 in .\.labenv\Lib\site-packages (from httpcore==1.*->httpx<1,>=0.23.0->openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.16.0)
Requirement already satisfied: requests>=2.21.0 in .\.labenv\Lib\site-packages (from azure-core>=1.31.0->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (2.34.2)
Requirement already satisfied: cffi>=2.0.0 in .\.labenv\Lib\site-packages (from cryptography>=2.5->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (2.1.1)
Requirement already satisfied: pycparser in .\.labenv\Lib\site-packages (from cffi>=2.0.0->cryptography>=2.5->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (3.0)
Requirement already satisfied: PyJWT<3,>=1.0.0 in .\.labenv\Lib\site-packages (from PyJWT[crypto]<3,>=1.0.0->msal>=1.35.1->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (2.15.0)
Requirement already satisfied: charset_normalizer<4,>=2 in .\.labenv\Lib\site-packages (from requests>=2.21.0->azure-core>=1.31.0->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (3.5.1)
Requirement already satisfied: urllib3<3,>=1.26 in .\.labenv\Lib\site-packages (from requests>=2.21.0->azure-core>=1.31.0->azure-identity==1.25.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 2)) (2.8.0)
Requirement already satisfied: colorama in .\.labenv\Lib\site-packages (from tqdm>4->openai<3,>=2.25.0->agent-framework-openai<2,>=1.10.0->agent-framework-foundry==1.10.3->-r <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\requirements.txt (line 5)) (0.4.6)
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? 
Stopped before model inference; no draft was produced.
```

</details>

Exit **0**. This setup request stopped before configuration/client creation or
model inference; it produced no draft.

### 3. Normal command - printed-draft prompt

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py
```

**Prompt/input:**

```text
Create a printed expense-claim email draft from these expenses. Use the configured recipient and subject Expense Claim. Include every item and the exact total, do not invent a currency, and clearly state that nothing was sent or submitted.
```

**Captured output:**

```text
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? Create a printed expense-claim email draft from these expenses. Use the configured recipient and subject Expense Claim. Include every item and the exact total, do not invent a currency, and clearly state that nothing was sent or submitted.
[3/5] Checking local configuration and preparing the Foundry model client.
[4/5] Sending the request and expense text to the remote model; waiting for its reply.

[tool: submit_claim] PRINTED DRAFT ONLY - no email or claim was sent.
To: <configured-recipient>
Subject: Expense Claim
Printed expense-claim email draft (draft only; nothing was sent or submitted)

To: <configured-recipient>
Subject: Expense Claim

Hello,

Please find the expense claim details below:

- 07-Mar-2025 — taxi — 24.00
- 07-Mar-2025 — dinner — 65.50
- 07-Mar-2025 — hotel — 125.90

Total: 215.40

This is a printed draft only. Nothing has been sent or submitted. 


# Agent:
Printed expense-claim email draft created as draft-only. Nothing was sent or submitted.

To: <configured-recipient>  
Subject: Expense Claim

Hello,

Please find the expense claim details below:

- 07-Mar-2025 — taxi — 24.00
- 07-Mar-2025 — dinner — 65.50
- 07-Mar-2025 — hotel — 125.90

Total: 215.40

This is a printed draft only. Nothing has been sent or submitted.
[5/5] Closing the SDK clients and Azure CLI credential.
Finished. Review the printed tool output; nothing was sent, submitted, or saved.
```

Exit **0**. The real tool trace and the final answer both contain every supplied
amount and **215.40**; neither invents a currency or claims delivery/submission.

### 4. New normal command - analysis-only prompt

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py
```

**Prompt/input:**

```text
Summarize these expenses by category and give the exact total. Do not call submit_claim, create a draft, or claim that anything was sent or submitted.
```

**Captured output:**

```text
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? Summarize these expenses by category and give the exact total. Do not call submit_claim, create a draft, or claim that anything was sent or submitted.
[3/5] Checking local configuration and preparing the Foundry model client.
[4/5] Sending the request and expense text to the remote model; waiting for its reply.

# Agent:
Expense summary by category:

- taxi: 24.00
- dinner: 65.50
- hotel: 125.90

Exact total: 215.40
[5/5] Closing the SDK clients and Azure CLI credential.
Finished. Review the printed tool output; nothing was sent, submitted, or saved.
```

Exit **0**. There is a genuine final answer and **no `[tool: submit_claim]` trace**.
This was a fresh process/request, not a continuing conversation.

### 5. Cancellation and configuration-error commands

Each case started the same normal launcher:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\10-agent-framework\ agent-framework.py
```

**Prompt/input: `exit`**

```text
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? exit
Stopped before model inference; no draft was produced.
```

Exit **0**. Blank cancellation was already exercised by the setup run.

**Prompt/input: EOF** (child stdin closed without supplying a request)

```text
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? Stopped before model inference; no draft was produced.
```

Exit **0**. No model request or draft occurred.

**Prompt/input: the exact analysis-only prompt, with the child process's
`PROJECT_ENDPOINT` temporarily set to an empty string**

```text
[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.
The only tool prints a draft. No email, claim submission, payment, or file write occurs.
Here is the expenses data in data.txt:

date,description,amount
07-Mar-2025,taxi,24.00
07-Mar-2025,dinner,65.50
07-Mar-2025,hotel,125.90

[2/5] Enter one request below, or press Enter / type exit to stop before inference.
What would you like me to do with it? Summarize these expenses by category and give the exact total. Do not call submit_claim, create a draft, or claim that anything was sent or submitted.
[3/5] Checking local configuration and preparing the Foundry model client.

Lab failed (ValueError): Set PROJECT_ENDPOINT in this lab's local .env file.
```

Exit **1**, the expected genuine validation error. This request did not reach
inference. The override affected only that child; `.env` was never edited.

### 6. Offline regression command

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\10-agent-framework -p test_claim_privacy.py -v
```

```text
test_blank_exit_and_eof_stop_before_inference (test_claim_privacy.ClaimPrivacyTests.test_blank_exit_and_eof_stop_before_inference) ... ok
test_client_creation_failure_closes_credential (test_claim_privacy.ClaimPrivacyTests.test_client_creation_failure_closes_credential) ... ok
test_empty_response_is_failure (test_claim_privacy.ClaimPrivacyTests.test_empty_response_is_failure) ... ok
test_missing_project_or_model_fails_before_client_creation (test_claim_privacy.ClaimPrivacyTests.test_missing_project_or_model_fails_before_client_creation) ... ok
test_missing_recipient_fails_before_client_creation (test_claim_privacy.ClaimPrivacyTests.test_missing_recipient_fails_before_client_creation) ... [3/5] Checking local configuration and preparing the Foundry model client.
ok
test_model_failure_is_propagated_and_clients_close (test_claim_privacy.ClaimPrivacyTests.test_model_failure_is_propagated_and_clients_close) ... ok
test_recipient_comes_from_local_configuration (test_claim_privacy.ClaimPrivacyTests.test_recipient_comes_from_local_configuration) ... ok
test_tool_rejects_a_recipient_not_in_configuration (test_claim_privacy.ClaimPrivacyTests.test_tool_rejects_a_recipient_not_in_configuration) ... Function failed. Error: The draft recipient must match EXPENSE_CLAIM_EMAIL.
Executing <Task finished name='Task-37' coro=<ClaimPrivacyTests.test_tool_rejects_a_recipient_not_in_configuration() done, defined at <repository-root>\2_Develop_AI_Agents_with_Azure\10-agent-framework\test_claim_privacy.py:147> result=None created at <user-profile>\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py:101> took 0.223 seconds
ok
test_tool_returns_the_same_printed_draft_without_writing_files (test_claim_privacy.ClaimPrivacyTests.test_tool_returns_the_same_printed_draft_without_writing_files) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.350s

OK
```

Exit **0**, **9 tests passed**. The rejected-recipient error and asyncio timing
diagnostic above are real test output, not hidden failures or a live model error.
The tests mock the remote boundary; live behavior is evidenced separately above.

### 7. Observed exits, timing, and side effects

Durations are measured **whole subprocess wall time**, including launcher/startup,
not model latency. Each child was bounded to 180 seconds.

| Captured command/request | Exit | Wall time (seconds) |
|---|---:|---:|
| Prerequisite/token check | 0 | 3.66 |
| `-Install` and blank request | 0 | 9.80 |
| Printed draft, final UTF-8 capture | 0 | 15.81 |
| Analysis only, final UTF-8 capture | 0 | 16.00 |
| `exit` cancellation | 0 | 5.07 |
| EOF cancellation | 0 | 4.56 |
| Empty endpoint validation | 1 | 4.41 |
| Offline regression suite | 0 | 1.95 |

Inspection of [submit_claim](agent-framework.py) confirmed that its only effect is
printing, followed by returning the same `draft_only` fields to the model. The
live draft trace proves that local function ran; it is not evidence of a send,
approval, reimbursement, or remote claim submission. No draft/report file was
generated, so there is no generated-output link or cleanup deletion.

Before/after checks confirmed that installed distribution versions and this
lab's pre-existing `.env`, source, requirements, tests, and CSV were unchanged.
Only this README was persisted; the named private capture files were removed
after transcript/metric validation. No shared resource or sibling lab was changed.
