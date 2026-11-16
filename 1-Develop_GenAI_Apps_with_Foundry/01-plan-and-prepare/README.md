# Lab 1 - Plan and prepare to develop AI solutions on Azure

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/01-Explore-ai-studio.html)
| [Downloaded guide](upstream-guide.md) | [Section setup](../README.md)

## Table of contents

- [What is included](#what-is-included)
- [User steps](#user-steps)
- [Actual validation](#actual-validation)
- [Captured output](#captured-output)
  - [1. Configuration and authentication commands](#1-configuration-and-authentication-commands)
  - [2. Launcher command and dependency output](#2-launcher-command-and-dependency-output)
  - [3. Documented prompt and model output](#3-documented-prompt-and-model-output)
  - [4. Result checks and limits](#4-result-checks-and-limits)

## What is included

[verify-project.py](verify-project.py) checks an existing Foundry account,
project, and deployed model through Azure Resource Manager. It requires the
project and deployment to be `Succeeded`, then sends the guide's
three-considerations prompt to the model. It does not create resources.
Numbered progress messages explain configuration, authentication, resource
lookups, readiness checks, the live model call, and report saving. The script
shows the test prompt and model response, warns about inference charges, and
announces success only after the report is saved.

## User steps

1. Follow the official guide to create/select a Foundry project, inspect its
   resource/project/OpenAI endpoints, and deploy a chat model if needed.
   The guide uses GPT-5.2; use a model available to your subscription.
2. From the repository root:

   ```powershell
   Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\.env.example .\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\.env
   az login
   ```

3. Edit `.env`:

   | Setting | Value |
   |---|---|
   | `AZURE_OPENAI_ENDPOINT` | Resource OpenAI v1 URL, ending `/openai/v1/`. |
   | `MODEL_DEPLOYMENT` | Existing chat-model deployment name. |
   | `AZURE_SUBSCRIPTION_ID` | Subscription containing the resource. |
   | `AZURE_RESOURCE_GROUP` | Resource group name. |
   | `AZURE_AI_ACCOUNT_NAME` | Foundry resource/account name, not the project. |
   | `AZURE_PROJECT_NAME` | Project name under that account. |

4. Run:

   ```powershell
   .\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\ verify-project.py -Install
   ```

5. Review the printed answer and local `results\project-validation.json`.
   A failure exits nonzero; do not treat an endpoint configuration error as
   successful validation.
6. Complete the guide's portal and Foundry Toolkit exploration manually.

## Actual validation

The launcher passed against an existing project and GPT-5.5 deployment:
account/project inventory succeeded, provisioning was ready, and the model
returned the three requested considerations. The report explicitly records
`new_resources_created=false` and `portal_and_toolkit_ui_validated=false`.

Permissions: Reader on the resource/project plus model inference access.
Resource creation, portal UI, and Toolkit UI were not exercised. Preserve
shared resources during cleanup.

## Captured output

The command below was run from the repository root against the existing
configured resource, project, and chat-model deployment. It exited with code
`0`, printed a nonempty model answer, and saved its report. Standard error was
empty. One live inference request was made; no Azure resources were created,
deployed, reconfigured, or deleted.

The [complete console transcript](results/project-validation-captured.txt)
preserves the dependency output and all eight validation stages. The
[sanitized report](results/project-validation-captured.json) preserves the
response and usage. The absolute repository path and configured deployment
name are replaced with placeholders; other identifying configuration values
are withheld, and the report's `recorded_at` metadata is omitted. Line endings
are normalized to LF; answer wording and numerical results are unchanged.
The pre-existing `results\project-validation.json` was restored byte-for-byte
after retaining this run separately, so it is not the report for this capture.
Model wording may differ on another run.

### 1. Configuration and authentication commands

The working `.env` was preserved: the unconditional `Copy-Item` in step 2 was
not rerun because it would overwrite the existing configuration. All six
required settings were present, and the resource endpoint had the expected
HTTPS `/openai/v1/` shape. No setting values or credentials are displayed.

Azure authentication was already valid, so `az login` was not rerun. These
read-only commands acquired management-plane and inference tokens while
printing only their token type:

```powershell
az account get-access-token --resource https://management.azure.com/ --query tokenType --output tsv
az account get-access-token --resource https://ai.azure.com --query tokenType --output tsv
```

Each command exited with code `0` and returned:

```text
Bearer
```

### 2. Launcher command and dependency output

All four direct dependency constraints and runtime imports were checked
before starting. `pip check` returned `No broken requirements found.` A
read-only `pip install --dry-run --no-index` check resolved the complete
dependency set with an empty installation plan. The documented launcher
command was then run with process-local `PIP_NO_INDEX=1`,
`PIP_DISABLE_PIP_VERSION_CHECK=1`, and `PIP_NO_CACHE_DIR=1`; no packages were
installed, upgraded, or uninstalled, and no shared environment settings were
changed.

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\ verify-project.py -Install
```

The direct-dependency lines were:

```text
Requirement already satisfied: openai<3,>=2.54.0 in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\requirements.txt (line 1)) (2.54.0)
Requirement already satisfied: azure-identity<2,>=1.25.0 in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: python-dotenv<2,>=1.2.0 in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\requirements.txt (line 3)) (1.2.3)
Requirement already satisfied: requests<3,>=2.32.0 in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\requirements.txt (line 4)) (2.34.2)
```

Every transitive requirement also printed `Requirement already satisfied`;
those lines are retained in the complete transcript rather than repeated
here. `-Install` continues directly into validation and inference: it is not
an installation-only command.

### 3. Documented prompt and model output

Run [verify-project.py](verify-project.py) from the repository root with:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\ verify-project.py
```

`verify-project.py` sends this guide prompt automatically; there is no stdin
prompt and nothing to enter at the PowerShell prompt:

```text
Describe three key considerations for working with Large Language Models for AI application development.
```

It uses these instructions:

```text
You are an AI assistant that provides advice about AI software development.
```

After the dependency check, the actual console output was:

```text
Foundry project validation: checking existing resources only.
No Azure resources will be created or changed.

[1/8] Loading configuration from this lab's .env file...
Selected model deployment: <model-deployment>

[2/8] Preparing Azure authentication with DefaultAzureCredential...

[3/8] Reading Foundry resource details from Azure Resource Manager...
Resource region: westus3

[4/8] Reading the Foundry project's provisioning status...
Project provisioning state: Succeeded

[5/8] Listing the resource's model deployments...
Found 4 model deployment(s).

[6/8] Checking that the project and selected deployment are ready...
Project and selected deployment are both Succeeded.

[7/8] Testing the deployed model with a live inference request...
This model call may incur inference charges.
Prompt: Describe three key considerations for working with Large Language Models for AI application development.
Sending the prompt using the Responses API. Waiting for the model response...

Model response:
Here are three key considerations when working with Large Language Models for AI application development:

1. **Prompting, context, and model behavior**
   - LLMs are sensitive to how instructions are written and what context they receive.
   - Good application design often requires careful prompt engineering, structured inputs, examples, and clear output formats.
   - You should also account for limitations such as hallucinations, ambiguity, and inconsistent responses.

2. **Evaluation, reliability, and safety**
   - LLM outputs should be tested against real use cases, not just simple examples.
   - Important evaluation criteria include accuracy, consistency, relevance, toxicity, bias, and robustness to unusual inputs.
   - For production systems, use safeguards such as validation layers, moderation, human review, fallback behavior, and retrieval from trusted sources.

3. **Cost, latency, and scalability**
   - Larger models often produce better results but can be slower and more expensive.
   - Developers need to balance model quality with response time, token usage, API cost, and infrastructure requirements.
   - Techniques such as caching, prompt compression, smaller specialized models, batching, and retrieval-augmented generation can help optimize performance and cost.

[8/8] Saving the validation results to a local JSON report...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\01-plan-and-prepare\results\project-validation.json

Validation completed successfully.
Portal navigation and the VS Code Foundry Toolkit UI were not validated.
```

### 4. Result checks and limits

The saved response matched the printed answer exactly after the declared
sanitization. It contains the three requested considerations: prompting and
context, evaluation and safety, and cost and scalability. The script requires
a completed, nonempty Responses API result before reporting success.

The report identifies the underlying public model as `gpt-5.5` and records
`project_state="Succeeded"`, `success=true`, `input_tokens=38`,
`output_tokens=297`, and `total_tokens=335`. The output-token detail includes
`reasoning_tokens=51`. Its scope flags are `new_resources_created=false` and
`portal_and_toolkit_ui_validated=false`.

Resource/project/deployment readiness and the live model answer were
verified; portal navigation and the Foundry Toolkit playground remain
manual exercises. The guide's resource creation, model deployment, extension
installation, and resource-group deletion were not repeated against shared
resources. There were no cloud-prerequisite failures in this run.

