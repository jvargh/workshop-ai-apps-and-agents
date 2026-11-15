# Lab 9 - Query product knowledge with Foundry IQ

[Official lab](https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/Exercises/04-integrate-agent-with-foundry-iq.html) | [Agent labs](../README.md) | [Repository setup](../../README.md)

Foundry IQ connects an agent to a searchable knowledge base so it can answer from supplied documents rather than rely only on its training. This walkthrough uses the existing knowledge-grounded agent and project configured in this lab's `.env` to answer questions about Contoso's outdoor products.

[agent_client.py](agent_client.py) retrieves that agent, starts a conversation, sends your questions, and handles any knowledge-tool approval requests. It does **not** create a Search resource, upload documents, build a knowledge base, or change the agent's configuration.

## Table of contents

- [1. Confirm the existing agent and knowledge connection](#1-confirm-the-existing-agent-and-knowledge-connection)
- [2. Configure the Python client](#2-configure-the-python-client)
- [3. Use automatic approval for the knowledge tool](#3-use-automatic-approval-for-the-knowledge-tool)
- [4. Install dependencies separately](#4-install-dependencies-separately)
- [5. Run the guide's product questions](#5-run-the-guides-product-questions)
  - [Check a few facts against the supplied documents](#check-a-few-facts-against-the-supplied-documents)
- [6. Review the outcome and finish](#6-review-the-outcome-and-finish)
- [Troubleshooting, privacy, and cleanup](#troubleshooting-privacy-and-cleanup)
- [Offline checks](#offline-checks)
- [Validation and conclusion](#validation-and-conclusion)
- [How the client works](#how-the-client-works)
  - [Connection and agent ownership](#connection-and-agent-ownership)
  - [Questions and optional approval rounds](#questions-and-optional-approval-rounds)
  - [Answers, references, and history](#answers-references-and-history)
  - [Foundry IQ prerequisites](#foundry-iq-prerequisites)
- [Captured output](#captured-output)
  - [1. Configuration, sign-in, and dependency precheck](#1-configuration-sign-in-and-dependency-precheck)
  - [2. Install command and setup exit](#2-install-command-and-setup-exit)
  - [3. Guide questions - original conversation](#3-guide-questions---original-conversation)
    - [3.1. Startup and blank input](#31-startup-and-blank-input)
    - [3.2. Outdoor product categories](#32-outdoor-product-categories)
    - [3.3. Tent weatherproof features](#33-tent-weatherproof-features)
    - [3.4. Daypacks versus expedition backpacks](#34-daypacks-versus-expedition-backpacks)
    - [3.5. Weekend accessories - failed first attempt](#35-weekend-accessories---failed-first-attempt)
  - [4. Remaining guide questions - paced retry in a new conversation](#4-remaining-guide-questions---paced-retry-in-a-new-conversation)
    - [4.1. Startup](#41-startup)
    - [4.2. Weekend hiking accessories - successful retry](#42-weekend-hiking-accessories---successful-retry)
    - [4.3. Contextual pricing follow-up](#43-contextual-pricing-follow-up)
    - [4.4. Local history](#44-local-history)
    - [4.5. Quit](#45-quit)
  - [5. Playground questions - exercised through Python, not the portal UI](#5-playground-questions---exercised-through-python-not-the-portal-ui)
    - [5.1. Startup](#51-startup)
    - [5.2. Tent types](#52-tent-types)
    - [5.3. XL backpacks](#53-xl-backpacks)
    - [5.4. Available camping accessories](#54-available-camping-accessories)
    - [5.5. Quit](#55-quit)
  - [6. Exact README offline checks](#6-exact-readme-offline-checks)
  - [7. Outcome, source verification, and cleanup](#7-outcome-source-verification-and-cleanup)

## 1. Confirm the existing agent and knowledge connection

In Foundry, open the project identified by `PROJECT_ENDPOINT` and select the agent named by `AGENT_NAME`. Confirm it has the product-expert instructions and an active Foundry IQ connection to the Contoso knowledge base.

The [data folder](data/) contains the sample product documents and their Markdown counterparts. The exercises use information about tents, backpacks, and camping accessories. Keeping those files locally does not make them available to the agent: they must already be indexed in its connected knowledge source.

If this setup is missing, complete the portal setup in the [official guide](https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/Exercises/04-integrate-agent-with-foundry-iq.html) before running the client. This is not the separate provisioning implementation in [supplemental lab z10a](../z10a-m365-teams-integration/).

For a quick portal check, try the guide's questions:

| Playground question | What to review |
|---|---|
| `What types of tents does Contoso offer?` | Named products and categories from the tents catalog, not generic tent advice. |
| `Tell me about which backpacks are available in XL.` | Sizes and model names supported by the backpack guide. |
| `What camping accessories are available?` | Items from the accessories document. |

Review any citations or tool details. A fluent answer alone does not prove the connected knowledge source was used.

## 2. Configure the Python client

Run all terminal commands in **PowerShell from the repository root**. Keep a working `.env`; create one from [.env.example](.env.example) only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env.example .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env
}
az login
```

Edit this lab's `.env`:

| Setting | What to enter |
|---|---|
| `PROJECT_ENDPOINT` | The full existing project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. This client needs the project endpoint, not a model-only `/openai/v1/` URL. |
| `AGENT_NAME` | The actual name of the existing knowledge-grounded agent in your selected project. |

Your identity needs permission to retrieve and invoke the agent. Its knowledge connection must separately have access to the backing Search/storage services. Signing into the project does not automatically grant that connection access.

## 3. Use automatic approval for the knowledge tool

This walkthrough now uses automatic approval for the configured, trusted knowledge-base MCP tool. Its agent-definition setting is `require_approval="never"`, so Foundry can run lookups without asking you to type `yes` each time. This change has been applied to the configured agent while preserving its other tools and settings.

If you use another agent, check its setting in **Foundry Toolkit for VS Code**:

1. Select the correct project under **Microsoft Foundry Resources**.
2. Open **Agents > Prompt Agents**, then select the agent named by `AGENT_NAME` in Agent Builder.
3. In **Tools**, locate the actual **`kb-knowledgebase...`** tool. Do not change an unrelated Web search or standalone Azure AI Search tool and assume that affects Foundry IQ.
4. Open its **… > Configure**, enable auto-approval for this trusted knowledge tool rather than **Never auto-approve tools**, save, and select **Deploy** to publish the updated agent version.

Apply automatic approval only to the trusted, read-only knowledge tool. Do not automatically approve unrelated tools that can change data or perform actions.

The client prints the configured MCP tool label and approval setting on startup. With `never`, it also explains that manual prompts are disabled. The original guide's manual-approval exercise is still supported: use **Never auto-approve tools** (`require_approval="always"`) if you want to practice reviewing each request.

## 4. Install dependencies separately

After configuring access, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py -Install
```

**The launcher installs packages and then starts the client.** It retrieves the existing agent and creates a conversation. At `You:`, enter `quit` and wait for the cleanup/completion messages and the PowerShell prompt before proceeding.

Entering only `quit` sends no product question, but a cloud conversation has already been created. The client closes its SDK connections; it does not delete the existing agent, knowledge resources, or conversation. [requirements.txt](requirements.txt) defines the dependencies.

## 5. Run the guide's product questions

Launch a new session without reinstalling:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py
```

Follow `[1/4]` through `[4/4]`: configuration, authentication, existing-agent lookup, and conversation creation. Confirm that the loaded agent and configured knowledge tool match the intended setup.

At `You:`, enter these questions **one at a time inside the client, not in PowerShell**. Knowledge lookups run automatically; no yes/no input is expected for the configured knowledge tool. Wait for the final `Agent:` answer and the next `You:` prompt before entering another question.

| Step | Input or action | What to review |
|---|---|---|
| 1 | Press Enter without typing anything. | `No model request was sent.` |
| 2 | `What types of outdoor products does Contoso offer?` | Product categories from the supplied documents, including tents, backpacks, and camping accessories. |
| 3 | `Tell me about the weatherproof features of your tents.` | Specific rain-fly/floor ratings and product features supported by the tents catalog. |
| 4 | `What's the difference between your daypacks and expedition backpacks?` | Capacity, load, construction, and intended-use differences from the backpack guide. |
| 5 | `What camping accessories would you recommend for a weekend hiking trip?` | Named accessories supported by the catalog and suited to the described trip. |
| 6 | `How much do those items typically cost?` | Prices for the items recommended in the preceding answer, not an unrelated shopping list. |
| 7 | `history` | Both your questions and the agent's answers, in order. This is local display and sends no new model request. |
| 8 | `quit` | The client closes its SDK connections and returns to PowerShell without deleting the agent. |

Look for `[Knowledge] Completed MCP call: kb-...` to confirm that a lookup actually completed. No approval prompt is expected when the tool uses `never`; some follow-ups may also reuse existing conversation context without another lookup.

`[Source]` lists each unique source once per answer: URLs are deduplicated by URL, and files by file ID. If a citation's title is the URL itself, the URL is printed only once on that line. Inline citations in the answer are preserved because separate claims can cite the same document. If no separate annotations are returned, the client says so; inspect references in the answer and any retrieval details. Do not mistake a completed tool call for proof that every generated statement is accurate.

### Check a few facts against the supplied documents

Use the local Markdown copies as a reference when reviewing the answers:

- [Tents catalog](data/contoso-tents-catalog.md): Alpine Explorer 2P lists a 3000mm rain fly and 5000mm floor; models have different ratings, so the answer should identify which product it describes.
- [Backpacks guide](data/contoso-backpacks-guide.md): the daypack category is 20-35 liters; expedition packs are larger and designed for heavier, longer trips. Expandable collars can increase a model's listed capacity.
- [Accessories catalog](data/contoso-camping-accessories.md): for example, HeadLamp Pro 500 is $49.99 and Water Filter Pro is $79.99. Check these amounts only if those items appear in the agent's recommendation.

These are sample-catalog facts, not live inventory, price availability, or weather-performance guarantees.

## 6. Review the outcome and finish

A successful run retrieves the configured agent, completes automatic knowledge lookups, answers the questions with relevant product details, and displays the full local history. The pricing follow-up should retain the context of the preceding recommendations.

The client does not save a chat transcript file. Its `history` command displays only the current session's questions and answers; restarting creates a new cloud conversation. No generated-file folder is part of this walkthrough.

If you switch back to manual mode, the client still displays each requested action and accepts yes/no decisions. A denial is returned to the service and is not evidence that the denied lookup ran. Invalid approval input is reprompted rather than silently approved.

## Troubleshooting, privacy, and cleanup

- **Agent/project not found:** Check the exact project endpoint and agent name. Do not enter a project or deployment name as `AGENT_NAME`.
- **Approval prompts still appear:** Restart the client after deploying the updated tool setting. Confirm the actual `kb-knowledgebase...` tool uses `never`. Requests from other tools can still require manual approval; do not approve them without review.
- **Lookup denied or fails:** Check the tool request and knowledge connection's permissions/authentication. Project login and knowledge-service access are separate.
- **Generic or unsupported answers:** Review the agent's instructions, active knowledge source, cited material, and local catalog. Having files in this repository does not upload or index them.
- **Failed/empty response:** The client raises an explicit error rather than returning a success-shaped fallback. Resolve the failure before continuing or treating an older answer as new evidence.
- **Privacy:** Questions, approval arguments, and answers may contain source information. Keep logs and knowledge content private and avoid sensitive test prompts.
- **Cleanup:** `quit`, EOF, or interruption closes the SDK clients and credential. The client does not delete the reusable agent, knowledge base, Search/storage resources, or cloud conversation. Remove only your own disposable test conversations as appropriate.

## Offline checks

After installation, run from the repository root:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $python = Join-Path (Get-Location) '.labenv\Scripts\python.exe'
    Push-Location .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ
    try {
        & $python -m unittest test_foundry_iq -v
        if ($LASTEXITCODE -ne 0) { throw 'Foundry IQ checks failed.' }
    } finally {
        Pop-Location
    }
}
```

Ten offline tests passed, covering approval rounds/IDs, denial and invalid input, no-approval responses, failed lookups, unique source display, complete history, and preservation of the existing agent.

## Validation and conclusion

The current automatic-approval setting was verified with a live knowledge question: the MCP lookup completed, a product comparison and source URL annotations were returned, and **zero manual approval prompts** appeared. The client exited normally, and that successful test conversation was deleted. The private record is saved in `results\foundry-iq-auto-approval-validation.json`.

The earlier manual-approval walkthrough completed using the configured project and agent. Those results remain useful evidence; its seven prompts describe that earlier mode, not the current automatic-approval behavior:

| Check | Observed result |
|---|---|
| Agent configuration | The earlier run used `always`. The knowledge tool has since been changed to `never` at your request; readback confirmed all other definition fields were preserved. |
| Guide questions | All **five** client questions returned product answers, including the pricing follow-up. |
| Approval and retrieval | **Seven approvals** were supplied and **seven knowledge-base MCP calls** completed. Some questions needed more than one lookup. |
| Product facts | The tent ratings and backpack categories matched the sample documents. All **13 price rows** in the follow-up matched catalog values; the sample budget bundle summed to **$732.91**. |
| Sources | No separate URL/file citation annotations were returned in this run. The client reported that limitation; selected facts were checked against the local catalog copies rather than claiming citation validation. |
| History and exit | `history` displayed all five user questions and their answers. `quit` closed the client normally. |
| Test cleanup | Only the two conversations created for validation were deleted. The existing agent, its updated approval setting, and knowledge resources remain in place. |

The focused offline suite also passed. A private test record is saved in `results\foundry-iq-validation.json` and ignored by Git; ordinary client runs do not automatically save transcripts. Portal provisioning and every possible product claim were not independently validated.

**Conclusion:** This lab connects to an existing knowledge-grounded agent and runs trusted lookups automatically. Manual approval remains available when required. Check completed tool activity, supporting product information, and follow-up context—not just whether the program starts.

## How the client works

### Connection and agent ownership

The program loads this lab's `.env`, authenticates with `DefaultAzureCredential`, and creates `AIProjectClient` plus an OpenAI-compatible client. It retrieves the existing agent by name and creates an empty conversation. Context managers close the clients and credential when the session ends.

Unlike the custom-function and MCP-creation labs, it does not create or delete an agent version. Knowledge sources and tool settings belong to the existing Foundry configuration.

### Questions and optional approval rounds

`conversations.items.create` stores the user's message in the cloud conversation. The client also adds it to the local history before requesting an agent response. The response request references the agent and conversation, with empty `input` because the user message is already stored.

For each completed response, the client checks MCP discovery/call results and looks for `mcp_approval_request` items. With the knowledge tool set to `never`, its lookup runs in Foundry without that approval exchange. If another tool or a manual-mode configuration returns an approval request, the client displays its name, server label, and decoded JSON arguments, then collects a yes/no decision. Each `mcp_approval_response` carries the matching request ID.

When decisions are needed, they are added to the same conversation and the agent is asked to continue. The loop repeats if more approvals are requested. Failed tool calls, invalid arguments, missing approval IDs, incomplete responses, and empty final answers remain explicit errors.

### Answers, references, and history

Once no approvals remain, the client prints the final text and a deduplicated list of URL/file citation annotations in the response's message content. Deduplication spans all messages in that answer and resets for the next turn; it does not alter the answer's inline citation markers. The client does not assume a separate top-level `citations` property exists.

The successful answer is added to local history after the user's question. `history` prints both roles without invoking the model. This local list is for display; the cloud conversation ID supplies the context used by the agent on later turns.

### Foundry IQ prerequisites

The agent's MCP knowledge tool calls the connected knowledge base, which retrieves from the configured Search/storage sources. The Python client does not read the local catalog files when answering, provision those resources, or repair connection permissions. Its responsibilities are sending messages, handling approvals when required, displaying results, and closing its own SDK connections.

## Captured output

These are new, actual PowerShell runs from the repository root on the local
date above, using the existing `.env`, Azure sign-in, and product agent. The
earlier validation records above describe separate historical runs. No agent,
tool approval setting, knowledge source, Search/storage resource, or shared
Python package was changed for this capture.

Inputs were supplied only after the corresponding `You:` prompt and inserted
into the transcript because redirected stdin is not echoed by the client.
Agent names, conversation/request identifiers, deployment names, absolute
repository paths, knowledge-tool labels, and nonpublic source URLs are replaced
with placeholders. The three source-URL placeholders consistently identify
three distinct returned URLs; they are redactions, not clickable citations.
Inline reference tokens are transcribed as `<citation:turn:source>` so the
Markdown/chat renderer does not consume them; their returned numeric indexes
are preserved. Public Microsoft documentation links, answer wording, and
numerical results are otherwise preserved. All product facts and prices concern
the **synthetic Contoso sample catalogs**, not live retail inventory or
performance guarantees.

The first guide session answered three questions and then failed with HTTP
`429`. Its failure is captured below rather than counted as a successful
recommendation. A completed lookup establishes tool execution, not the accuracy
of every generated claim. No manual approval decision was required or supplied:
the existing knowledge tool reported `never`. No unrelated remote action was
authorized.

### 1. Configuration, sign-in, and dependency precheck

The section 2 conditional copy was evaluated exactly as documented:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env.example .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\.env
}
```

The file existed, so no copy or edit occurred. Both settings were configured,
and the endpoint had the required HTTPS `/api/projects/` shape. The valid
sign-in was reused; the README's `az login` command was **not rerun**. Instead,
this read-only authentication check exited `0`, printing only token expiry:

```powershell
az account get-access-token --resource https://ai.azure.com --query expiresOn --output tsv
```

```text
2026-11-14 23:37:45.000000
```

Before permitting `-Install`, installed distribution metadata was checked
against every direct constraint and its recursive active dependency closure:

```text
azure-ai-projects==2.3.0: 2.3.0; satisfied=True
azure-identity: 1.25.3; satisfied=True
python-dotenv: 1.2.3; satisfied=True
openai<3: 2.54.0; satisfied=True
Recursively checked 33 installed distributions; constraints satisfied.
```

The existing shared environment and activation script were present. A read-only
SDK lookup also retrieved the configured agent and confirmed its MCP knowledge
tool used `never`; this precheck created no conversation and sent no model
question. No missing dependency or configuration repair was needed.

### 2. Install command and setup exit

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py -Install
```

All requirements were already satisfied. To make this concurrent package check
non-mutating, the child process used `PIP_CONFIG_FILE=NUL`, `PIP_NO_INDEX=1`,
`PIP_NO_DEPS=1`, `PIP_NO_CACHE_DIR=1`, and
`PIP_DISABLE_PIP_VERSION_CHECK=1`, with other inherited `PIP_*` overrides
removed. The complete dependency closure was checked beforehand; no install,
upgrade, uninstall, cache update, or shared environment change occurred.

Input: `quit` at the first prompt. Exit code: `0`. A cloud conversation was
created, but no product question or knowledge lookup was sent.

<details>
<summary>Actual dependency check and setup transcript</summary>

```text
Requirement already satisfied: azure-ai-projects==2.3.0 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\requirements.txt (line 1)) (2.3.0)
Requirement already satisfied: azure-identity in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: python-dotenv in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\requirements.txt (line 3)) (1.2.3)
Requirement already satisfied: openai<3 in .\.labenv\Lib\site-packages (from -r <repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\requirements.txt (line 6)) (2.54.0)
[1/4] Loading this lab's project endpoint and existing agent name...
Selected agent: <configured-agent-name>
This client does not create an agent, upload documents, or change its knowledge connections.
Model and knowledge-retrieval calls may incur charges.
[2/4] Connecting to Foundry with Microsoft Entra authentication...
[3/4] Retrieving the existing product agent...
Connected to agent: <configured-agent-name>
[Configured MCP] <knowledge-tool>; approval setting: never
[Approval] This MCP tool runs without manual approval prompts.
[4/4] Creating a new conversation for product questions...
Conversation created: <conversation-id>
Ask about Contoso products. Use history to review this session, or quit to exit.
You: quit
[Input] Quit requested. Ending the chat.
[Cleanup] Closing SDK clients and the Azure credential. The existing agent and cloud conversation are not deleted.
[Complete] Product-agent conversation ended.
```

</details>

### 3. Guide questions - original conversation

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py
```

The following turns share one new conversation. This launcher returned exit
code `1` when the fourth product question exceeded the model token rate limit.
The remaining inputs were not silently sent after the failure.

#### 3.1. Startup and blank input

```text
[1/4] Loading this lab's project endpoint and existing agent name...
Selected agent: <configured-agent-name>
This client does not create an agent, upload documents, or change its knowledge connections.
Model and knowledge-retrieval calls may incur charges.
[2/4] Connecting to Foundry with Microsoft Entra authentication...
[3/4] Retrieving the existing product agent...
Connected to agent: <configured-agent-name>
[Configured MCP] <knowledge-tool>; approval setting: never
[Approval] This MCP tool runs without manual approval prompts.
[4/4] Creating a new conversation for product questions...
Conversation created: <conversation-id>
Ask about Contoso products. Use history to review this session, or quit to exit.
You:
[Input] Please enter a question. No model request was sent.
```

#### 3.2. Outdoor product categories

```text
You: What types of outdoor products does Contoso offer?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Tools] Discovered 1 tools from <knowledge-tool>.
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Based on the Contoso product knowledge base, Contoso Outdoor offers these main types of outdoor camping and hiking products:

- **Tents and tent accessories** — including 2-person backpacking tents, 4-person family tents, specialty/4-season tents, ultralight solo shelters, footprints, stake kits, gear lofts, and seam sealer.<citation:6:0><citation:6:13><citation:6:9>
- **Backpacks and backpack accessories** — including technical daypacks, weekend backpacks, expedition packs, rain covers, hydration bladders, waterproof pack liners, and repair kits.<citation:6:7><citation:6:8><citation:6:12>
- **Sleeping systems** — including sleeping bags for cold-weather, three-season, and warm-weather camping, plus sleeping pads such as inflatable and closed-cell foam options.<citation:6:16><citation:6:4>
- **Camp furniture** — such as lightweight backpacking chairs, full-size folding camp chairs, and portable camp tables.<citation:6:3>
- **Cooking equipment** — including integrated stove systems, family cooksets, and fuel canisters.<citation:6:11>
- **Lighting** — including rechargeable headlamps and collapsible LED lanterns.<citation:6:11>
- **Safety, navigation, and emergency gear** — including GPS/navigation devices, first aid kits, emergency bivy shelters, and related safety items.<citation:6:2>
- **Miscellaneous trail and camp accessories** — such as trekking poles, portable solar panels, waterproof dry bags, and multi-tools.<citation:6:2><citation:6:5>

I found product information for camping, hiking, backpacking, and mountaineering gear in the knowledge base; I did not find evidence there for categories like apparel or footwear.

[Source] <knowledge-source-url-1>
[Source] <knowledge-source-url-2>
[Source] <knowledge-source-url-3>
```

One completed retrieval and three unique URL annotations were displayed.
The catalog contains the named categories; this particular overview does not
explicitly enumerate hydration, although the accessories catalog does.

#### 3.3. Tent weatherproof features

```text
You: Tell me about the weatherproof features of your tents.
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Contoso tents use a mix of **waterproof coatings, rain-fly designs, reinforced floors, seam protection, and wind/snow-focused structures** depending on the model.

### Key weatherproof features across Contoso tents

- **Waterproof rain flies and floors:** Models list separate waterproof ratings for the rain fly and floor. For example, the **Alpine Explorer 2P** has a **3000mm rain fly** and **5000mm floor**, while the **TrailMaster Lite 2P** has a **2000mm rain fly** and **3000mm floor**.<citation:10:6>

- **Full or extended rain-fly coverage:** Several tents include extended or full-coverage rain flies. The Alpine Explorer 2P has a **full coverage rain fly** with a stormproof design tested in **60 mph winds**, while the TrailMaster Lite 2P uses **extended rain fly coverage**.<citation:10:6>

- **Family tent rain protection:** The **SummitDome 4P** includes a **full-coverage rain fly with vestibule** and waterproof ratings of **1500mm rain fly / 2000mm floor**. The **MegaSpace 4P Cabin** steps up to **2000mm rain fly / 3000mm floor**, with a heavy-duty bathtub-style floor.<citation:10:2>

- **Welded floors and inverted seams:** The MegaSpace 4P Cabin includes Contoso’s **WeatherTec system**, featuring **patented welded floors and inverted seams** to help reduce water entry points.<citation:10:4>

- **Taped seams, storm flaps, and reinforced points:** The **BaseCamp Pro 6P** is designed for long-term group camping and includes a **3000mm rain fly / 5000mm floor**, an **extended rain fly**, **taped seams**, **storm flaps over all zippers**, **reinforced stress points**, and reinforced stake points.<citation:10:4>

- **Extreme-weather construction:** The **FourSeason Alpine 2P** is Contoso’s most technical tent, built for mountaineering and winter camping. It has a **5000mm rain fly / 10000mm floor**, double silicone-coated ripstop nylon, a ballistic nylon floor, a **full-coverage fly**, a geodesic structure, internal tensioning, **8 stake-out points**, a snow skirt, and is engineered for **extreme wind loads and snow accumulation**.<citation:10:8>

- **Ultralight weather protection:** The **UltraLite Solo 1P** has a **3000mm rain fly / 5000mm floor**, an integrated rain-fly single-wall hybrid design, **waterproof zipper**, **taped seams**, and a **bathtub floor**.<citation:10:8>

- **Condensation management:** Weatherproofing also includes ventilation. For example, the FourSeason Alpine 2P uses **adjustable vents at all corners** to help prevent condensation, while larger tents include mesh windows, roof vents, and ground vents.<citation:10:8><citation:10:4>

### Maintenance for long-term waterproofing

Contoso recommends drying tents completely before storage, cleaning only with mild soap and water, repairing small tears promptly, and **resealing seams annually** for maximum waterproofing. Contoso also offers a **Seam Sealer** accessory designed to maintain tent waterproofing over time.<citation:10:0>

[Source] <knowledge-source-url-1>
```

All seven models' displayed rain-fly/floor ratings match the local
[tents catalog](data/contoso-tents-catalog.md). The wind-test statement and
WeatherTec wording are sample-document claims, not independently tested
weather-performance evidence.

#### 3.4. Daypacks versus expedition backpacks

```text
You: What's the difference between your daypacks and expedition backpacks?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
The main difference is that **Contoso daypacks are built for single-day use and lighter loads**, while **expedition backpacks are built for extended trips, heavy loads, and technical mountain travel**.

| Category | Contoso Daypacks | Contoso Expedition Backpacks |
|---|---|---|
| **Typical capacity** | **20–35 liters** | **60–75 liters**, with extension collars up to **80–90L max** |
| **Best for** | Day hiking, biking, school, travel, scrambling, winter day hikes | Week-long trips, mountaineering, winter camping, international trekking, high-altitude expeditions |
| **Load range** | Not positioned for heavy overnight loads | **35–65 lbs** on Expedition Pro 65L; **40–80 lbs** on Summit Master 75L |
| **Weight** | Lighter: SummitTrail 25L is **1.3 lbs**; Explorer Pro 32L is **2.1 lbs** | Heavier but more supportive: Expedition Pro 65L is **5.2 lbs**; Summit Master 75L is **6.1 lbs** |
| **Frame/support** | Simple or lighter support systems; Explorer Pro has load-lifting shoulder straps and padded hip belt | Full load-carrying frames: internal aluminum stays, HDPE framesheet, advanced suspension, load-bearing hip belts |
| **Organization** | Hydration sleeve, water bottle pockets, front stash/organization pockets, trekking pole attachments | Sleeping bag compartments, detachable lids, large main compartments, side access, compression systems, crampon/helmet/ice tool carry |
| **Weather protection** | Water-resistant materials or DWR finish | More weather-focused materials like TPU coating, water-resistant zippers, triple waterproof coating, welded waterproof construction, rain covers |

### Daypacks: lighter, simpler, for daily or technical day use

Contoso’s daypacks fall in the **20–35L** range. The **SummitTrail 25L Daypack** is designed for day hikes, urban exploring, and daily commutes, with a 25L capacity, 1.3 lb weight, hydration compatibility, side bottle pockets, trekking pole straps, and reflective accents.<citation:14:0>

For more technical day use, the **Explorer Pro 32L** adds a suspended mesh back panel, load-lifting shoulder straps, padded hip belt, hydration sleeve, trekking pole attachments, an ice axe loop, gear loops, and an emergency whistle. It’s best for technical day hikes, scrambling, via ferrata, and winter hiking.<citation:14:1>

### Expedition packs: much larger, stronger, and more load-capable

Contoso’s expedition packs are in the **60–75L** class. The **Expedition Pro 65L** expands to **80L max**, weighs 5.2 lbs, carries **35–65 lbs**, and uses removable/adjustable internal aluminum stays. It also includes a waterproofing-focused TPU coating, water-resistant zippers, reinforced compression straps, a premium integrated rain cover, sleeping bag compartment, ice tool loops, crampon patch, and helmet attachment straps.<citation:14:4>

The **Summit Master 75L** is Contoso’s largest pack, expanding to **90L max** and carrying **40–80 lbs**. It has a dual aluminum stay system, HDPE framesheet, triple waterproof coating, welded waterproof construction, advanced suspension, ultra-padded hip belt, triple compartment design, full-length side access, heavy-duty lash points, ski/snowboard carry, and winter-specific features.<citation:14:2><citation:14:3>

**Bottom line:** choose a **daypack** for day hikes and light technical outings; choose an **expedition backpack** when you need to carry shelter, sleep system, food, technical gear, and heavy loads for multi-day or alpine trips.

[Source] <knowledge-source-url-2>
```

The category capacities, model weights, expedition load ranges, and expandable
80L/90L maximum capacities agree with the
[backpacks guide](data/contoso-backpacks-guide.md). There was one completed
lookup and one deduplicated source URL for this answer.

#### 3.5. Weekend accessories - failed first attempt

```text
You: What camping accessories would you recommend for a weekend hiking trip?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Cleanup] Closing SDK clients and the Azure credential. The existing agent and cloud conversation are not deleted.
```

<details>
<summary>Actual failure traceback (redacted)</summary>

```text
Traceback (most recent call last):
  File "<repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\agent_client.py", line 170, in <module>
    main()
    ~~~~^^
  File "<repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\agent_client.py", line 161, in main
    send_message_to_agent(text, client, agent.name, conversation.id, history)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<repository-root>\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\agent_client.py", line 58, in send_message_to_agent
    response = client.responses.create(
        conversation=conversation_id, input="",
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    )
  File "<repository-root>\.labenv\Lib\site-packages\openai\resources\responses\responses.py", line 1016, in create
    return self._post(
           ~~~~~~~~~~^
        "/responses",
        ^^^^^^^^^^^^^
    ...<47 lines>...
        stream_cls=Stream[ResponseStreamEvent],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "<repository-root>\.labenv\Lib\site-packages\openai\_base_client.py", line 1375, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<repository-root>\.labenv\Lib\site-packages\openai\_base_client.py", line 1148, in request
    raise self._make_status_error_from_response(err.response) from None
openai.RateLimitError: Error code: 429 - {'error': {'code': 'rate_limit_exceeded', 'message': 'Model deployment rate limit exceeded. Your requests to gpt-5.5 for <model-deployment> in westus3 have exceeded token rate limit.. To request more quota, see https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits', 'type': 'error', 'additionalInfo': {'request_id': '<request-id>', 'rate_limit_source': 'rapi'}}}
```

</details>

No recommendation answer or completed fourth lookup was printed. The pricing
follow-up, `history`, and `quit` were not reached in this session. The `finally`
cleanup ran, but the normal `[Complete]` message did not. No quota change,
deployment change, or runtime-code patch was made to hide this service limit.

### 4. Remaining guide questions - paced retry in a new conversation

After a 90-second cooldown, the same README command was launched again. The
capture waited 25 seconds before each product prompt to reduce concurrent
model traffic. This was a new conversation, not an attempted resumption of the
failed one. The recommendation and its pricing follow-up therefore share their
own context. Exit code: `0`; two completed lookups, zero manual approvals.

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py
```

#### 4.1. Startup

```text
[1/4] Loading this lab's project endpoint and existing agent name...
Selected agent: <configured-agent-name>
This client does not create an agent, upload documents, or change its knowledge connections.
Model and knowledge-retrieval calls may incur charges.
[2/4] Connecting to Foundry with Microsoft Entra authentication...
[3/4] Retrieving the existing product agent...
Connected to agent: <configured-agent-name>
[Configured MCP] <knowledge-tool>; approval setting: never
[Approval] This MCP tool runs without manual approval prompts.
[4/4] Creating a new conversation for product questions...
Conversation created: <conversation-id>
Ask about Contoso products. Use history to review this session, or quit to exit.
```

#### 4.2. Weekend hiking accessories - successful retry

```text
You: What camping accessories would you recommend for a weekend hiking trip?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Tools] Discovered 1 tools from <knowledge-tool>.
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
For a **weekend hiking/backpacking trip**, I’d prioritize lightweight, compact accessories that cover sleep, cooking, lighting, water, safety, and comfort:

| Priority | Recommended Contoso item | Why it’s a good fit |
|---|---|---|
| **Sleep system** | **Summer Lite 40°F Sleeping Bag** — SKU **SLP-SL-40**, **$79.99** | Lightweight at **2.3 lbs**, packs to **7" x 14"**, and is designed for warm-weather camping and backpacking. Good for mild weekend trips. <citation:6:5> |
| **Sleeping pad** | **FoamRest Trail** — SKU **PAD-FRT**, **$44.99** | Very reliable for hiking: **14 oz**, no inflation needed, won’t puncture/leak, and doubles as a sit pad or pack frame. Best for ultralight backpacking and budget camping. <citation:6:5> |
| **Cooking** | **Trail Chef Stove System** — SKU **COOK-TCS**, **$149.99** | A strong backpacking choice: weighs **14.2 oz including pot**, boils 16 oz of water in **2.5 minutes**, has a built-in igniter, and is best for solo backpacking and fast cooking. Fuel canister sold separately. <citation:6:1><citation:6:4> |
| **Fuel** | **Fuel Canisters** — SKU **COOK-FC-SIZE**, **$7.99–$12.99** | Isobutane-propane canisters that work in cold weather, are resealable, recyclable when empty, and use a universal thread. <citation:6:4> |
| **Lighting** | **HeadLamp Pro 500** — SKU **LGT-HLP-500**, **$49.99** | Better than a handheld light for hiking: **500 lumens**, **3.2 oz**, IPX6 weather resistance, red-light mode, battery indicator, and best for night hiking and camping. <citation:6:4> |
| **Water treatment** | **Water Filter Pro** — SKU **HYD-WFP**, **$79.99** | Lightweight gravity filter at **10 oz**, filters **2L in 3 minutes**, and removes **99.99% bacteria** and **99.9% protozoa**—great if you’ll refill from natural sources. <citation:6:16> |
| **Water bottle** | **Water Bottle Insulated 32oz** — SKU **HYD-WB-32**, **$34.99** | Durable stainless bottle, leak-proof, BPA-free, keeps drinks cold for **24 hours** or hot for **12 hours**. <citation:6:16> |
| **Safety** | **First Aid Kit – Trail** — SKU **SAF-FAK-TRL**, **$49.99** | Treats **1–4 people for 1–4 days** and includes blister treatment, bandages, gauze, antiseptic wipes, pain relievers, emergency blanket, CPR face shield, and guide. Best for hiking and camping. <citation:6:0> |
| **Emergency backup** | **Emergency Shelter Bivy** — SKU **SAF-ESB**, **$29.99** | Only **4.8 oz**, waterproof/windproof, reflects **90% of body heat**, and works as an ultralight backup shelter. <citation:6:0> |
| **Trekking support** | **Trekking Poles – Carbon** — SKU **MISC-TP-CARB**, **$129.99** | Lightweight carbon poles, **16 oz per pair**, adjustable **24"–54"**, with cork grips, anti-shock system, and interchangeable tips. Best for backpacking and hiking. <citation:6:0> |
| **Tool/repair utility** | **Multi-Tool** — SKU **MISC-MT**, **$79.99** | A 17-in-1 tool with pliers, knife, saw, scissors, can opener, screwdrivers, awl, and more; best for camping, hiking, and emergency kits. <citation:6:2> |
| **Weather protection for gear** | **Dry Bags Set** — SKU **MISC-DB-SET**, **$39.99** | Three waterproof bags—**5L, 10L, 20L**—with roll-top closure, IPX6 rating, welded seams, and floating design; useful for rainy-weather camping. <citation:6:2> |

**My “must-pack” shortlist:** HeadLamp Pro 500, Water Filter Pro, First Aid Kit – Trail, Emergency Shelter Bivy, FoamRest Trail, Summer Lite 40°F bag, Trail Chef Stove System + fuel, and Dry Bags Set. If your route is hilly or rocky, add the Carbon Trekking Poles.

[Source] <knowledge-source-url-3>
```

The returned products, SKUs, and listed prices were checked against the local
[accessories catalog](data/contoso-camping-accessories.md). The recommendation
assumes mild weather; the catalog's 40°F bag is a warm-weather option, not a
universal recommendation for every weekend or destination. Treatment percentages
and emergency-shelter properties are synthetic catalog claims, not independent
safety testing or guarantees.

#### 4.3. Contextual pricing follow-up

```text
You: How much do those items typically cost?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Here are the **catalog prices** for the items I recommended for a weekend hiking/backpacking trip:

| Item | SKU | Price |
|---|---:|---:|
| Summer Lite 40°F Sleeping Bag | SLP-SL-40 | **$79.99** <citation:10:0> |
| FoamRest Trail sleeping pad | PAD-FRT | **$44.99** <citation:10:0> |
| Trail Chef Stove System | COOK-TCS | **$149.99** <citation:10:1> |
| Fuel Canister | COOK-FC-SIZE | **$7.99 / $9.99 / $12.99** depending on 110g, 230g, or 450g size <citation:10:7> |
| HeadLamp Pro 500 | LGT-HLP-500 | **$49.99** <citation:10:7> |
| Water Filter Pro | HYD-WFP | **$79.99** <citation:10:3> |
| Water Bottle Insulated 32oz | HYD-WB-32 | **$34.99** <citation:10:3> |
| First Aid Kit – Trail | SAF-FAK-TRL | **$49.99** <citation:10:8> |
| Emergency Shelter Bivy | SAF-ESB | **$29.99** <citation:10:8> |
| Trekking Poles – Carbon | MISC-TP-CARB | **$129.99** <citation:10:8> |
| Dry Bags Set | MISC-DB-SET | **$39.99** <citation:10:9> |
| Multi-Tool | MISC-MT | **$79.99** <citation:10:9> |

**Estimated total for the full list:** **$777.88–$782.88**, depending on fuel canister size.

If you want to keep it to the core “must-pack” items I suggested—sleeping bag, pad, stove, fuel, headlamp, water filter, first aid kit, emergency bivy, and dry bags—the estimated total is **$532.91–$537.91**.

Prices are based on the Contoso catalog and may change; the catalog notes that products and prices are subject to change and recommends checking the website for current availability and pricing <citation:10:17>.

[Source] <knowledge-source-url-3>
```

All 12 item rows, including the three fuel-size prices, match the sample
catalog. Independent decimal addition gives **$777.88–$782.88** for all
12 items and **$532.91–$537.91** for the nine-item core list, matching the
answer. The follow-up retained the preceding recommendation rather than
introducing an unrelated list.

#### 4.4. Local history

```text
You: history

CONVERSATION HISTORY

USER: What camping accessories would you recommend for a weekend hiking trip?

ASSISTANT: For a **weekend hiking/backpacking trip**, I’d prioritize lightweight, compact accessories that cover sleep, cooking, lighting, water, safety, and comfort:
```

The complete recommendation from section 4.2 was printed next. The second
user/assistant pair then began:

```text
USER: How much do those items typically cost?

ASSISTANT: Here are the **catalog prices** for the items I recommended for a weekend hiking/backpacking trip:
```

The complete pricing answer from section 4.3 followed. These are excerpts:
duplicate tables are not repeated here. Both full assistant-history entries
were compared with their preceding answers in the captured transcript and
matched exactly; role order was `USER`, `ASSISTANT`, `USER`, `ASSISTANT`.
No request or knowledge-call log appeared during `history`. This restarted
session's history does **not** contain the earlier three questions from
section 3.

#### 4.5. Quit

```text
You: quit
[Input] Quit requested. Ending the chat.
[Cleanup] Closing SDK clients and the Azure credential. The existing agent and cloud conversation are not deleted.
[Complete] Product-agent conversation ended.
```

### 5. Playground questions - exercised through Python, not the portal UI

The same command started another new conversation, with 25-second spacing
before each question:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ\ agent_client.py
```

This run submitted the three section 1 playground questions through the
documented client. It did **not** open, operate, or validate the Foundry portal,
Agent Builder, Tools configuration, auto-approval toggle, Save, or Deploy UI.
Those manual steps were not needed or executed; the existing tool setting was
left unchanged. Exit code: `0`.

#### 5.1. Startup

```text
[1/4] Loading this lab's project endpoint and existing agent name...
Selected agent: <configured-agent-name>
This client does not create an agent, upload documents, or change its knowledge connections.
Model and knowledge-retrieval calls may incur charges.
[2/4] Connecting to Foundry with Microsoft Entra authentication...
[3/4] Retrieving the existing product agent...
Connected to agent: <configured-agent-name>
[Configured MCP] <knowledge-tool>; approval setting: never
[Approval] This MCP tool runs without manual approval prompts.
[4/4] Creating a new conversation for product questions...
Conversation created: <conversation-id>
Ask about Contoso products. Use history to review this session, or quit to exit.
```

#### 5.2. Tent types

```text
You: What types of tents does Contoso offer?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Tools] Discovered 1 tools from <knowledge-tool>.
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Contoso offers several tent types in its 2026 tents catalog:

- **2-Person Backpacking Tents** — for hikers and backpackers, including:
  - **Alpine Explorer 2P**: ultralight flagship model for serious hikers/mountaineers.
  - **TrailMaster Lite 2P**: value option for recreational backpackers and casual hikers. <citation:6:0>

- **4-Person Family Tents** — for car camping and family use, including:
  - **SummitDome 4P**: popular family dome tent.
  - **MegaSpace 4P Cabin**: cabin-style tent with stand-up room and more living space. <citation:6:6>

- **6-Person Group Tents** — for larger families, groups, or extended trips, including:
  - **BaseCamp Pro 6P**: premium large-capacity tent with a 3-room design. <citation:6:2>

- **Specialty Tents** — for technical or minimalist use, including:
  - **FourSeason Alpine 2P**: mountaineering/winter tent for extreme conditions.
  - **UltraLite Solo 1P**: minimalist solo shelter for ultralight backpacking and thru-hiking. <citation:6:4>

Contoso also offers **tent accessories** such as universal footprints, premium stake kits, gear loft organizers, and seam sealer. <citation:6:8>

[Source] <knowledge-source-url-1>
```

All seven named tents and their categories match the local sample catalog.

#### 5.3. XL backpacks

```text
You: Tell me about which backpacks are available in XL.
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Contoso’s backpack guide lists **four backpack models available in XL**:

| Backpack | SKU | Capacity | Price | Sizes | Best for |
|---|---:|---:|---:|---|---|
| **TrailMaster 45L** | PACK-TM-45 | 45L | $189.99 | S, M, L, **XL** | Weekend backpacking, overnight trips, hut-to-hut hiking |
| **Alpine Trekker 50L** | PACK-AT-50 | 50L + 10L extendable collar = 60L max | $249.99 | S, M, L, **XL** | Weekend backpacking, alpine trekking, shoulder-season trips |
| **Expedition Pro 65L** | PACK-EP-65 | 65L + 15L extendable collar = 80L max | $349.99 | S, M, L, **XL** | Week-long trips, mountaineering, winter camping, international trekking |
| **Summit Master 75L** | PACK-SM-75 | 75L + 15L collar extension = 90L max | $429.99 | M, L, **XL** | Extended expeditions and high-altitude mountaineering |

A few fit notes: Contoso’s general size chart defines **X-Large as 21+ inches torso length**, while the TrailMaster 45L lists **X-Large as 21–23 inches**. The Alpine Trekker 50L uses the same torso range as the TrailMaster 45L. <citation:10:4><citation:10:0><citation:10:2>

Sources: TrailMaster 45L details <citation:10:0>, Alpine Trekker 50L details <citation:10:2>, Expedition Pro 65L details <citation:10:1>, Summit Master 75L details <citation:10:3>.

[Source] <knowledge-source-url-2>
```

The four models, prices, XL size availability, and specified fit ranges match
the local backpacks guide. One-size and S/M–M/L daypacks were not
misrepresented as explicit XL offerings.

#### 5.4. Available camping accessories

```text
You: What camping accessories are available?
[Conversation] Adding your question to the existing cloud conversation...
[Request] Asking the agent to answer or request a knowledge lookup...
[Knowledge] Completed MCP call: <knowledge-tool> / knowledge_base_retrieve

Agent:
Contoso’s **Camping Accessories & Equipment 2026** catalog includes accessories across these categories:

| Category | Available accessories | Prices |
|---|---|---:|
| **Sleeping bags** | Alpine Down -15°F, TrailRest 20°F, Summer Lite 40°F | $299.99, $129.99, $79.99 |
| **Sleeping pads** | Alpine Air Pro, FoamRest Trail | $179.99+; $44.99 |
| **Camp furniture** | TrailChair Pro, BaseCamp Comfort Chair, Camp Table Lite | $89.99, $49.99, $69.99 |
| **Cooking equipment** | Trail Chef Stove System, BaseCamp Cookset, Fuel Canisters | $149.99, $79.99, $7.99–$12.99 |
| **Lighting** | HeadLamp Pro 500, Lantern LED 600 | $49.99, $39.99 |
| **Hydration** | Water Filter Pro, Water Bottle Insulated 32oz | $79.99, $34.99 |
| **Navigation & safety** | GPS Navigator Pro, First Aid Kit - Trail, Emergency Shelter Bivy | $399.99, $49.99, $29.99 |
| **Miscellaneous camp gear** | Trekking Poles - Carbon, Portable Solar Panel, Dry Bags Set, Multi-Tool | $129.99, $99.99, $39.99, $79.99 |

A few highlights:
- The **Alpine Down -15°F** sleeping bag is a premium 800-fill down bag for winter camping and high-altitude mountaineering. <citation:14:0>
- The **Alpine Air Pro** sleeping pad is offered in Regular, Large, and X-Large sizes, with prices from **$179.99 to $219.99**. <citation:14:1>
- The **Trail Chef Stove System** is an integrated canister stove system for fast boiling, while the **BaseCamp Cookset** is a family/group cooking kit. <citation:14:4><citation:14:6>
- Lighting options include the **HeadLamp Pro 500** and **Lantern LED 600**. <citation:14:6><citation:14:5>
- Safety and utility items include a **GPS Navigator Pro**, **First Aid Kit**, **Emergency Shelter Bivy**, **Trekking Poles**, **Portable Solar Panel**, **Dry Bags Set**, and **Multi-Tool**. <citation:14:5><citation:14:3><citation:14:2>

Contoso also lists separate **tent accessories**—universal footprints, premium tent stake kit, gear loft organizer, and seam sealer—and **backpack accessories** such as rain covers, hydration bladder, pack liners, and a backpack repair kit. <citation:14:7><citation:14:9>

[Source] <knowledge-source-url-3>
[Source] <knowledge-source-url-1>
[Source] <knowledge-source-url-2>
```

The displayed category products and prices agree with the local accessory
catalog; Alpine Air Pro's `+` corresponds to its larger sizes at $199.99 and
$219.99. Three unique source URLs were displayed, once each, despite multiple
inline references.

#### 5.5. Quit

```text
You: quit
[Input] Quit requested. Ending the chat.
[Cleanup] Closing SDK clients and the Azure credential. The existing agent and cloud conversation are not deleted.
[Complete] Product-agent conversation ended.
```

### 6. Exact README offline checks

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $python = Join-Path (Get-Location) '.labenv\Scripts\python.exe'
    Push-Location .\2_Develop_AI_Agents_with_Azure\09-integrateFoundryIQ
    try {
        & $python -m unittest test_foundry_iq -v
        if ($LASTEXITCODE -ne 0) { throw 'Foundry IQ checks failed.' }
    } finally {
        Pop-Location
    }
}
```

Exit code: `0`.

```text
test_approval_rounds_return_matching_decisions_and_keep_full_history (test_foundry_iq.FoundryIQTests.test_approval_rounds_return_matching_decisions_and_keep_full_history) ... ok
test_failed_incomplete_and_empty_answers_do_not_enter_assistant_history (test_foundry_iq.FoundryIQTests.test_failed_incomplete_and_empty_answers_do_not_enter_assistant_history) ... ok
test_failed_knowledge_call_is_not_reported_as_success (test_foundry_iq.FoundryIQTests.test_failed_knowledge_call_is_not_reported_as_success) ... ok
test_history_and_quit_do_not_call_model_or_delete_existing_agent (test_foundry_iq.FoundryIQTests.test_history_and_quit_do_not_call_model_or_delete_existing_agent) ... ok
test_invalid_approval_input_is_reprompted_and_no_denies (test_foundry_iq.FoundryIQTests.test_invalid_approval_input_is_reprompted_and_no_denies) ... ok
test_invalid_arguments_and_approval_eof_are_explicit_failures (test_foundry_iq.FoundryIQTests.test_invalid_arguments_and_approval_eof_are_explicit_failures) ... ok
test_no_approval_response_does_not_ask_for_a_decision (test_foundry_iq.FoundryIQTests.test_no_approval_response_does_not_ask_for_a_decision) ... ok
test_source_deduplication_resets_each_turn_and_keeps_inline_references (test_foundry_iq.FoundryIQTests.test_source_deduplication_resets_each_turn_and_keeps_inline_references) ... ok
test_sources_and_history_display_actual_response_data (test_foundry_iq.FoundryIQTests.test_sources_and_history_display_actual_response_data) ... ok
test_sources_are_unique_across_messages_without_hiding_different_files (test_foundry_iq.FoundryIQTests.test_sources_are_unique_across_messages_without_hiding_different_files) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.027s

OK
```

These are mocked/offline behavior checks. They do not validate live permissions,
token quota, retrieval relevance, or a portal deployment.

### 7. Outcome, source verification, and cleanup

| Command/run | Exit | Observed result |
|---|---:|---|
| Conditional `.env` copy | 0 | Existing file preserved; no copy. |
| Read-only token-expiry check | 0 | Existing sign-in valid; no token printed. |
| `agent_client.py -Install` | 0 | All requirements already satisfied; setup `quit`; zero model questions. |
| First `agent_client.py` guide run | 1 | Blank input handled; three answers/lookups; fourth question hit HTTP 429. |
| Paced `agent_client.py` retry | 0 | Recommendation and contextual pricing answered; history and quit verified. |
| `agent_client.py` playground-question run | 0 | Three catalog questions answered through Python; portal UI unexecuted. |
| README `unittest` command | 0 | Ten offline tests passed in 0.027s. |

Across the three product sessions, **nine product questions were submitted**:
**eight answers** and **eight completed `knowledge_base_retrieve` calls** were
displayed; the failed recommendation attempt had neither. There were **zero
manual approval prompts/decisions**. The eight answers displayed **12 source
lines referencing three distinct URLs**. Returned source basenames were
checked against the three local sample catalogs; the URLs are not published
here and the remote documents were not downloaded or independently audited.

Selected tent ratings, backpack sizes/capacities/weights/load ranges, accessory
prices, and pricing totals were checked against the local Markdown catalogs.
Inline references and deduplicated URL annotations provide stronger evidence
than connection success alone, but do not independently validate every
generated claim or guarantee future answers.

Four test conversations were created and **left intact**, including the failed
session. SDK clients and credentials were closed; the three normal exits printed
`[Complete]`, while the failed run printed cleanup and its traceback. No
generated product file was returned, and no local output artifact was claimed.
Only this README persists from the capture; its named private transcript/helper
files were removed after verification. Existing private historical results were
not overwritten or removed.

The shared model token limit was reported for coordination. No further retries,
quota increase, resource provisioning, deployment, or automatic approval change
was attempted. All documented client questions were eventually exercised, but
the original uninterrupted five-question/history session did **not** complete:
the successful retry's history covers only its two questions. Portal setup,
configuration/deployment UI, manual approval mode, and exhaustive claim
validation remain outside this capture.
