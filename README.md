# Workshop: AI Apps and Agents with Microsoft Foundry

Hands-on Python labs for developing generative AI applications and AI agents
with Microsoft Foundry and Azure. The repository contains **two modules and
16 lab guides**, with per-lab configuration templates, dependencies, sample
data, and a shared PowerShell launcher.

Start with labs 01-05 for model-based applications, then labs 06-11 for agents.
Folders prefixed with `z` contain supplemental exercises. Each lab guide
describes its prerequisites, run commands, expected behavior, validation
history, and cleanup limitations.

## Workshop modules

### 1. Develop generative AI apps with Foundry

[Module overview](1-Develop_GenAI_Apps_with_Foundry/README.md)

| Lab | Focus |
|---|---|
| [01 - Plan and prepare](1-Develop_GenAI_Apps_with_Foundry/01-plan-and-prepare/README.md) | Inspect existing project/model deployments and verify live inference. |
| [02 - Model catalog and evaluation](1-Develop_GenAI_Apps_with_Foundry/02-model-catalog-evaluation/README.md) | Compare deployed models and run or resume cloud evaluation. |
| [03 - Foundry SDK app](1-Develop_GenAI_Apps_with_Foundry/03-foundry-sdk/README.md) | Use the OpenAI SDK for Chat Completions, Responses, history, streaming, and async calls. |
| [04 - Chat with tools](1-Develop_GenAI_Apps_with_Foundry/04-tools/README.md) | Combine brochure file search, web search, and conversation history. |
| [05 - Responsible AI](1-Develop_GenAI_Apps_with_Foundry/05-responsible-ai-content-filters/README.md) | Audit assigned content-filter policies and inspect an unapplied policy template. |
| [z05 - Optimize and fine-tune](1-Develop_GenAI_Apps_with_Foundry/z05-optimize-fine-tuning/README.md) | Validate an SFT dataset, test prompting, and optionally compare an already deployed fine-tuned model; training is not submitted automatically. |

### 2. Develop AI agents with Azure

[Module overview](2_Develop_AI_Agents_with_Azure/README.md)

| Lab | Focus |
|---|---|
| [06 - Build AI agents](2_Develop_AI_Agents_with_Azure/06-buildaiagents/README.md) | Test an existing IT-support agent in VS Code and Python, including generated-file downloads. |
| [07 - Custom tools](2_Develop_AI_Agents_with_Azure/07-customtools/README.md) | Handle local astronomy functions, sample cost calculations, and report creation. |
| [08 - MCP integration](2_Develop_AI_Agents_with_Azure/08-mcpintegration/README.md) | Connect agents to hosted Microsoft Learn MCP and a local sample-inventory MCP server. |
| [09 - Foundry IQ](2_Develop_AI_Agents_with_Azure/09-integrateFoundryIQ/README.md) | Query an existing knowledge-grounded agent and handle tool approvals. |
| [10 - Agent Framework](2_Develop_AI_Agents_with_Azure/10-agent-framework/README.md) | Run a local agent that prints an expense-claim draft; no email or claim is sent. |
| [11 - Agent orchestration](2_Develop_AI_Agents_with_Azure/11-agent-orchestration/README.md) | Coordinate summarizer, classifier, and action agents in a local sequential workflow. |
| [z10a - Microsoft 365 and Teams concepts](2_Develop_AI_Agents_with_Azure/z10a-m365-teams-integration/README.md) | Run sample-policy search with Azure AI Search; Teams and Graph sections are educational walkthroughs, not deployed integrations. |
| [z10b - Work IQ integration](2_Develop_AI_Agents_with_Azure/z10b-work-iq-integration/README.md) | Bridge a Foundry agent to the installed Work IQ CLI over local MCP stdio. |
| [z10c - Foundry workflow](2_Develop_AI_Agents_with_Azure/z10c-build-workflow-ms-foundry/README.md) | Invoke an existing published remote support workflow; the client does not create or deploy it. |
| [z12 - Remote agents with A2A](2_Develop_AI_Agents_with_Azure/z12-build-remote-agents-with-a2a/README.md) | Run local title, outline, and routing services with Agent-to-Agent communication. |

## Prerequisites

- Windows PowerShell or PowerShell on Windows for the shared launcher.
- Git, Python with `venv` and `pip`, and Azure CLI available on `PATH`.
  Agent Framework labs require Python 3.11 or later; check the selected guide
  and dependency manifest for its requirements.
- Access to the existing Azure/Foundry resources required by the selected lab,
  an appropriate model deployment, permissions, and available quota.
- VS Code and Foundry Toolkit for exercises that use the extension playground.
- For Work IQ only: the installed Work IQ CLI, its sign-in prerequisites,
  entitlement, and any required tenant consent.

