# Workshop: AI Apps and Agents with Microsoft Foundry

- [Module 1 PDF - Develop generative AI apps in Azure](AI-103T00-ENU-Module01-DevelopGenerativeAIAppsInAzure%E2%80%8B.pdf)
- [Module 2 PDF - Develop AI agents on Azure](AI-103T00-ENU-Module02-DevelopAIAgentsonAzure.pdf)
- [Module 3 PDF - Develop natural language solutions in Azure](AI-103T00-ENU-Module03-DevelopNaturalLangSolutionsInAzure.pdf)
- [Module 4 PDF - Extract insights from visual data](AI-103T00-ENU-Module04-ExtractInsightsFromVisualData.pdf)

Hands-on Python labs for developing generative AI applications and AI agents
with Microsoft Foundry and Azure, plus language, speech, and visual-data
solutions. The repository contains **four modules covering labs 01-22 and
supplemental exercises**. Implemented labs include configuration templates,
dependencies, sample data, and a shared PowerShell launcher.

Start with labs 01-05 for model-based applications, then labs 06-11 for agents.
Continue with labs 12-17 for language and speech, and labs 18-22 for visual
data and Content Understanding. Folders prefixed with `z` contain supplemental
exercises. Each lab guide describes its prerequisites, implementation status,
run commands where available, validation history, and cleanup limitations.

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

### 3. Develop language solutions with Azure AI

[Module overview](3_Develop_Language_Soltns_with_AzureAI/README.md)

| Lab | Focus |
|---|---|
| [12 - Analyze text](3_Develop_Language_Soltns_with_AzureAI/12-analyze-text/README.md) | Analyze text with Azure AI Language. |
| [13 - Text analysis agent](3_Develop_Language_Soltns_with_AzureAI/13-text-analysis-agent/README.md) | Query an existing Foundry agent configured with the Azure Language MCP tool. |
| [14 - Speech-capable generative AI models](3_Develop_Language_Soltns_with_AzureAI/14-use-speech-capable-genai-models/README.md) | Generate speech from text and transcribe a supplied recording using Azure OpenAI deployments. |
| [15 - Recognize and synthesize speech](3_Develop_Language_Soltns_with_AzureAI/15-recognize-and-synth-speech/README.md) | Synthesize a voicemail greeting and recognize speech from sample WAV files with Azure Speech. |
| [16 - Azure Speech in an agent](3_Develop_Language_Soltns_with_AzureAI/16-use-azure-speech-in-agent/README.md) | Incomplete speech-client starter; not a runnable application. |
| [17 - Voice Live agent](3_Develop_Language_Soltns_with_AzureAI/17-develop-voice-live-agent/README.md) | Connect microphone input and audio playback to an existing Foundry agent through Azure Voice Live. |
| [z - Translation](3_Develop_Language_Soltns_with_AzureAI/z-translation/README.md) | Translate text or recognize, translate, and synthesize speech with the respective Azure services. |

Language labs run from nested runtime folders, not the numbered navigation
folders. See the module overview for each runtime path.

### 4. Extract insights from visual data on Azure

[Module overview](4_Extract_Insights_From_Visual_Data_On_Azure/README.md)

| Lab | Focus |
|---|---|
| [18 - Vision-enabled chat](4_Extract_Insights_From_Visual_Data_On_Azure/18-develop-vision-enabled-chatapp/README.md) | Chat about local images and images supplied by URL. |
| [19 - Generate images with AI](4_Extract_Insights_From_Visual_Data_On_Azure/19-generate-images-with-ai/README.md) | Generate images with a deployed image-generation model. |
| [20 - Analyze media with Content Understanding](4_Extract_Insights_From_Visual_Data_On_Azure/20-analyze-media-with-content-understanding/README.md) | Extract image descriptions and tags using an existing published analyzer. |
| [21 - Extract information from multimodal content](4_Extract_Insights_From_Visual_Data_On_Azure/21-extract-info-from-mm-content/README.md) | Portal-based exercise and assets-only starter; no runnable Python application. |
| [22 - Content Understanding client](4_Extract_Insights_From_Visual_Data_On_Azure/22-develop-content-understanding-client-app/README.md) | Create a business-card analyzer and extract contact fields from local images. |
| [z - Knowledge mining with Azure AI Search](4_Extract_Insights_From_Visual_Data_On_Azure/zcreate-knowledge-mining-with-azureai-search/README.md) | Build and query a Search enrichment pipeline; recorded PDF upload is blocked by storage network policy, so end-to-end enrichment remains unverified. |

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
- For language and visual-data labs: access to the Azure Language, Speech,
  Translator, Voice Live, Content Understanding, or Search services required
  by the selected exercise. Speech playback and microphone scenarios also
  require working local audio devices and permissions.

This is not a one-command infrastructure deployment. Some labs create
temporary agents; others require an agent, connected knowledge source, Search
index, or published workflow to exist first. Follow the individual guide
before running a client. Labs 16 and 21 are incomplete starters, not working
applications to launch.

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

### Run language and visual-data clients

Follow the [language module setup](3_Develop_Language_Soltns_with_AzureAI/README.md)
or [visual-data module setup](4_Extract_Insights_From_Visual_Data_On_Azure/README.md).
Copy the chosen **runtime folder's** `.env.example` to `.env` only if missing,
then configure its service access before running either example:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis\ text-analysis.py -Install
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py -Install
```

These are separate exercises, not a batch setup command. Install and run only
the selected lab. Some input images, recordings, and generated outputs are
local-only; follow the selected guide to obtain required samples.

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

Keep configuration local to each lab's runtime folder. Use the exact keys in
its `.env.example`; endpoint types and variable names are not interchangeable.

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

Modules 3 and 4 also use service-specific resource-root endpoints and
configuration keys. Do not substitute a Foundry project URL or the OpenAI v1
URL for a Language, Speech, Translator, Voice Live, or Content Understanding
endpoint; follow that runtime's guide.

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
- Root Git ignore and attributes configuration files are local-only and are
  not included in clones. Configure local ignore rules for environment files,
  virtual environments, caches, downloaded reference checkouts, and generated
  output before running labs or staging files. Never publish credentials,
  workplace content, private transcripts, or unsanitized resource configuration.
- Use synthetic data. Work IQ can access authorized Microsoft 365 content;
  Azure sign-in and workplace-data authorization are separate. Language,
  speech, and visual-data clients can send text, recordings, images, and
  extracted personal data to Azure; use only authorized inputs and keep private
  recordings, business-card data, and analysis output local.
- Model inference, evaluation, fine-tuning, Search, and hosted resources can
  incur charges. Inspect configured tools and remote workflow actions before
  invoking them; a displayed draft or escalation message is not proof of an
  external action.
- Cleanup differs by lab. Some clients delete their own temporary resources;
  conversations, evaluation objects, datasets, or agent versions can remain.
  Review the selected guide and saved resource IDs. Do not delete a shared
  resource group or unrelated resources to finish a lab.
