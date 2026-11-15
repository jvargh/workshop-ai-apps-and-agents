# Lab 5 - Implement a responsible generative AI solution

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/06-Explore-content-filters.html) | [Downloaded guide](upstream-guide.md) | [Section setup](../README.md)

Content filters help screen the questions people send to a model and the answers it generates. The policy attached to a deployment determines which risk categories and severity levels the filters block. In this lab, you will find out which policy your deployment uses, send a safe test question, and optionally check a stricter custom policy.

[audit-guardrails.py](audit-guardrails.py) checks the local [policy template](guardrail-policy.json), reads your deployment's settings through Azure Resource Manager (ARM), and asks the model a safe sightseeing question. **It does not change your Azure resources.** Creating a custom policy and attaching it to a deployment are separate steps you perform in the portal.

## Table of contents

- [1\. Choose the deployment you want to check](#1-choose-the-deployment-you-want-to-check)
- [2\. Install dependencies once](#2-install-dependencies-once)
- [3\. Check the local policy file without connecting to Azure](#3-check-the-local-policy-file-without-connecting-to-azure)
- [4\. Check the current policy and ask a safe test question](#4-check-the-current-policy-and-ask-a-safe-test-question)
- [5\. Optional: set up stricter filters in the portal](#5-optional-set-up-stricter-filters-in-the-portal)
  - [Configure the controls](#configure-the-controls)
  - [Select the deployment in the assignment step](#select-the-deployment-in-the-assignment-step)
  - [Name, review, and create the guardrail](#name-review-and-create-the-guardrail)
- [6\. Check that the custom policy has the expected settings](#6-check-that-the-custom-policy-has-the-expected-settings)
- [7\. Review the result and finish the lab](#7-review-the-result-and-finish-the-lab)
- [Troubleshooting, privacy, and cleanup](#troubleshooting-privacy-and-cleanup)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [Command: dependency installation and automatic audit](#command-dependency-installation-and-automatic-audit)
    - [Prompt and captured response](#prompt-and-captured-response)
  - [Command: documented offline policy tests](#command-documented-offline-policy-tests)
  - [Command: ordinary read-only audit](#command-ordinary-read-only-audit)
    - [Prompt and captured response](#prompt-and-captured-response-1)
  - [Command: prompted strict audit of the existing custom policy](#command-prompted-strict-audit-of-the-existing-custom-policy)
    - [Interactive input and capture recovery](#interactive-input-and-capture-recovery)
    - [Automatic prompt and captured response](#automatic-prompt-and-captured-response)
  - [What these executions establish](#what-these-executions-establish)

## 1\. Choose the deployment you want to check

Run every command below in **PowerShell from the repository root**. If you already have a working `.env` for this lab, keep it. The following commands create the file only when it is missing, then sign you into Azure:

```
if (-not (Test-Path .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\.env)) {
    Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\.env.example .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\.env
}
az login
```

Open this lab's `.env` and fill in the five settings below. Make sure the endpoint, account details, and deployment name all refer to the **same Azure resource**:

| Setting | What to enter |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT` | The resource's HTTPS OpenAI v1 URL ending `/openai/v1/`, not the project `/api/projects/...` URL. |
| `MODEL_DEPLOYMENT` | The actual deployment name to audit, not just a model family name. |
| `AZURE_SUBSCRIPTION_ID` | The subscription containing that resource. |
| `AZURE_RESOURCE_GROUP` | The resource's group name. |
| `AZURE_AI_ACCOUNT_NAME` | The Foundry resource/account name, not the project name. |

You need Reader access to inspect the deployment and its policy, plus permission to call the model. If you later create or apply a custom policy, you will also need permission to change those settings. The safe test question is still a live model call and may incur inference charges.

## 2\. Install dependencies once

After configuring access, run:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py -Install
```

**The launcher installs packages and then runs the ordinary audit automatically.** It reads the current policy, sends the safe Rome question, saves a report, and exits. It does not create or attach a policy, and it does not perform strict custom-policy verification without `--expect-policy`. The model request may incur inference charges.

Wait for the command to finish. The remaining run commands reuse the installed packages and do not need `-Install`.

## 3\. Check the local policy file without connecting to Azure

Check that the supplied policy file has the settings this lab expects:

```
.\.labenv\Scripts\python.exe .\1-Develop_GenAI_Apps_with_Foundry\tests\test_foundry_labs.py GuardrailTests -v
if ($LASTEXITCODE -ne 0) { throw 'Local policy checks failed. Resolve the errors before continuing.' }
```

You should see `**Ran 4 tests**` **followed by** `**OK**`. Each of the four risk categories needs a filter for incoming questions and another for generated answers, giving eight required filters. The tests check that those filters are enabled, block at the Low threshold, and have no missing or duplicate entries. They accept `Default` or `Blocking` policy mode and reject asynchronous or unknown modes. This test command makes no Azure calls.

Passing these tests means the local file meets those checks. **It does not mean the policy has been created or applied in Azure.**

## 4\. Check the current policy and ask a safe test question

The installation command already ran the ordinary audit. This block repeats it and checks the resulting report, including another live model request. Your deployment can use a built-in or existing custom policy; you do not need to create a new one first. Copy and run the **entire block**, including `& {` and the closing `}`. This keeps the commands together: an error stops the block before it reads an old report or prints `PASS`.

```
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py
    if ($LASTEXITCODE -ne 0) { throw 'Audit failed. Do not read an older report as evidence for this run.' }

    $reportPath = '.\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\results\guardrail-audit.json'
    $audit = Get-Content -LiteralPath $reportPath -Raw -ErrorAction Stop | ConvertFrom-Json
    if (-not $audit.success -or -not $audit.assigned_policy -or -not $audit.local_strict_template_valid -or $audit.shared_settings_changed -or $audit.harmful_prompts_executed) {
        throw 'The report does not confirm a successful read-only assignment audit.'
    }
    $choice = $audit.smoke_response.choices[0]
    if ($choice.finish_reason -ne 'stop' -or [string]::IsNullOrWhiteSpace($choice.message.content)) {
        throw 'The benign model request did not complete with nonempty text.'
    }
    $audit | Select-Object deployment, assigned_policy, policy_definition_available, local_strict_template_valid, strict_guardrail_verified, shared_settings_changed, harmful_prompts_executed
    Write-Host 'PASS: current policy assignment inspected and benign inference completed.'
}
```

You do not need to type a prompt or `quit`. The script sends the following question automatically through Chat Completions, saves its report, and exits:

```
Suggest three safe daytime sightseeing activities in Rome.
```

Follow the eight numbered messages as the script runs. They show it loading your settings, checking the local file, looking up the deployment and policy, deciding whether to run strict checks, asking the model, checking its response, and saving the report. You will see the question before it is sent. The script announces completion only after it saves the report.

You should see a sightseeing answer, the saved report's location, a summary of the assigned policy, and a final `PASS` message from the PowerShell checks. The answer and policy name may differ from the recorded example.

| Report field | How to interpret it |
| --- | --- |
| `assigned_policy` | The policy name Azure reports for this deployment (`raiPolicyName`), such as `Microsoft.DefaultV2`. |
| `policy_mode` | The policy-level filtering mode returned by Azure. `Default` is compatible with individual controls set to Block; it is not the policy's name or its severity threshold. `null` means the mode was not returned or the definition was unavailable. |
| `policy_definition_available` | Whether the script could read the policy's settings. Azure may return 404 when a built-in policy is requested as an account-owned policy; the script explains that limitation. Other HTTP failures still stop the audit. |
| `local_strict_template_valid` | `true` means the local file passed its checks. It does not mean that file was applied to Azure. |
| `strict_guardrail_verified` | This stays `false` when you run without `--expect-policy`, even if the policy settings can be read. |
| `shared_settings_changed` / `harmful_prompts_executed` | Both should be `false`: the script changes no cloud settings and sends only the safe sightseeing question. |

If the script cannot read a built-in policy's settings, it cannot verify that policy's thresholds. That warning does not mean filtering is disabled. Likewise, receiving a safe answer does not show what would happen to a harmful request.

## 5\. Optional: set up stricter filters in the portal

**Use a separate lab deployment, or get its owner's approval before continuing.** Unlike the audit script, the following portal steps change the deployment's behavior.

Open [Microsoft Foundry](https://ai.azure.com), select the project/resource containing your intended deployment, and enable **New Foundry** if needed. Under **Build**, find the deployment in **Deployments** or **Models**, depending on the portal layout. Confirm its name matches `MODEL_DEPLOYMENT` in this lab's `.env`, and record its current policy assignment so you can restore it later.

Open **Build > Guardrails > Create guardrail**. The wizard separates control settings, model assignment, and review. You do not enter the deployment name on the controls page or in the **Guardrail name** field.

### Configure the controls

On **Step 1: Add controls**, configure or confirm the four **Content harms** controls below. **User input, Output** in the portal corresponds to Prompt and Completion. Each control should use **Highest blocking** and the **Block** action; leave unrelated default controls unchanged.

If your layout uses **Add controls > Risk**, select each category, set the intervention points and blocking threshold, and choose **Add control**. Confirm replacement only for the approved target.

| Category | Prompt threshold | Completion threshold |
| --- | --- | --- |
| Hate | Highest blocking / Low | Highest blocking / Low |
| Violence | Highest blocking / Low | Highest blocking / Low |
| Sexual | Highest blocking / Low | Highest blocking / Low |
| Self-harm (`Selfharm` in ARM) | Highest blocking / Low | Highest blocking / Low |

### Select the deployment in the assignment step

1.  Select **Next** to reach **Step 2: Assign agents and models** (also labelled **Select agents and models** in some layouts).
2.  Select **Add models** to open the deployment list. This is where you select the deployment; it is not another name field.
3.  Select **only** the approved deployment matching `MODEL_DEPLOYMENT`, then choose **Save** to confirm the selection.
4.  Select **Next** to reach **Step 3: Review**.

If **Add models** opens an empty list, check that you are in the project/resource containing the deployment and that it appears under **Build > Models/Deployments**. Also check your permissions: Microsoft's portal guidance requires **Foundry Account Owner** or higher on the resource for guardrail management. Do not create another deployment or change a different one just to get past an empty list.

### Name, review, and create the guardrail

On the review page, enter `**lab-strict-content-filter**` in **Guardrail name**. If that name already exists, choose a unique name such as `lab-strict-content-filter-2`; do not overwrite someone else's policy.

**Check the Models summary before creating the guardrail.** It must list the intended deployment. If it says **No models selected**, return to the assignment step, use **Add models**, select the deployment, and **Save**. A name and correctly configured controls alone do not attach the policy to a model.

Once the review lists the intended deployment and correct controls, select **Create** (or **Submit**, depending on the layout) and wait for confirmation.

Return to **Deployments > your deployment > Details** and check that the new policy is attached. Record its actual ARM policy name (`raiPolicyName`), which may differ from its display label. If you used a different account or deployment, update this lab's `.env` to match.

If you already created the guardrail with no models selected, open **Build > Guardrails**, select the guardrail, choose **Edit**, and advance from the controls page to the assignment step. Use **Add models** to select the approved deployment, confirm the selection with **Save**, and complete the review/save flow. Alternatively, open the model's playground and use **Guardrails > Manage > Assign a new guardrail** to select the existing guardrail and choose **Assign**. Both routes change the deployment's policy; use only the approved target.

See Microsoft's [guardrail creation and assignment instructions](https://learn.microsoft.com/azure/foundry/guardrails/how-to-create-guardrails) for the current portal flow.

For the script's strict checks to pass, all eight required filters must have `enabled=true`, `blocking=true`, and `severityThreshold=Low`. The policy-level mode must be `Default` or `Blocking`. Additional controls supplied by the portal do not replace these required eight checks.

**Block action and policy mode are different settings.** The portal can show Block for every harm-category control while Azure returns `mode=Default` for the policy. Default filtering still evaluates content against the configured blocking rules; it does not disable them. Keep the portal's **Streaming mode** at **Default** for this walkthrough rather than switching to asynchronous filtering. See Microsoft's [content-streaming explanation](https://learn.microsoft.com/azure/foundry/openai/concepts/content-streaming).

The Low threshold means these category filters target content classified as Low, Medium, or High severity. Safe content falls below that threshold, although other controls may still affect the request.

Before moving on, confirm that your approved deployment shows the custom policy. If it still shows the built-in policy, check that you attached the custom policy to the right deployment.

## 6\. Check that the custom policy has the expected settings

After creating and assigning the policy in step 5, run the block below. If the deployment's actual policy name (`raiPolicyName`) is `lab-strict-content-filter`, enter exactly:

```
lab-strict-content-filter
```

If you chose another name, or Azure reports a different ARM name, enter that actual assigned name instead. **There is no ready-made custom policy to enter if you have not completed step 5.** Typing a name here does not create or attach it. If you only want to inspect the existing built-in policy, use the ordinary audit in step 4 without `--expect-policy`.

Copy and run the **entire block**, including its outer braces, then enter the policy name when prompted. Do not run the final `Write-Host` separately: it is only a label and cannot verify a policy on its own.

```
& {
    $ErrorActionPreference = 'Stop'
    $policyName = (Read-Host 'Enter the applied custom ARM policy name (raiPolicyName)').Trim()
    if ([string]::IsNullOrWhiteSpace($policyName) -or $policyName -like 'Microsoft.*') {
        throw 'Enter an applied custom policy name, not a built-in policy or an empty value.'
    }
    .\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py --expect-policy $policyName
    if ($LASTEXITCODE -ne 0) { throw 'Strict audit failed. Do not use an older report as evidence.' }

    $reportPath = '.\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\results\guardrail-audit.json'
    $audit = Get-Content -LiteralPath $reportPath -Raw -ErrorAction Stop | ConvertFrom-Json
    if (-not $audit.success -or $audit.assigned_policy -ne $policyName -or -not $audit.policy_definition_available -or -not $audit.strict_guardrail_verified -or -not $audit.local_strict_template_valid -or $audit.shared_settings_changed -or $audit.harmful_prompts_executed) {
        throw 'The assigned custom strict policy was not verified.'
    }
    $choice = $audit.smoke_response.choices[0]
    if ($choice.finish_reason -ne 'stop' -or [string]::IsNullOrWhiteSpace($choice.message.content)) {
        throw 'The benign model request did not complete with nonempty text.'
    }
    $audit | Select-Object deployment, assigned_policy, policy_definition_available, strict_guardrail_verified
    Write-Host 'PASS: the applied custom policy meets the strict checks and benign inference completed.'
}
```

The script checks that your deployment uses the expected policy, reads its settings, and verifies all eight required filters. It then sends the same safe Rome question automatically. You do not need to enter any chat prompts.

You should see exit code 0, a sightseeing answer, the `PASS` message, and a summary like this. The deployment/policy values below are placeholders for your configured names:

```
PASS: the applied custom policy meets the strict checks and benign inference completed.

deployment        assigned_policy     policy_definition_available strict_guardrail_verified
----------        ---------------     --------------------------- -------------------------
<deployment-name> <custom-policy-name>                      True                      True
```

PowerShell may print `PASS` before the formatted table because it buffers table output. That order is normal; the checks run before the success message. Your deployment and policy names may differ, but both verification columns must be `True`.

If the policy name differs from the expected name, its settings cannot be read, a required filter is missing or incorrect, or the model call fails, the block stops with an error and does not print `PASS`. Resolve that error before continuing.

If Azure reports `Expected policy lab-strict-content-filter; deployment uses Microsoft.DefaultV2`, the selected deployment still uses the built-in policy. Return to step 5 and attach the custom policy to the approved deployment selected in `.env`, or use step 4 if you are not changing policies. A failed audit does not save a new report; any existing report still describes an earlier run.

Passing this step confirms the policy's settings. It still does not show a filter blocking a request.

## 7\. Review the result and finish the lab

**The successful strict audit completes this lab's configuration walkthrough. You do not need external safety-test cases to finish it.** Review what the result establishes:

| Result | What you have confirmed |
| --- | --- |
| The expected policy name is assigned | The deployment uses the custom policy you selected, not merely a local file with the same name. |
| `policy_definition_available=True` | The script read the actual policy settings from Azure. |
| `strict_guardrail_verified=True` | All eight required harm-category filters passed the enabled, blocking, and Low-threshold checks, with an accepted policy mode. |
| The safe Rome question completed | The deployment accepted this harmless request and returned an answer under the assigned policy. |

The report in `results\guardrail-audit.json` preserves those checks and the raw model response. No additional model prompts are required.

**What remains outside this lab:** a broader evaluation of whether harmful inputs or outputs are blocked consistently. The [official guide](upstream-guide.md) notes that its example prompts may produce similar answers under default and custom policies. The safe request here is deliberately not a blocking test.

If you later perform a separate safety evaluation, distinguish service filtering (`code=content_filter` for blocked input, or `finish_reason=content_filter` for blocked output, with relevant category details) from a model refusal with `finish_reason=stop`. That further evaluation is optional follow-on work, not a prerequisite for this lab's `PASS`.

## Troubleshooting, privacy, and cleanup

*   **The policy name does not match:** Check the policy attached to the deployment named in `.env`. Do not substitute `Microsoft.DefaultV2` just to make the strict check pass.
*   **The policy settings cannot be read:** A built-in policy's 404 warning is allowed for the ordinary audit. The strict audit must be able to read the custom policy; otherwise it fails.
*   **A command fails:** Stop before inspecting the report. It may still contain a previous successful run. An older `success=true` does not mean the new run passed.
*   **You cannot connect:** Check your Azure sign-in, tenant and subscription, endpoint ending `/openai/v1/`, deployment/account settings, and permissions.
*   **Keep reports private:** They contain resource and deployment details, model output, and filter annotations. Do not commit sensitive input or screenshots.
*   **Restore changes when finished:** The script creates or deletes no resources. If you changed a deployment's policy in the portal, restore its original assignment when appropriate. Remove only your own disposable lab artifacts, not shared resources.

## Validation and conclusion

| What was checked | What the results show |
| --- | --- |
| Local policy file | Four offline tests check the required strict settings and reject incorrect filter configurations. |
| Live custom-policy check | The configured deployment used the expected custom policy with `mode=Default`. All eight required filters passed the enabled, blocking, and Low-threshold checks; the safe sightseeing request completed and the report recorded `strict_guardrail_verified=true`. |
| Changes made by the script | You create and attach the custom policy in the portal. The audit only reads its settings and sends the safe request; it changes no cloud settings. |
| Actual blocking | Not tested in this walkthrough. Broader safety evaluation is separate follow-on work and is not required to complete the lab. |

**Conclusion:** The successful audit confirms the custom policy is assigned, its required settings are correct, and the deployment can answer a safe question. That completes the configuration exercise. It does not establish how every harmful request would be handled.

## Captured output

These commands used the existing lab `.env`, Azure authentication, and shared Python environment. No sign-in, provisioning, permission changes, policy creation, or policy assignment was performed. The deployment already had a custom policy assigned before these runs. `<deployment>`, `<assigned-custom-policy>`, and `<repository-root>` redact the corresponding configured identifiers and local path.

The per-run transcripts and JSON linked below preserve the captured results with identifiers redacted. README excerpts omit trailing Markdown line-break spaces; the full transcripts retain them. The pre-existing `results\guardrail-audit.json` was preserved; use the per-run files, not that older report, as evidence for these executions.

| Executed case | Exit/status | Established result |
| --- | --- | --- |
| Dependency installation and automatic audit | `0` | All packages already satisfied; no package modifications. Current custom assignment read; benign answer completed. |
| Documented `GuardrailTests` command | `0`, four tests passed | The local policy tests ran directly through the shared test file. |
| Ordinary audit and step 4 report-validation block | `0`, `PASS` | Assigned policy definition available, `mode=Default`; strict deployed-policy checks intentionally skipped. |
| Prompted strict audit and step 6 report-validation block | `0`, `PASS` | Already-assigned custom policy matched; all eight required deployed filters passed the strict settings checks. |

### Command: dependency installation and automatic audit

Direct and active transitive dependency constraints and audit imports were checked first. A `pip install --dry-run --no-index` preflight confirmed that installation required no modifications. The documented launcher was then run with index access and pip's version check disabled:

```powershell
$env:PIP_NO_INDEX = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py -Install
```

**Exit code: `0`.** Pip reported `Requirement already satisfied` for every dependency: `openai=2.54.0`, `azure-identity=1.25.3`, `python-dotenv=1.2.3`, and `requests=2.34.2` met the direct requirements. No shared packages were installed, upgraded, or removed. This command also ran the audit and sent the benign question automatically.

#### Prompt and captured response

```text
Prompt: Suggest three safe daytime sightseeing activities in Rome.
```

```text
Response finish reason: stop

Model answer:
1. **Visit the Colosseum and Roman Forum**
   Explore Rome’s most famous ancient sites during the day. Booking tickets in advance can help avoid long lines.

2. **Tour the Vatican Museums and St. Peter’s Basilica**
   Spend a daytime visit seeing the Sistine Chapel, Vatican collections, and the basilica. Go early to avoid the biggest crowds.

3. **Walk through Piazza Navona, the Pantheon, and Trevi Fountain**
   This central route is busy, scenic, and easy to do on foot during daylight hours. Keep an eye on personal belongings in crowded areas.
```

The saved report recorded `success=true`, `policy_mode="Default"`, `policy_definition_available=true`, and `strict_guardrail_verified=false`. The latter is expected without `--expect-policy`. This request used 15 prompt tokens and 157 completion tokens, 172 total.

Evidence: [full installation/audit transcript](results/captured-install-audit.txt) · [redacted installation/audit report](results/captured-install-audit.json).

### Command: documented offline policy tests

```powershell
.\.labenv\Scripts\python.exe .\1-Develop_GenAI_Apps_with_Foundry\tests\test_foundry_labs.py GuardrailTests -v
if ($LASTEXITCODE -ne 0) { throw 'Local policy checks failed. Resolve the errors before continuing.' }
```

**Exit code: `0`; four tests passed.** The documented command ran the existing
policy tests directly, without an isolated loader or Azure requests:

```text
test_all_eight_category_source_pairs (__main__.GuardrailTests.test_all_eight_category_source_pairs) ... ok
test_blocking_mode_and_unique_filters (__main__.GuardrailTests.test_blocking_mode_and_unique_filters) ... ok
test_each_filter_must_be_present (__main__.GuardrailTests.test_each_filter_must_be_present) ... ok
test_each_filter_must_block_low_severity (__main__.GuardrailTests.test_each_filter_must_block_low_severity) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.016s

OK
```

Evidence: [direct policy-test transcript](results/captured-direct-policy-tests.txt).
The local template has `mode=Blocking` and eight enabled, blocking,
Low-threshold filters. These offline tests do not establish that the template
was applied to Azure.

### Command: ordinary read-only audit

The **entire step 4 block**, including its report and response checks, was executed. Its audit command was:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py
```

**Exit code: `0`.** ARM returned the already-assigned custom policy and its definition with `mode=Default`. The script deliberately skipped deployed strict-threshold verification because `--expect-policy` was not supplied.

#### Prompt and captured response

```text
Prompt: Suggest three safe daytime sightseeing activities in Rome.
```

```text
Response finish reason: stop

Model answer:
1. **Visit the Colosseum and Roman Forum**
   Explore ancient Rome’s most famous ruins during daylight hours. Booking tickets in advance helps avoid long lines.

2. **Stroll around Piazza Navona and the Pantheon**
   This central area is lively, walkable, and full of cafés, fountains, and historic architecture.

3. **Tour Vatican City and St. Peter’s Basilica**
   Visit the Vatican Museums, Sistine Chapel, and St. Peter’s Square. Go early in the day to avoid crowds.
```

Captured report-check output:

```text
deployment                  : <deployment>
assigned_policy             : <assigned-custom-policy>
policy_definition_available : True
local_strict_template_valid : True
strict_guardrail_verified   : False
shared_settings_changed     : False
harmful_prompts_executed    : False

PASS: current policy assignment inspected and benign inference completed.
```

This request used 15 prompt tokens and 136 completion tokens, 151 total.

Evidence: [full ordinary-audit transcript](results/captured-ordinary-audit.txt) · [redacted ordinary-audit report](results/captured-ordinary-audit.json).

### Command: prompted strict audit of the existing custom policy

Because the ordinary audit established that a readable custom policy was **already assigned**, the **entire step 6 block** was executed with that actual ARM policy name. No portal creation or assignment steps were performed. The block reads the name and runs:

```powershell
$policyName = (Read-Host 'Enter the applied custom ARM policy name (raiPolicyName)').Trim()
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\05-responsible-ai-content-filters\ audit-guardrails.py --expect-policy $policyName
```

#### Interactive input and capture recovery

The first capture attempt waited for `Read-Host`, but PowerShell suppressed the prompt in redirected output. It was stopped before input was supplied or the audit started; it produced no audit result. A local capture-only wrapper then made the **same `Read-Host` prompt** visible while delegating input handling to PowerShell's original cmdlet. The bounded retry observed the prompt and only then supplied the already-assigned name:

```text
Enter the applied custom ARM policy name (raiPolicyName): <assigned-custom-policy>
```

**Retry exit code: `0`.** The actual assignment matched the supplied name, its definition was read, and `mode=Default` plus all eight enabled, blocking, Low-threshold category/source filters passed. The local template's `Blocking` mode and the deployed policy's `Default` mode are distinct accepted settings.

#### Automatic prompt and captured response

```text
Prompt: Suggest three safe daytime sightseeing activities in Rome.
```

```text
Response finish reason: stop

Model answer:
Here are three safe daytime sightseeing activities in Rome:

1. **Visit the Colosseum and Roman Forum**
   Explore ancient Rome’s most famous landmarks with a guided tour or timed-entry ticket to avoid long lines.

2. **Walk through Piazza Navona, the Pantheon, and Trevi Fountain area**
   This central route is lively during the day, full of cafés, historic architecture, and classic photo spots.

3. **Tour Vatican Museums and St. Peter’s Basilica**
   Spend the day seeing the Sistine Chapel, museum collections, and the basilica. Book tickets in advance and go early to avoid crowds.
```

Captured success message:

```text
PASS: the applied custom policy meets the strict checks and benign inference completed.
```

The strict report recorded `success=true`, `policy_definition_available=true`, `strict_guardrail_verified=true`, `local_strict_template_valid=true`, `shared_settings_changed=false`, and `harmful_prompts_executed=false`. This request used 15 prompt tokens and 151 completion tokens, 166 total.

Evidence: [full prompted strict-audit transcript](results/captured-strict-audit.txt) · [redacted strict-audit report](results/captured-strict-audit.json).

### What these executions establish

All three completed model requests used only the documented benign sightseeing question. In their actual prompt and completion filter annotations, Hate, Violence, Sexual, and Self-harm had `severity="safe"` and `filtered=false`. The additional `defender_for_ai` annotation reported `evaluation="unavailable"` with `evaluationReason="missing_or_unknown_provider_evaluation_status"`; its `detected=false` and `filtered=false` do **not** prove that Defender evaluated the request.

The strict run verified configuration of an existing applied policy, not application of the local template. No harmful-content enforcement tests were performed, no default-versus-custom policy comparison was made, and no safety policies or shared resources were changed. The documented offline command now runs all four existing policy tests directly.