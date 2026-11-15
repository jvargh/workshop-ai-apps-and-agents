# 01 - Develop generative AI apps with Foundry

Six runnable companions to the Microsoft Learn Foundry labs. Each lab
contains a configuration template, dependencies, and its own run instructions.
Downloaded official guides are included where available.

| Lab | Local guide | Implementation |
|---|---|---|
| 1 - Plan and prepare | [01-plan-and-prepare](01-plan-and-prepare/) | Read-only project/deployment readiness and live inference. |
| 2 - Model catalog and evaluation | [02-model-catalog-evaluation](02-model-catalog-evaluation/) | Live two-model comparison and completed 45-question cloud evaluation validated. |
| 3 - Foundry SDK app | [03-foundry-sdk](03-foundry-sdk/) | Chat Completions, Responses, history, streaming, and asynchronous clients. |
| 4 - Chat with tools | [04-tools](04-tools/) | Responses with brochure file search, web search, conversation history, and cleanup of its own temporary resources. |
| 5 - Responsible AI | [05-responsible-ai-content-filters](05-responsible-ai-content-filters/) | Read-only policy audit and an unapplied highest-blocking policy template. |
| Lab-z05 - Optimize and fine-tune | [z05-optimize-fine-tuning](z05-optimize-fine-tuning/) | Official SFT dataset validation, live prompting baseline, interactive travel chat, and optional deployed-model comparison. Training is not submitted automatically. |

## Setup and run

Run commands from the repository root in PowerShell. Install Python and
Azure CLI, then sign in with `az login`. Copy the selected lab's
`.env.example` to `.env` and replace its placeholders. Do not overwrite an
existing working `.env`.

```powershell
Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\.env.example .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\.env
az login
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py -Install
```

The [shared launcher](../run-lab.ps1) installs dependencies only with
`-Install`. Pass the folder first and Python file separately. These labs use
the OpenAI Python SDK with Microsoft Entra authentication and refreshable
tokens, following the current lab 3 guide. They do not require a project SDK
upgrade or an API key.

### Configuration shared by the model clients

| Setting | Meaning |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | HTTPS resource **OpenAI v1** URL: `https://<resource>.openai.azure.com/openai/v1/`. Not a Foundry project URL. |
| `MODEL_DEPLOYMENT` | Your deployed model's **deployment name**, not merely its catalog model ID. |

The individual guides explain additional project, comparison, and management
settings. `DefaultAzureCredential` uses your signed-in Azure CLI identity
locally. That identity needs inference permissions, such as Cognitive Services
OpenAI User, and Reader access for ARM inventory. Cloud evaluation also needs
Foundry project evaluation permissions and available model quota.

## Validation and intentional differences

- Existing GPT-5.5 and GPT-5-mini deployments are reused; the guides' GPT-5.2
  deployment was not present. No new model deployment was created.
- Live project access, SDK modes/history, and the default assigned-policy
  audit passed. Dataset validation passed for all **10** official examples.
- The live prompt-engineering baseline completed all **eight** calls.
- The **45-question cloud evaluation completed and was validated on
  2026-11-01** using `--resume`: all 45 rows have coherence, fluency, and
  relevance scores, with 45 passed and zero failed/errored/skipped rows.
  Initial polling timed out on 2026-10-30; saved IDs allowed retrieval of the
  completed run without submitting a duplicate job.
- Portal navigation, catalog leaderboards, VS Code Foundry Toolkit UI,
  paid GPT-5 training, and custom guardrail attachment are **not** claimed as
  validated. The existing region is not the guide's fine-tuning setup.
- A benign safety prompt completing is **not** proof that harmful content is
  blocked. The default policy name is visible; its internal thresholds were
  not returned by the account-owned policy API.

Run the local regression suite without Azure calls:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\1-Develop_GenAI_Apps_with_Foundry\tests -v
```

The suite covers endpoint validation, response errors, sync/async history,
stream completion, dataset constraints, evaluation request shapes, and all
eight strict content-filter pairs.
**46 offline tests passed**, including source-checksum verification, exact
45-row/scored-metric checks, automatic resume, reset archival/fresh-job
submission, and comparison-only isolation. The normal evaluation launcher
now automatically resumes saved state and passed live with exit 0.
Run reports preserve the original Azure response JSON without triggering
the SDK's preview-field serializer warnings; genuine failures remain explicit.
Missing trained-model configuration and invalid stream/API combinations
remain explicit failures; earlier negative launcher checks returned exit 1.

Tested runtime: Python 3.13, `openai 2.54.0`, `azure-identity 1.25.3`,
`python-dotenv 1.2.3`, and `requests 2.34.2`. Existing dependencies satisfied
the new manifests; the shared project/agent SDK packages were not upgraded.

## Source, privacy, and cleanup

Official content is pinned to MicrosoftLearning/mslearn-ai-studio commit
`b702dc2fd9f9411b5eb1f86b9259db6515cd9c48`. Each `upstream-guide.md` is an
unmodified downloaded guide. Lab 3 preserves the unfinished original
starters under [upstream](03-foundry-sdk/upstream/); run our completed clients
instead. The upstream [MIT license](UPSTREAM-LICENSE.txt) is retained.
The [source manifest](SOURCE-MANIFEST.json) records each original path and
SHA-256 checksum for reproducible provenance.
The original **11** guide/code/data downloads were verified byte-for-byte against the pinned official
Git commit, not merely against their local checksums.
Lab 1's **seven screenshots** are also downloaded from that commit into
[media](media/), so its existing relative image links work in local Markdown
previews. Other guides retain upstream-relative illustration links; use
the official rendered guides for those images. Required code/data downloads
are included locally.

Actual `.env` files and all `results` folders are ignored by Git. Reports can
contain endpoints, deployment names, model output, and cloud job IDs; keep
them private. Share only sanitized configuration templates.

Inference, synthetic-data generation, judge evaluation, fine-tuning, and model
hosting incur charges. The evaluation creates persistent cloud evaluation
objects and a dataset; review saved job IDs in Foundry before starting another
run. No script here deletes resources. Do not delete a shared resource group
when following an upstream cleanup section.
