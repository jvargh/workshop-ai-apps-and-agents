# Lab-z05 - Optimize generative AI model performance

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/04b-finetune-model.html) | [Downloaded guide](upstream-guide.md) | [Section setup](../README.md)

[fine-tune.py](fine-tune.py) demonstrates local training-data checks, prompt engineering, interactive travel chat, and optional comparison with an already trained deployment. **It never submits a training job or creates a deployment.** Changing instructions changes the request, not the model's trained weights.

## Install dependencies once

Run this setup command in **PowerShell from the repository root**:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\ fine-tune.py -Install
```

The launcher installs dependencies and then runs the script's default `validate` mode. Expect the local training-data checks and a saved dataset report; no Azure sign-in, model call, or training job is needed. All exercise commands below reuse the installed packages and omit `-Install`.

## 1\. Check the training file locally

Supervised fine-tuning (SFT) uses example conversations to demonstrate desired answers. This step checks the included [travel training file](data/travel-finetune-hotel.jsonl) for the required structure; it does not upload data or train a model. No Azure sign-in or model configuration is needed.

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\ fine-tune.py --mode validate
```

**Do not type any prompts.** Wait for the command to finish and return to PowerShell. Expect validation of **10 examples**, a saved `results\dataset-validation.json`, and `No training was submitted.` The checks cover encoding, message roles, nonempty content, unique user prompts, and the minimum example count, not the quality of the training answers.

## 2\. Configure access for live model calls

The remaining modes call deployed models and may incur inference charges. Create this module's `.env` only if it does not already exist, then sign in:

```
if (-not (Test-Path .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\.env)) {
    Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\.env.example .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\.env
}
az login
```

Edit the existing or newly copied `.env`:

| Setting | What to enter |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT` | Your resource's HTTPS OpenAI v1 URL ending `/openai/v1/`. |
| `MODEL_DEPLOYMENT` | An existing base chat-model deployment name. |
| `FINE_TUNED_DEPLOYMENT` | Leave unset until optional comparison. It must name a model you separately trained and deployed, accessible through the same endpoint and different from the base deployment. |

These clients use Microsoft Entra authentication. Your signed-in identity needs inference access. Do not display private configuration during a demonstration.

## 3\. Compare instructions using eight automatic prompts

This baseline shows how the same base model responds to different instructions. The script first sends three independent requests, then starts a separate five-question Rome conversation using the detailed travel instructions.

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\ fine-tune.py --mode baseline
```

**Do not type prompts or** `**quit**`**.** The script sends all eight requests below, prints their instructions and answers, saves `results\baseline.json`, and exits automatically.

| Request | Automatically sent prompt | What to review |
| --- | --- | --- |
| 1 | `What can you do?` | Generic assistant instructions: how broad is the answer? |
| 2 | `What can you do?` | Travel-focused instructions: does the answer narrow to travel? |
| 3 | `What can you do?` | Detailed instructions: does the answer describe travel support without offering hotel, flight, rental-car, or restaurant recommendations? |
| 4 | `Where in Rome should I stay?` | A new conversation starts. Look for general area advice or clarifying questions rather than specific hotel recommendations. |
| 5 | `I'm mostly there for the food. Where should I stay to be within walking distance of affordable restaurants?` | Does the answer retain Rome context while avoiding specific hotel/restaurant recommendations? |
| 6 | `What are some local delicacies I should try?` | Does it provide useful food/culture information within the permitted scope? |
| 7 | `When is the best time of year to visit in terms of the weather?` | Does it use the earlier city context to discuss seasonal conditions? |
| 8 | `What's the best way to get around the city?` | Does it discuss transportation without rental-car recommendations? |

Watch `[Prompt 1/8]` through `[Prompt 8/8]` and the `[History]` messages. The first three requests do not share context; requests 4-8 are linked through previous response IDs. Successful requests do not prove that the model followed every instruction: review the generated answers yourself.

## 4\. Try the travel assistant yourself