This is not a one-command infrastructure deployment. Some labs create
temporary agents; others require an agent, connected knowledge source, Search
index, or published workflow to exist first. Follow the individual guide
before running a client.

## Quick start

Clone the repository, then run all following commands from its root:

```powershell
git clone https://github.com/jvargh/workshop-ai-apps-and-agents.git
Set-Location .\workshop-ai-apps-and-agents
az login
```

### Run a model-based application

Create Lab 03's local configuration only if it does not already exist:

```powershell
$lab = ".\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk"
if (-not (Test-Path -LiteralPath "$lab\.env")) {
    Copy-Item "$lab\.env.example" "$lab\.env"
}
```

Edit that lab's `.env`, replacing the endpoint and deployment placeholders,
then run:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py -Install
```

Follow the [Lab 03 guide](1-Develop_GenAI_Apps_with_Foundry/03-foundry-sdk/README.md)
for prompts and the other SDK modes.

### Run an agent with custom tools

Alternatively, follow the [Lab 07 guide](2_Develop_AI_Agents_with_Azure/07-customtools/README.md).
Copy that lab's `.env.example` to `.env` without overwriting existing settings,
configure its project endpoint and model deployment, then run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\07-customtools\ agent.py -Install
```

### Launcher behavior

The [shared launcher](run-lab.ps1) creates and activates a repository-local
`.labenv`, installs the selected lab's dependencies **only with `-Install`**,
and runs Python from that lab's directory. Pass the folder first and the
Python filename as a separate argument. Later runs normally omit `-Install`.

**`-Install` is not install-only:** it starts the selected program immediately
after installing dependencies. Some scripts make billable calls or create
cloud objects before displaying a prompt; others run automatically without
any prompt. Read the selected guide first.

Dependencies vary across labs, and installing all manifests into the shared
environment can introduce SDK conflicts. Install only what the selected lab
requires, and do not run concurrent installations into `.labenv`.

## Configuration and authentication

Keep configuration local to each lab. Use the exact keys in its `.env.example`;
endpoint types and variable names are not interchangeable.

| Setting | Used for |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Module 1 model clients: `https://<resource>.openai.azure.com/openai/v1/`. This is not a project URL. |
| `MODEL_DEPLOYMENT` | Module 1 model deployment name. |
| `PROJECT_ENDPOINT` | Most project/agent clients: `https://<resource>.services.ai.azure.com/api/projects/<project>`. |
| `MODEL_DEPLOYMENT_NAME` | Agent clients that select a model deployment. |
| `AZURE_AI_PROJECT_ENDPOINT` / `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Lab 11's project and model settings. |
| `AGENT_NAME` / `WORKFLOW_NAME` | Existing remote assets for labs that retrieve an agent or invoke a published workflow. |

Use the **deployment name**, not merely a model-family or catalog ID. Model-only
clients, project agents, Search, cloud evaluation, and Work IQ have different
permission requirements. Local Azure authentication uses `DefaultAzureCredential`
or `AzureCliCredential`, depending on the lab; `az login` does not by itself
grant resource access or Microsoft 365 consent.

## Local checks and validation

Offline regression tests are included for the Foundry clients and several
agent labs. After preparing the relevant dependencies, examples are:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\1-Develop_GenAI_Apps_with_Foundry\tests -v
.\.labenv\Scripts\python.exe -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\07-customtools -p "test_*.py" -v
```

Use each guide's test command for other labs. These checks do not establish
live Azure access, model availability, tool execution, or answer accuracy.
Recorded runs and captured output in the guides are historical examples,
not a guarantee that your configuration has been validated.

## Sources, privacy, costs, and cleanup

- The labs adapt Microsoft Learn exercises. Module 1 retains downloaded
  upstream guides, starter code, a [source manifest](1-Develop_GenAI_Apps_with_Foundry/SOURCE-MANIFEST.json),
  and the [upstream MIT license](1-Develop_GenAI_Apps_with_Foundry/UPSTREAM-LICENSE.txt).
  Follow each lab's official-guide links for its source and portal setup.
- [Git ignore rules](.gitignore) exclude local environment files, virtual
  environments, caches, downloaded reference checkouts, and selected generated
  output. Not every report filename is ignored: review new files before staging.
  Never publish credentials, workplace content, private transcripts, or
  unsanitized resource configuration.
- Use synthetic data. Work IQ can access authorized Microsoft 365 content;
  Azure sign-in and workplace-data authorization are separate.
- Model inference, evaluation, fine-tuning, Search, and hosted resources can
  incur charges. Inspect configured tools and remote workflow actions before
  invoking them; a displayed draft or escalation message is not proof of an
  external action.
- Cleanup differs by lab. Some clients delete their own temporary resources;
  conversations, evaluation objects, datasets, or agent versions can remain.
  Review the selected guide and saved resource IDs. Do not delete a shared
  resource group or unrelated resources to finish a lab.
