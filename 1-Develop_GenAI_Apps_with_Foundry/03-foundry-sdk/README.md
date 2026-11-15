# Lab 3 - Develop an AI app with the Microsoft Foundry SDK

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/03-foundry-sdk.html) | [Downloaded guide](upstream-guide.md) | [Section setup](../README.md)

The current guide uses the **OpenAI Python SDK** against Foundry-hosted models. These completed clients follow that API approach; an `AIProjectClient` is not required. Original incomplete Microsoft starters are preserved under [upstream](upstream/) for reference, not execution.

## Table of contents

- [Configure](#configure)
- [Install dependencies once](#install-dependencies-once)
- [Test chat APIs, conversation history, and response delivery](#test-chat-apis-conversation-history-and-response-delivery)
  - [1\. Chat Completions with history](#1-chat-completions-with-history)
  - [2\. Responses without history](#2-responses-without-history)
  - [3\. Responses with history (the default)](#3-responses-with-history-the-default)
  - [4\. Responses with streamed text and history](#4-responses-with-streamed-text-and-history)
  - [5\. Async Responses with history](#5-async-responses-with-history)
- [Optional practice](#optional-practice)
- [Troubleshooting](#troubleshooting)
- [Recorded validation and limits](#recorded-validation-and-limits)
- [Captured output](#captured-output)
  - [Dependency setup command](#dependency-setup-command)
    - [Setup input: quit](#setup-input-quit)
  - [Exercise 1 command: Chat Completions with history](#exercise-1-command-chat-completions-with-history)
    - [Exercise 1 input: blank](#exercise-1-input-blank)
    - [Exercise 1 prompt: remember the codeword](#exercise-1-prompt-remember-the-codeword)
    - [Exercise 1 prompt: recall the codeword](#exercise-1-prompt-recall-the-codeword)
    - [Exercise 1 input: quit](#exercise-1-input-quit)
  - [Exercise 2 command: Responses without history](#exercise-2-command-responses-without-history)
    - [Exercise 2 input: blank](#exercise-2-input-blank)
    - [Exercise 2 prompt: remember the codeword](#exercise-2-prompt-remember-the-codeword)
    - [Exercise 2 prompt: recall the codeword](#exercise-2-prompt-recall-the-codeword)
    - [Exercise 2 input: quit](#exercise-2-input-quit)
  - [Exercise 3 command: Responses with history](#exercise-3-command-responses-with-history)
    - [Exercise 3 input: blank](#exercise-3-input-blank)
    - [Exercise 3 prompt: remember the codeword](#exercise-3-prompt-remember-the-codeword)
    - [Exercise 3 prompt: recall the codeword](#exercise-3-prompt-recall-the-codeword)
    - [Exercise 3 input: quit](#exercise-3-input-quit)
  - [Exercise 4 command: streamed Responses with history](#exercise-4-command-streamed-responses-with-history)
    - [Exercise 4 input: blank](#exercise-4-input-blank)
    - [Exercise 4 prompt: remember the codeword](#exercise-4-prompt-remember-the-codeword)
    - [Exercise 4 prompt: three numbered points](#exercise-4-prompt-three-numbered-points)
    - [Exercise 4 prompt: recall after the additional turn](#exercise-4-prompt-recall-after-the-additional-turn)
    - [Exercise 4 input: quit](#exercise-4-input-quit)
  - [Exercise 5 command: async Responses with history](#exercise-5-command-async-responses-with-history)
    - [Exercise 5 input: blank](#exercise-5-input-blank)
    - [Exercise 5 prompt: remember the codeword](#exercise-5-prompt-remember-the-codeword)
    - [Exercise 5 prompt: recall the codeword](#exercise-5-prompt-recall-the-codeword)
    - [Exercise 5 input: quit](#exercise-5-input-quit)
  - [Optional ELIZA command and prompts](#optional-eliza-command-and-prompts)
    - [ELIZA first prompt](#eliza-first-prompt)
    - [ELIZA follow-up prompt](#eliza-follow-up-prompt)
    - [ELIZA input: quit](#eliza-input-quit)
  - [Optional travel command and prompts](#optional-travel-command-and-prompts)
    - [Travel first prompt](#travel-first-prompt)
    - [Travel follow-up prompt](#travel-follow-up-prompt)
    - [Travel input: quit](#travel-input-quit)
  - [Optional Python command and prompts](#optional-python-command-and-prompts)
    - [Python first prompt](#python-first-prompt)
    - [Python follow-up prompt](#python-follow-up-prompt)
    - [Python input: quit](#python-input-quit)
  - [EOF commands: sync and async cleanup](#eof-commands-sync-and-async-cleanup)
    - [Sync EOF command and output](#sync-eof-command-and-output)
    - [Async EOF command and output](#async-eof-command-and-output)
  - [SDK regression checks and discovery limitation](#sdk-regression-checks-and-discovery-limitation)

## Configure

Run from the repository root:

```
Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\.env.example .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\.env
az login
```

Set `AZURE_OPENAI_ENDPOINT` to the resource's HTTPS `/openai/v1/` URL and `MODEL_DEPLOYMENT` to your chat deployment name. No API version or resource key is required for these v1 clients. The signed-in identity needs inference access. Do not supply the `/api/projects/...` URL here.

## Install dependencies once

Run this setup command separately in **PowerShell from the repository root**:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py -Install
```

**This command installs dependencies and then opens the default Responses chat client; it is not install-only.** When `Enter a prompt (or type "quit" to exit):` appears, type `quit` and press Enter. Wait for `[Exit] Chat session closed.` and the PowerShell prompt before starting exercise 1. No model request is sent if you only enter `quit`.

The five exercise commands below reuse the installed environment and do not include `-Install`.

## Test chat APIs, conversation history, and response delivery

Your application can call a model through two API interfaces: **Chat Completions**, which takes a list of conversation messages, and **Responses**, which can link a new prompt to an earlier response. These five exercises use the same configured model deployment to explore those interfaces, conversation context, and different ways to receive answers.

Here, **history** means making earlier conversation turns available when you send a follow-up. It does not retrain the model or automatically carry context into a new client session.

Complete the configuration and installation above, then follow these exercises **in order**. Run each launch command in **PowerShell from the repository root**. Once `Enter a prompt (or type "quit" to exit):` appears, enter the table's inputs **one at a time in the running client**, not as PowerShell commands. Press Enter after each input and wait for the answer before entering the next one.

Type `quit` at the end of each exercise and wait for `[Exit] Chat session closed.` and the PowerShell prompt before launching the next exercise. Each nonblank prompt except `quit` sends a live model request and may incur inference charges.

The codeword below is synthetic, not a credential. Expected model answers are checks to look for, not guaranteed wording from every model. Progress messages appear around the answers; inspect the text under `[Response]`.

### 1\. Chat Completions with history

In this mode, your application keeps a list of user messages and model replies, then sends that list with each new prompt. The follow-up therefore includes the earlier codeword exchange. This shows how an application supplies conversation context explicitly.

Launch:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --api chat-completions
```

At each client prompt, do the following:

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | `Please enter a prompt. No model request was sent.` |
| 2 | `Remember the codeword SAPPHIRE-42. Reply with only ACK.` | The model answers `ACK`. |
| 3 | `What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.` | The model answers `SAPPHIRE-42`. The history message includes two earlier user/assistant messages. |
| 4 | `quit` | Cleanup messages appear and control returns to PowerShell. |

### 2\. Responses without history

Here, the client sends each prompt as a separate Responses API request without linking it to earlier replies. The model receives no codeword in the follow-up, even though it acknowledged the first prompt. Use this exercise to see what happens when conversation context is not supplied.

Launch a new session:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --no-history
```

Repeat the same inputs to see what changes when earlier turns are excluded:

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | No model request is sent. |
| 2 | `Remember the codeword SAPPHIRE-42. Reply with only ACK.` | The model answers `ACK`. |
| 3 | `What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.` | The model answers `UNKNOWN`; `[History]` says earlier conversation turns are excluded. |
| 4 | `quit` | The session closes and control returns to PowerShell. |

### 3\. Responses with history (the default)

This mode also uses the Responses API, but the client includes `previous_response_id` to link each follow-up to the preceding response. The service can then use that conversation context without your application resending the earlier messages. Compare the codeword answer with exercise 2.

Launch a new session without flags:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

Enter:

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | No model request is sent. |
| 2 | `Remember the codeword SAPPHIRE-42. Reply with only ACK.` | The model answers `ACK`. |
| 3 | `What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.` | The model answers `SAPPHIRE-42`; `[History]` says the previous response context is reused. |
| 4 | `quit` | The session closes and control returns to PowerShell. |

### 4\. Responses with streamed text and history

Streaming changes when you see the answer, not how conversation history is supplied. This mode keeps the previous-response link but prints text chunks as they arrive, instead of waiting for the entire answer before displaying it.

Launch:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --stream
```

Enter the following. The longer second prompt makes streaming easier to observe:

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | No model request is sent. |
| 2 | `Remember the codeword SAPPHIRE-42. Reply with only ACK.` | The model answers `ACK`, followed by `Stream completed and text validated.` |
| 3 | `Explain how a language model generates text in three numbered points.` | Three explanatory points appear under `[Response] Streaming model answer:` as text chunks arrive. |
| 4 | `What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.` | The model answers `SAPPHIRE-42`, showing context is still available after another turn. |
| 5 | `quit` | The session closes and control returns to PowerShell. |

Wait for the stream-completion message and the next input prompt before continuing. Short answers may appear all at once; streaming does not guarantee a visible word-by-word typing effect.

### 5\. Async Responses with history

Async means the model request is awaited, allowing Python to run other asynchronous tasks while the service responds. This example still reads one prompt at a time, waits for a full answer, and keeps previous-response history; it does not stream text or submit concurrent prompts.

Launch:

```
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-async.py
```

Enter:

| Step | Input or action | What to look for |
| --- | --- | --- |
| 1 | Press Enter without typing anything. | No model request is sent. |
| 2 | `Remember the codeword SAPPHIRE-42. Reply with only ACK.` | The model answers `ACK` after the async request completes. |
| 3 | `What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.` | The model answers `SAPPHIRE-42`; the previous response context is reused. |
| 4 | `quit` | `[Cleanup]` announces async client/credential cleanup, then `[Exit] Chat session closed.` appears. |

The required walkthrough ends here. The examples below are [optional practice](#optional-practice); use [troubleshooting](#troubleshooting) if a run does not behave as expected.

## Optional practice

To try a more realistic conversation, relaunch a history-enabled mode from exercise 1, 3, 4, or 5. Choose one pair below, enter the first prompt, wait for the answer, then enter the follow-up. Type `quit` when finished.

| Topic | First prompt | Follow-up prompt |
| --- | --- | --- |
| ELIZA / lab walkthrough | `Tell me about ELIZA, one of the earliest chatbots.` | `How does it compare to modern LLMs?` |
| Travel planning | `Suggest a three-day sightseeing itinerary for Rome.` | `Adapt it for a family with young children.` |
| Python coding | `Show a Python function that counts words in a string.` | `Add tests for empty strings and repeated spaces.` |

These examples have no fixed expected wording. Check whether the follow-up builds on the first answer, then assess whether the advice or code is useful and correct.

## Troubleshooting

- **Unexpected codeword answer:** Check the selected mode and `[History]` messages, then repeat that exercise in a fresh session. A fluent answer alone does not prove that earlier context was used.
- **`Lab failed: ...`:** Read the error before retrying. For authentication or access errors, check `az login`, the configured endpoint and deployment, and your identity's inference permissions. Failed, incomplete, empty, or truncated responses are errors, not successful answers.
- **Streaming appears all at once:** Short replies may arrive in one chunk. Try the longer prompt in exercise 4 and wait for the stream-completion message.
- **Ending a session:** Type `quit` or send EOF. On normal exit, `[Cleanup]` and `[Exit]` show resource cleanup and session closure. Neither client automatically saves a chat transcript.

## Recorded validation and limits

An earlier live validation passed all five modes against an existing GPT-5.5 deployment. Each run tested blank input, two turns, and quit. History-enabled modes retained the synthetic codeword; no-history returned `UNKNOWN`. Private evidence is recorded in `results\live-client-validation.json`.

That record is not a new execution of this expanded walkthrough; exercise 4 now includes an additional turn. Offline regression tests cover request shapes, history handling, stream completion, errors, and async cleanup. Neither the live record nor those tests validate the portal/VS Code Toolkit UI or establish answer quality for an application.

## Captured output

The commands below ran through the unchanged Windows launcher and shared `.labenv`. Existing `.env` configuration and the authenticated Azure session were reused; `Copy-Item` and `az login` were not rerun, avoiding configuration replacement or account changes.

Each exercise and optional prompt pair used a separate process. Inputs were supplied only when the client displayed its prompt, with each response completed before the next input. Fenced blocks are exact output excerpts, with deployment names replaced by `[redacted]` and local identifying paths by `[repository]` or `[user-profile]`. [Complete transcripts](results/captured-sdk-output.json) retain all stdout, echoed inputs, commands, and exit codes; [validation results](results/captured-sdk-checks.json) retain the checks and test-discovery failure. Optional model answers are recorded output, not independently verified historical or travel advice.

All 11 launcher sessions exited **0** and printed `[Exit] Chat session closed.` The five exercises produced **11** completed answers, including **three** validated streams. Optional practice produced **six** more answers. Blank input, quit, and EOF produced no model requests. No final model errors or fresh-session retries were needed.

### Dependency setup command

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py -Install
```

Direct requirement versions and imports passed preflight. A `pip install --dry-run --no-index` check found every direct and transitive requirement already satisfied. The documented launcher then ran with process-local `PIP_NO_INDEX=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1`; no packages were installed, upgraded, or removed. The complete dependency output is in the transcript artifact.

```text
Requirement already satisfied: openai<3,>=2.54.0 in .\.labenv\Lib\site-packages (from -r [repository]\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\requirements.txt (line 1)) (2.54.0)
Requirement already satisfied: azure-identity<2,>=1.25.0 in .\.labenv\Lib\site-packages (from -r [repository]\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: python-dotenv<2,>=1.2.0 in .\.labenv\Lib\site-packages (from -r [repository]\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\requirements.txt (line 3)) (1.2.3)
Requirement already satisfied: requests<3,>=2.32.0 in .\.labenv\Lib\site-packages (from -r [repository]\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\requirements.txt (line 4)) (2.34.2)
```

#### Setup input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; model requests: **0**.

### Exercise 1 command: Chat Completions with history

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --api chat-completions
```

```text
[Mode] Chat Completions API; output: full response.
Selected deployment: [redacted]
[History] Enabled: earlier user and assistant messages are sent with each follow-up.
```

#### Exercise 1 input: blank

```text
Please enter a prompt. No model request was sent.
```

#### Exercise 1 prompt: remember the codeword

```text
Enter a prompt (or type "quit" to exit): Remember the codeword SAPPHIRE-42. Reply with only ACK.
[History] Including 0 earlier user/assistant message(s) with this prompt.
[Request] Sending prompt using Chat Completions. Waiting for the complete response...

[Response] Model answer:
ACK
[History] Context updated for the next prompt in this session.
```

#### Exercise 1 prompt: recall the codeword

```text
Enter a prompt (or type "quit" to exit): What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.
[History] Including 2 earlier user/assistant message(s) with this prompt.
[Request] Sending prompt using Chat Completions. Waiting for the complete response...

[Response] Model answer:
SAPPHIRE-42
[History] Context updated for the next prompt in this session.
```

#### Exercise 1 input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**. The follow-up explicitly included two earlier user/assistant messages.

### Exercise 2 command: Responses without history

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --no-history
```

```text
[Mode] Responses API; output: full response.
Selected deployment: [redacted]
[History] Disabled: each prompt is an independent request.
```

#### Exercise 2 input: blank

```text
Please enter a prompt. No model request was sent.
```

#### Exercise 2 prompt: remember the codeword

```text
Enter a prompt (or type "quit" to exit): Remember the codeword SAPPHIRE-42. Reply with only ACK.
[History] Sending this prompt without earlier conversation turns.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
ACK
[History] The next prompt will be independent of this turn.
```

#### Exercise 2 prompt: recall the codeword

```text
Enter a prompt (or type "quit" to exit): What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.
[History] Sending this prompt without earlier conversation turns.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
UNKNOWN
[History] The next prompt will be independent of this turn.
```

#### Exercise 2 input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**. Acknowledging the codeword did not give the independent follow-up access to it.

### Exercise 3 command: Responses with history

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

```text
[Mode] Responses API; output: full response.
Selected deployment: [redacted]
[History] Enabled: follow-ups reference the previous response ID.
```

#### Exercise 3 input: blank

```text
Please enter a prompt. No model request was sent.
```

#### Exercise 3 prompt: remember the codeword

```text
Enter a prompt (or type "quit" to exit): Remember the codeword SAPPHIRE-42. Reply with only ACK.
[History] First turn: no previous response context.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
ACK
[History] Context updated for the next prompt in this session.
```

#### Exercise 3 prompt: recall the codeword

```text
Enter a prompt (or type "quit" to exit): What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
SAPPHIRE-42
[History] Context updated for the next prompt in this session.
```

#### Exercise 3 input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**. Unlike exercise 2, the follow-up reused the preceding response context.

### Exercise 4 command: streamed Responses with history

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py --stream
```

```text
[Mode] Responses API; output: streamed text.
Selected deployment: [redacted]
[History] Enabled: follow-ups reference the previous response ID.
```

#### Exercise 4 input: blank

```text
Please enter a prompt. No model request was sent.
```

#### Exercise 4 prompt: remember the codeword

```text
Enter a prompt (or type "quit" to exit): Remember the codeword SAPPHIRE-42. Reply with only ACK.
[History] First turn: no previous response context.
[Request] Sending prompt using Responses. Waiting for streamed output...

[Response] Streaming model answer:
ACK
[Response] Stream completed and text validated.
[History] Context updated for the next prompt in this session.
```

#### Exercise 4 prompt: three numbered points

```text
Enter a prompt (or type "quit" to exit): Explain how a language model generates text in three numbered points.
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for streamed output...

[Response] Streaming model answer:
1. A language model takes the input text and converts it into tokens, which are small pieces of text such as words, parts of words, or punctuation.

2. It predicts the most likely next token based on patterns learned from large amounts of training text and the context provided in the prompt.

3. It repeats this process token by token, using each newly generated token as part of the context, until it completes the response or reaches a stopping point.
[Response] Stream completed and text validated.
[History] Context updated for the next prompt in this session.
```

#### Exercise 4 prompt: recall after the additional turn

```text
Enter a prompt (or type "quit" to exit): What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for streamed output...

[Response] Streaming model answer:
SAPPHIRE-42
[Response] Stream completed and text validated.
[History] Context updated for the next prompt in this session.
```

#### Exercise 4 input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed streams: **3**. The capture preserves text printed while the stream was read, followed by each completion/validation marker. It does not measure service chunk boundaries or claim a word-by-word display rate.

### Exercise 5 command: async Responses with history

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-async.py
```

```text
[Mode] Async Responses API; output: full response.
Selected deployment: [redacted]
[History] Enabled: follow-ups reference the previous response ID.
```

#### Exercise 5 input: blank

```text
Please enter a prompt. No model request was sent.
```

#### Exercise 5 prompt: remember the codeword

```text
Enter a prompt (or type "quit" to exit): Remember the codeword SAPPHIRE-42. Reply with only ACK.
[History] First turn: no previous response context.
[Request] Sending prompt using async Responses. Waiting for the complete response...

[Response] Model answer:
ACK
[History] Context updated for the next prompt in this session.
```

#### Exercise 5 prompt: recall the codeword

```text
Enter a prompt (or type "quit" to exit): What codeword did I give you? Reply with only that codeword, or UNKNOWN if none was supplied.
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using async Responses. Waiting for the complete response...

[Response] Model answer:
SAPPHIRE-42
[History] Context updated for the next prompt in this session.
```

#### Exercise 5 input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the async model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**, sequentially awaited rather than streamed or submitted concurrently.

### Optional ELIZA command and prompts

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

A fresh default Responses/history session was used. The following are excerpts; the complete two answers are in transcript entry `practice-eliza`.

#### ELIZA first prompt

Input: `Tell me about ELIZA, one of the earliest chatbots.`

```text
[Response] Model answer:
ELIZA was one of the earliest and most famous chatbots in computing history. It was created in the mid-1960s by Joseph Weizenbaum, a computer scientist at MIT.

ELIZA was designed to simulate conversation by using pattern matching and scripted responses rather than real understanding. The most famous version of ELIZA was called **DOCTOR**, which imitated a Rogerian psychotherapist. This style of therapy was useful for a chatbot because it often reflects the user’s statements back as questions.
```

#### ELIZA follow-up prompt

Input: `How does it compare to modern LLMs?`

```text
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
ELIZA and modern large language models (LLMs) are both conversational systems, but they are fundamentally different in how they work and what they can do.

| Feature | ELIZA | Modern LLMs |
|---|---|---|
| Era | 1960s | 2010s–2020s |
| Core method | Hand-written pattern matching | Neural networks trained on massive text datasets |
```

The follow-up compared ELIZA with LLMs without the second prompt naming ELIZA again.

#### ELIZA input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**.

### Optional travel command and prompts

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

A separate fresh default Responses/history session was used. The following are excerpts; the complete itineraries are in transcript entry `practice-travel`.

#### Travel first prompt

Input: `Suggest a three-day sightseeing itinerary for Rome.`

```text
[Response] Model answer:
Here’s a balanced **three-day Rome sightseeing itinerary** covering ancient landmarks, major churches, museums, neighborhoods, and food-friendly areas.

## Day 1: Ancient Rome & Historic Center

**Morning**
- **Colosseum** – Book tickets in advance, ideally with access to the arena floor or underground.
- **Roman Forum** – Explore the ruins of temples, basilicas, and ancient government buildings.
- **Palatine Hill** – Great views over the Forum and Circus Maximus.
```

#### Travel follow-up prompt

Input: `Adapt it for a family with young children.`

```text
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
Here’s a more **family-friendly three-day Rome itinerary** for traveling with young children—slower paced, with shorter sightseeing blocks, outdoor time, snacks, and easy breaks.

## General Tips for Rome with Young Kids

- **Start early**, then plan a rest after lunch.
- Keep museum visits short: 1–2 hours max.
- Bring a **light stroller** or carrier; cobblestones and stairs can be tricky.
```

The follow-up retained Rome and the three-day structure while adapting the pace for children.

#### Travel input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; completed answers: **2**.

### Optional Python command and prompts

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

A third fresh default Responses/history session was used. Both complete model answers are shown below.

#### Python first prompt

Input: `Show a Python function that counts words in a string.`

````text
[Response] Model answer:
```python
def count_words(text: str) -> int:
    return len(text.split())
```

Example:

```python
sentence = "Hello world, this is Python."
print(count_words(sentence))  # 5
```

`split()` separates the string by whitespace, and `len()` counts the resulting words.
[History] Context updated for the next prompt in this session.
````

#### Python follow-up prompt

Input: `Add tests for empty strings and repeated spaces.`

````text
[History] Reusing the previous response context for this follow-up.
[Request] Sending prompt using Responses. Waiting for the complete response...

[Response] Model answer:
```python
def count_words(text: str) -> int:
    return len(text.split())


# Tests
assert count_words("") == 0
assert count_words("   ") == 0
assert count_words("hello") == 1
assert count_words("hello world") == 2
assert count_words("hello   world") == 2
assert count_words("  hello   world  ") == 2

print("All tests passed.")
```
[History] Context updated for the next prompt in this session.
````

The returned follow-up snippet was also executed unchanged in `.labenv`; all six assertions passed, exit code **0**, with actual stdout:

```text
All tests passed.
```

#### Python input: quit

```text
Enter a prompt (or type "quit" to exit): quit
[Input] Quit requested. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Launcher exit code: **0**; completed model answers: **2**. This is a whitespace-based word count, not a linguistic tokenizer.

### EOF commands: sync and async cleanup

Both clients were launched in additional fresh sessions. Their stdin was closed when the first input prompt appeared; no literal `EOF` prompt was sent.

#### Sync EOF command and output

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-app.py
```

```text
[Input] End of input received. Ending the chat session.
[Cleanup] Closing the model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; model requests: **0**.

#### Async EOF command and output

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\03-foundry-sdk\ chat-async.py
```

```text
[Input] End of input received. Ending the chat session.
[Cleanup] Closing the async model client and Azure credential...
[Exit] Chat session closed.
```

Exit code: **0**; model requests: **0**.

### SDK regression checks and discovery limitation

The standard existing-test selector was attempted:

```powershell
.\.labenv\Scripts\python.exe -m unittest discover -s .\1-Develop_GenAI_Apps_with_Foundry\tests -p test_foundry_labs.py -k ChatTests -v
```

It exited **1**, before executing SDK test cases, because the shared module imports a missing legacy fine-tuning script. The full redacted traceback is retained in the validation artifact:

```text
ImportError: Failed to import test module: test_foundry_labs
```

```text
FAILED (errors=1)
```

No shared test or sibling file was modified. As a bounded fallback, the unchanged existing `ChatTests` class and only its own imports/helpers/client bindings were executed from the source AST, excluding unrelated module bindings and test classes. All **nine** SDK tests passed, including request/history shapes, contiguous streamed text, service-error handling, and async cleanup:

```text
OK
```

Capture checks additionally verified the exact ACK/recall outputs, no-history `UNKNOWN`, the three numbered streamed points and three completion markers, sequential async response count, cleanup before exit, and Unicode preservation. These results do not claim that standard shared-suite discovery passed.