Interactive chat applies the detailed travel instructions to every question and links follow-ups to earlier responses. It uses the same base deployment as the baseline, not a fine-tuned model. No additional configuration is needed.

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\ fine-tune.py --mode chat
```

When `You:` appears, enter the following **one at a time inside the client, not in PowerShell**. Press Enter after each input and wait for `Assistant:` and the next `You:` prompt before continuing. You do not need to paste the travel instructions.

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | `No model request was sent.` |
| 2 | `What can you do?` | An explanation of travel support and its restrictions. |
| 3 | `Where in Rome should I stay?` | General area guidance or clarifying questions, without specific hotel recommendations. |
| 4 | `I'm mostly there for the food. Where should I stay to be within walking distance of affordable restaurants?` | A follow-up grounded in Rome, without specific hotel/restaurant recommendations. |
| 5 | `What are some local delicacies I should try?` | Food/culture information that uses the preceding city context. |
| 6 | `When is the best time of year to visit in terms of the weather?` | Seasonal advice for the same trip. |
| 7 | `What's the best way to get around the city?` | Transportation advice without rental-car recommendations. |
| 8 | `quit` | The conversation ends, `results\chat.json` is saved, and control returns to PowerShell. |

These are review goals, not guaranteed model answers. `[History]` should show the first question has no previous context and later questions reuse it. A new client session starts a new conversation; it does not reload the saved transcript.

The chat report includes your questions, answers, instructions, and token usage. A completed, nonempty session overwrites `results\chat.json` without changing the baseline report. If you quit before asking a question, no chat report is written.

## 5\. Optional: train separately, then compare deployments

**Skip this section until you have a fine-tuned deployment.** The previous steps do not create one. Dataset validation checks a file; prompt engineering and chat call the existing base model.

Follow the [official fine-tuning guide](upstream-guide.md) to choose a supported GPT-5 model/resource/region. The guide names North Central US and Sweden Central; check current availability, quota, permissions, and costs before proceeding.

In Foundry, choose supervised fine-tuning, Standard training, the included JSONL file, suffix `ft-travel`, and default hyperparameters. Review charges before submitting the training job; it can take over an hour.

Use the guide's Developer auto-deployment option, or deploy the completed model manually. Record its **deployment name**, not its training job or model ID.

Set `FINE_TUNED_DEPLOYMENT` in this module's `.env`. Both deployments must be reachable through `AZURE_OPENAI_ENDPOINT`, and their names must differ. Do not substitute an ordinary model or invent a name to bypass this prerequisite.

Run:

**Do not type prompts or** `**quit**`**.** The script validates the dataset, runs the same eight automatic prompts against the base deployment, then repeats them against the configured fine-tuned deployment: **16 billable inference requests**. It prints both sets of answers, saves `results\compare.json`, and exits.

Compare how the two deployments follow the travel instructions. The script trusts your comparison setting: it does not verify training lineage or establish improvement on unseen questions. If it reports `Configure FINE_TUNED_DEPLOYMENT in this lab's local .env`, stop and complete the training/deployment prerequisite; do not treat dataset validation as evidence of training.

## Troubleshooting and report privacy

*   `**Lab failed: ...**`**:** Read the error before retrying. Check local file errors for validation failures, or `az login`, endpoint/deployment settings, and inference permissions for live-call failures. Failed or empty responses do not count as success.
*   **Unexpected travel advice:** Review the printed instructions and `[History]` messages. Fluent text is not proof of correct context use or instruction adherence.
*   **Reports:** Files under `results` are ignored by Git but may contain private questions, model output, and deployment details. Avoid sensitive input; protect local reports. EOF also ends interactive input cleanly.
*   **Costs and cleanup:** Inference is billed even without training. Manual training and deployment have additional costs. Delete only your own disposable training/deployment artifacts, not shared resources.

## Recorded validation and limits

Earlier validation checked all **10 training examples**, completed all **eight baseline requests** against an existing GPT-5.5 deployment, and passed a live two-question chat test on 2026-11-01. The follow-up retained the city and a synthetic trip code; its transcript was saved without changing the baseline report.

That is a historical record, not a new execution of this expanded walkthrough. Offline regression tests cover data errors, request/history behavior, failed responses, chat exits, and comparison prerequisites. **No training job was submitted, no fine-tuned deployment was created, and no trained-model comparison is claimed.**

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\z05-optimize-fine-tuning\ fine-tune.py --mode compare
```