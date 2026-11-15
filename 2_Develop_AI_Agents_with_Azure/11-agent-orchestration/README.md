# Lab 11 - Sequential agent orchestration

[Agent labs](../README.md) | [Repository setup](../../README.md)

[agents.py](agents.py) runs locally in Python. Microsoft Agent Framework coordinates three local agent objects in sequence, while each agent sends a model request to the configured remote Foundry deployment. This is a local workflow, not a workflow or agent deployed to Foundry.

The **summarizer** produces one neutral sentence, the **classifier** returns Positive, Negative, or Feature request, and the **action** agent recommends one next step. The program prints the selected synthetic feedback, actual stage starts/completions, two intermediate results, and one final recommendation. No customer-support service, CRM, ticketing, messaging, or other business tool is connected.

## Table of contents

- [1. Check prerequisites and configuration](#1-check-prerequisites-and-configuration)
- [2. Install dependencies separately](#2-install-dependencies-separately)
- [3. Run the default sample](#3-run-the-default-sample)
- [4. Follow through with the other synthetic samples](#4-follow-through-with-the-other-synthetic-samples)
- [5. Errors, privacy, and cleanup](#5-errors-privacy-and-cleanup)
- [Offline regression checks](#offline-regression-checks)
- [Validation and conclusion](#validation-and-conclusion)
- [How the workflow works](#how-the-workflow-works)
- [Captured output](#captured-output)
  - [Configuration command and authentication reuse](#configuration-command-and-authentication-reuse)
  - [Dependency-install command — intentionally not executed](#dependency-install-command--intentionally-not-executed)
  - [Default positive command and selected synthetic prompt](#default-positive-command-and-selected-synthetic-prompt)
  - [Negative command and selected synthetic prompt](#negative-command-and-selected-synthetic-prompt)
  - [Feature-request command and selected synthetic prompt](#feature-request-command-and-selected-synthetic-prompt)
  - [Offline regression command](#offline-regression-command)
  - [Capture validation and cleanup](#capture-validation-and-cleanup)

## 1. Check prerequisites and configuration

Use **PowerShell from the repository root**. You need Python 3.11 or later, Azure CLI, an existing Foundry project, and a working chat-model deployment accessible to your signed-in identity. Do not create or switch cloud targets merely to make validation pass.

Keep an existing `.env`; copy the template only if it is missing:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env.example .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env
}
az login
```

Edit only the local configuration after confirming the intended target:

| Key | Value to supply |
|---|---|
| `AZURE_AI_PROJECT_ENDPOINT` | Your existing project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | `<existing-chat-model-deployment-name>`; use the deployment name, not just the model family. |

The program reads this lab's `.env` without overriding process environment variables. It rejects missing values and template placeholders before inference, and does not print configuration values. Azure authentication alone does not prove model permissions, availability, or quota.

## 2. Install dependencies separately

When setup is needed and no other lab is modifying the shared `.labenv`, run:

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py -Install
```

**The launcher installs dependencies and then starts the program.** This command immediately processes the default positive sample; it is not an install-only dry run and there is no menu to exit first. Wait for cleanup, `[Complete]`, and the PowerShell prompt. A successful sample makes three model requests and can incur charges. Do not run `-Install` concurrently with other labs.

[requirements.txt](requirements.txt) declares the compatible dependencies. Skip installation when the shared environment is already prepared; the validation below uses only non-install runs.

## 3. Run the default sample

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 failed; review the stage or cleanup error.' }
}
```

**Do not type feedback into the terminal.** There is no input prompt. With no arguments, the script selects `SAMPLES["positive"]` from [agents.py](agents.py), whose exact text is:

```text
I reached out to your customer support yesterday because I couldn't access my account. The representative responded almost immediately, was polite and professional, and fixed the issue within minutes. Honestly, it was one of the best support experiences I've ever had.
```

Follow the printed workflow in order: `[1/3] summarizer`, `[2/3] classifier`, then `[3/3] action`. Each stage must complete before the next starts. The summary should describe prompt, professional support resolving account access; the classification must be **Positive**; the recommendation should share or recognize that support praise, not claim an unresolved account problem or a completed external action.

Wait for `[Cleanup] SDK clients and credential closed` and `[Complete] 3/3 stages; 2 intermediate results; 1 final recommendation`, then check that the command exits without throwing. Output wording can vary; the relationships above, not an exact summary sentence or merely nonempty text, determine semantic success.

## 4. Follow through with the other synthetic samples

After the first run returns to the PowerShell prompt, run these commands **one at a time**, waiting for cleanup and completion after each:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py --sample negative
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 negative sample failed.' }
}
```

```text
Every time I upload a photo, the app crashes and the photo is lost. I tried three times today and could not complete a single upload.
```

The command-line selection loads the exact negative feedback shown above; do not paste it at a nonexistent prompt. Expect a summary of repeated photo-upload crashes and lost photos, exactly **Negative**, and a suggested investigation/fix for those crashes or data loss.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py --sample feature-request
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 feature-request sample failed.' }
}
```

```text
I use the dashboard every day to monitor metrics, and it works well overall. But when I'm working late at night, the bright screen is really harsh on my eyes. If you added a dark mode option, it would make the experience much more comfortable.
```

Expect a summary of the requested dashboard dark mode for nighttime comfort, exactly **Feature request**, and a recommendation to consider or backlog dark mode. The existing dashboard praise must not obscure the explicit feature request. Compare the recommendation with both printed intermediate results and the original feedback.

Each invocation creates a fresh local workflow and conversation context; samples are not continuations of one another. The only inputs are the selected entries in `SAMPLES`; no feedback file, portal-created agent, saved result file, or remote workflow artifact is used.

## 5. Errors, privacy, and cleanup

A missing configuration, invalid/empty result, provider failure, incomplete workflow, or cleanup failure prints `[Failed]` and exits **1**. An interruption exits **130**; an invalid sample argument exits **2**. The model-workflow portion is bounded to 180 seconds; a timeout fails the run rather than accepting partial stages. A printed recommendation is not a successful run unless cleanup and `[Complete]` follow it.

The program checks stage order, exact classification labels, and agreement between the two intermediate workflow outputs, the final output, and the observed stage responses. These structural checks do not independently prove factual accuracy; review the results against the synthetic input as described above.

Only synthetic feedback is supplied. The input and model output are printed and sent to the configured Foundry model; replacing the samples with real customer data would disclose that data to the model and console logs. Keep `.env` and any captured logs private and out of Git. Model calls may incur charges, and closing clients does not purge provider-side logs.

Normal exit, failures, timeout, and interruption unwind context managers for this run's OpenAI client, project client, and Azure credential. No remote agent, persisted conversation, workflow, CRM item, or ticket is created, so there is no remote resource deletion to perform. Do not delete the shared `.labenv`, Azure targets, or sign-in cache as cleanup.

If imports fail, report the exact missing/incompatible package and coordinate dependency changes with the shared-environment owner. For authentication, permissions, model, quota, or network failures, inspect the actual error and fix only the confirmed existing target; do not silently substitute another deployment or grant roles.

## Offline regression checks

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\.labenv\Scripts\python.exe -B -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\tests -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 offline checks failed.' }
}
```

The checks use real Agent Framework agents, middleware, and `SequentialBuilder` with a scripted, offline chat client. They exercise stage order, full-history propagation, intermediate/final outputs, strict labels, failed/empty responses, configuration, command-line selection, timeout, exit status, and client cleanup. The scripted responses do not prove live model quality.

## Validation and conclusion

All three documented non-install samples completed against the existing configuration with exit **0**, closing the clients and credential. Every run printed the actual order **summarizer → classifier → action**, two intermediate results, one final recommendation, cleanup, and `[Complete]`. The supplied feedback and both intermediate results were compared with each recommendation, not just checked for nonempty text.

| Sample | Observed summary | Classification | Observed final recommendation |
|---|---|---|---|
| Default positive | The customer praised the fast, professional support that quickly resolved their account access issue. | **Positive** | Share this praise with the support team to reinforce the impact of prompt, professional account access assistance. |
| `--sample negative` | The customer reports that photo uploads repeatedly crash the app, causing the photos to be lost. | **Negative** | Prioritize investigation of the photo upload crash that causes lost uploads. |
| `--sample feature-request` | The customer finds the dashboard useful but requests a dark mode to reduce eye strain at night. | **Feature request** | Recommend prioritizing a dark mode option to improve comfort for users monitoring the dashboard at night. |

All **24 offline tests passed**, exit **0**. Installed API/import checks also passed with the pinned core, Foundry, orchestration, and project SDK packages; no missing dependencies or target-access blockers were observed. `-Install` was not executed, and no shared dependencies, `.env` values, Azure targets, or root files were changed.

**Conclusion:** The local workflow produced input-supported summaries, the correct three labels, and consistent recommendations for these synthetic examples. This validates the documented path, not every future model response. Model output remains nondeterministic; no real customer data or external business mutations were tested, and no persistent test artifact was written.

## How the workflow works

`run_feedback` builds a fresh `SequentialBuilder` with the three agents. Default full-history chaining passes the original feedback and each prior assistant response downstream. `intermediate_output_from` selects summarizer/classifier responses; `output_from` selects only the action agent's terminal `AgentResponse`.

The non-streaming `report_stage` agent middleware prints at real model-call boundaries and validates each completed response before the next participant runs. `run_feedback` cross-checks the workflow's selected outputs against those observed results. `main` owns the async SDK clients and credential, while `run_cli` preserves failure status; all actions remain text recommendations.

## Captured output

Captured locally from **22:22:30 through 22:23:44, UTC−05:00**, using separate PowerShell processes from the repository root and the documented shared `.labenv` launcher. Each command below completed before the next began. These are actual stdout/stderr, not reconstructed expected answers. The newer response wording below is independent of the earlier validation table.

Privacy handling replaces configured values, local identity-bearing paths, email addresses, URLs (including signed URLs), and provider agent/conversation identifiers if present. No such replacements were needed in these successful program transcripts. UTF-8 text and line order are preserved; console line endings are normalized for Markdown. All customer feedback below is **fictional synthetic input**, not a real customer record. Each sample is a fresh workflow, not a continuation. There were no terminal input prompts or required clarifications.

Before execution, a read-only probe confirmed Python **3.13.17**, `python-dotenv` **1.2.3**, and all pinned requirements: `azure-identity==1.25.3`, `azure-ai-projects==2.3.0`, `agent-framework-core==1.12.1`, `agent-framework-foundry==1.10.3`, and `agent-framework-orchestrations==1.0.1`. Active transitive constraints and all source/test imports also passed; probe exit **0**.

### Configuration command and authentication reuse

Executed the documented conditional copy at **22:22:30**:

```powershell
if (-not (Test-Path .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env)) {
    Copy-Item .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env.example .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\.env
}
```

**Exit 0; stdout empty; stderr empty.** The existing `.env` was retained unchanged; the copy branch did not run. No configuration editor or portal step was performed.

`az login` was **not executed** because the existing Azure CLI sign-in was reused. This privacy-safe, read-only check ran instead at **22:22:30**:

```powershell
az account show --query 'user.name != null' -o tsv
```

Stdout:

```text
true
```

**Exit 0; stderr empty.** The live requests below, rather than this account-presence check alone, establish that the configured model was accessible.

### Dependency-install command — intentionally not executed

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py -Install
```

**Not executed; no exit code or captured output.** All constraints/imports were already satisfied, and other lab agents were using the shared environment concurrently. No `pip` install/uninstall/upgrade, shared environment mutation, or Foundry skill dependency auto-installer was run. The non-install default invocation below exercised the same program without package operations.

### Default positive command and selected synthetic prompt

Executed at **22:22:32**:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 failed; review the stage or cleanup error.' }
}
```

**Prompt/input:** no stdin; the default command selects `SAMPLES["positive"]`. Its exact synthetic text appears in the actual stdout:

```text
[Setup] Configuration present. Python coordinates locally; inference runs in Foundry.
[Input] Synthetic sample: positive
Customer feedback: I reached out to your customer support yesterday because I couldn't access my account. The representative responded almost immediately, was polite and professional, and fixed the issue within minutes. Honestly, it was one of the best support experiences I've ever had.
[Setup] No tools are attached. Recommendations do not change business data.
[Workflow] Local sequence: summarizer -> classifier -> action.
[1/3] summarizer: starting model call...
[1/3] summarizer: completed.
Intermediate result [summarizer]: The customer praised the fast, polite, and effective support that quickly resolved their account access issue.
[2/3] classifier: starting model call...
[2/3] Earlier results available: summarizer.
[2/3] classifier: completed.
Intermediate result [classifier]: Positive
[3/3] action: starting model call...
[3/3] Earlier results available: summarizer, classifier.
[3/3] action: completed.
Final recommendation [action]: Recognize the support team’s quick, professional account-access resolution and use it as a model for future service.
[Cleanup] Closing this run's SDK clients and credential...
[Cleanup] SDK clients and credential closed; no remote agent/workflow was created.
[Complete] 3/3 stages; 2 intermediate results; 1 final recommendation. Review meaning against the input.
```

**Exit 0; stderr empty.** The summary preserves the resolved account-access problem and support praise; **Positive** and the recommendation to recognize that service agree with the original input. No recognition was actually sent.

### Negative command and selected synthetic prompt

Executed at **22:22:55**:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py --sample negative
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 negative sample failed.' }
}
```

**Prompt/input:** no stdin; `--sample negative` selects the checked-in synthetic photo-upload feedback. Actual stdout:

```text
[Setup] Configuration present. Python coordinates locally; inference runs in Foundry.
[Input] Synthetic sample: negative
Customer feedback: Every time I upload a photo, the app crashes and the photo is lost. I tried three times today and could not complete a single upload.
[Setup] No tools are attached. Recommendations do not change business data.
[Workflow] Local sequence: summarizer -> classifier -> action.
[1/3] summarizer: starting model call...
[1/3] summarizer: completed.
Intermediate result [summarizer]: The customer reports that the app crashes during photo uploads, causing the photo to be lost and preventing successful uploads.
[2/3] classifier: starting model call...
[2/3] Earlier results available: summarizer.
[2/3] classifier: completed.
Intermediate result [classifier]: Negative
[3/3] action: starting model call...
[3/3] Earlier results available: summarizer, classifier.
[3/3] action: completed.
Final recommendation [action]: Prioritize investigating and fixing the photo upload crash to prevent lost photos and failed uploads.
[Cleanup] Closing this run's SDK clients and credential...
[Cleanup] SDK clients and credential closed; no remote agent/workflow was created.
[Complete] 3/3 stages; 2 intermediate results; 1 final recommendation. Review meaning against the input.
```

**Exit 0; stderr empty.** Repeated crashes, lost photos, **Negative**, and the suggested crash investigation/fix align. This is a recommendation only; no investigation, repair, or ticket creation was performed.

### Feature-request command and selected synthetic prompt

Executed at **22:23:16**:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\ agents.py --sample feature-request
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 feature-request sample failed.' }
}
```

**Prompt/input:** no stdin; `--sample feature-request` selects the checked-in synthetic dashboard feedback. Actual stdout:

```text
[Setup] Configuration present. Python coordinates locally; inference runs in Foundry.
[Input] Synthetic sample: feature-request
Customer feedback: I use the dashboard every day to monitor metrics, and it works well overall. But when I'm working late at night, the bright screen is really harsh on my eyes. If you added a dark mode option, it would make the experience much more comfortable.
[Setup] No tools are attached. Recommendations do not change business data.
[Workflow] Local sequence: summarizer -> classifier -> action.
[1/3] summarizer: starting model call...
[1/3] summarizer: completed.
Intermediate result [summarizer]: The customer finds the dashboard useful overall but requests a dark mode option to reduce eye strain at night.
[2/3] classifier: starting model call...
[2/3] Earlier results available: summarizer.
[2/3] classifier: completed.
Intermediate result [classifier]: Feature request
[3/3] action: starting model call...
[3/3] Earlier results available: summarizer, classifier.
[3/3] action: completed.
Final recommendation [action]: Recommend evaluating a dark mode option for the dashboard to improve comfort during nighttime use.
[Cleanup] Closing this run's SDK clients and credential...
[Cleanup] SDK clients and credential closed; no remote agent/workflow was created.
[Complete] 3/3 stages; 2 intermediate results; 1 final recommendation. Review meaning against the input.
```

**Exit 0; stderr empty.** The explicit nighttime dark-mode request is preserved despite the praise, classified **Feature request**, and reflected in the recommendation. No backlog item or product change was created.

### Offline regression command

Executed at **22:23:38**:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    .\.labenv\Scripts\python.exe -B -m unittest discover -s .\2_Develop_AI_Agents_with_Azure\11-agent-orchestration\tests -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Lab 11 offline checks failed.' }
}
```

**Exit 0; stdout empty.** Actual stderr, including the framework warnings from the scripted offline chat client:

```text
test_cli_cancellation_returns_130 (test_agents.ContractAndCliTests.test_cli_cancellation_returns_130) ... ok
test_cli_defaults_to_original_positive_sample (test_agents.ContractAndCliTests.test_cli_defaults_to_original_positive_sample) ... ok
test_cli_failure_returns_one (test_agents.ContractAndCliTests.test_cli_failure_returns_one) ... ok
test_cli_selects_feature_request (test_agents.ContractAndCliTests.test_cli_selects_feature_request) ... ok
test_cli_timeout_returns_one (test_agents.ContractAndCliTests.test_cli_timeout_returns_one) ... ok
test_configuration_reports_missing_keys_without_values (test_agents.ContractAndCliTests.test_configuration_reports_missing_keys_without_values) ... ok
test_configuration_uses_lab_env_without_overrides (test_agents.ContractAndCliTests.test_configuration_uses_lab_env_without_overrides) ... ok
test_non_response_is_rejected (test_agents.ContractAndCliTests.test_non_response_is_rejected) ... ok
test_placeholder_configuration_is_rejected (test_agents.ContractAndCliTests.test_placeholder_configuration_is_rejected) ... ok
test_unknown_sample_is_not_silently_replaced (test_agents.ContractAndCliTests.test_unknown_sample_is_not_silently_replaced) ... ok
test_user_message_is_rejected (test_agents.ContractAndCliTests.test_user_message_is_rejected) ... ok
test_valid_labels_are_accepted (test_agents.ContractAndCliTests.test_valid_labels_are_accepted) ... ok
test_cleanup_failure_cannot_report_success (test_agents.LifecycleTests.test_cleanup_failure_cannot_report_success) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_failed_model_call_still_closes_clients (test_agents.LifecycleTests.test_failed_model_call_still_closes_clients) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_success_closes_all_owned_clients (test_agents.LifecycleTests.test_success_closes_all_owned_clients) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_timeout_closes_clients_without_completion (test_agents.LifecycleTests.test_timeout_closes_clients_without_completion) ... ok
test_empty_action_is_failure (test_agents.WorkflowTests.test_empty_action_is_failure) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_empty_summary_stops_before_classifier (test_agents.WorkflowTests.test_empty_summary_stops_before_classifier) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_feature_request_is_not_generic_praise (test_agents.WorkflowTests.test_feature_request_is_not_generic_praise) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_invalid_classification_stops_before_action (test_agents.WorkflowTests.test_invalid_classification_stops_before_action) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_negative_meaning_and_context (test_agents.WorkflowTests.test_negative_meaning_and_context) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_no_outputs_is_failure (test_agents.WorkflowTests.test_no_outputs_is_failure) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_positive_order_context_and_outputs (test_agents.WorkflowTests.test_positive_order_context_and_outputs) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok
test_provider_failure_stops_workflow (test_agents.WorkflowTests.test_provider_failure_stops_workflow) ... The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
The provided chat client does not support function invoking, this might limit agent capabilities.
ok

----------------------------------------------------------------------
Ran 24 tests in 1.900s

OK
```

These warnings did not fail the offline suite and were not present on live stderr. The suite exercises real local Agent Framework orchestration with scripted responses; it is not an additional live-model evaluation.

### Capture validation and cleanup

All three live runs printed summarizer start/completion before classifier start/completion, then action start/completion, exactly two intermediate results and one final recommendation, followed by client/credential cleanup and `[Complete]`. Printed inputs exactly matched the checked-in `SAMPLES`; their summaries, labels, and recommendations were reviewed together as described above. No provider failure, missing dependency, or target-access blocker occurred.

Captured command/stream text was compared with this section after the declared sanitization and line-ending normalization; local links and Markdown fences were checked. The existing `.env`, source, requirements, and test files remained unchanged. The original README content was retained, and only this capture section was appended. Private capture harness/log files were removed after persistence and validation; no generated result file, remote agent/workflow, real business action, deployment, or shared-resource cleanup was performed.
