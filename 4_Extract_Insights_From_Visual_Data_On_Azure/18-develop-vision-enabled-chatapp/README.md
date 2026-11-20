# Lab 18 - Develop a vision-enabled chat app

[Official lab](https://microsoftlearning.github.io/mslearn-ai-vision/Instructions/Exercises/01-gen-ai-vision.html) | [Visual-data labs](../README.md) | [Repository setup](../../README.md)

This lab uses a Python chat app to ask questions about produce images. It sends
the image and your text prompt to an existing vision-capable Azure OpenAI
deployment. The URL exercise uses the guide's orange image; the final exercise
uses the local `mystery-fruit.jpeg` image.

## Table of contents

- [1. Prepare Azure access and configuration](#1-prepare-azure-access-and-configuration)
- [2. Install dependencies when needed](#2-install-dependencies-when-needed)
- [3. Run the URL-based orange-image exercise](#3-run-the-url-based-orange-image-exercise)
- [4. Run the local mystery-fruit exercise](#4-run-the-local-mystery-fruit-exercise)
- [How the app works](#how-the-app-works)
- [Troubleshooting, privacy, and costs](#troubleshooting-privacy-and-costs)
- [Images and optional playground exercise](#images-and-optional-playground-exercise)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [1. Current live local-image run](#1-current-live-local-image-run)
  - [2. Current no-request dry run](#2-current-no-request-dry-run)
  - [3. Initial input-capture attempt](#3-initial-input-capture-attempt)
  - [4. Historical live tests](#4-historical-live-tests)

## 1. Prepare Azure access and configuration

Before running the app, make sure you can access an existing Azure OpenAI
resource with a vision-capable model deployment. This lab reuses that
deployment; it does not create or update Azure resources. Model requests can
incur usage charges.

From **PowerShell at the repository root**, create this lab's `.env` from the
example only if the file does not already exist. This preserves existing local
configuration:

```powershell
if (-not (Test-Path .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\.env)) {
    Copy-Item .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\.env.example .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\.env
}
```

Open the lab's `.env` and set:

```dotenv
ENDPOINT=https://<your-resource>.openai.azure.com/openai/v1/
MODEL_DEPLOYMENT=<your-existing-vision-capable-deployment>
```

- `ENDPOINT` must be the Azure OpenAI v1 endpoint ending in `/openai/v1/`;
  this app rejects a Foundry project endpoint or a Content Understanding
  endpoint.
- `MODEL_DEPLOYMENT` must be the actual deployment name in that resource; it
  may differ from the model-family name.
- The app uses `DefaultAzureCredential` with the `https://ai.azure.com/.default`
  scope. If you use Azure CLI authentication, run `az login` in a terminal
  when needed. Do not put an API key or access token in the README or share it.

The script loads `.env` from this lab folder, regardless of the current
directory. Existing process environment variables take precedence.

## 2. Install dependencies when needed

The workspace launcher uses the shared `.labenv` Python environment. If the
required packages are not installed, run this from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py -Install
```

`-Install` installs the requirements and then starts the app. At the image
question prompt, enter `quit` to end this setup run without sending a model
question. Do not add `-Install` to subsequent runs unless you need to install
or update the dependencies.

## 3. Run the URL-based orange-image exercise

From the repository root, start the app in URL mode:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py --image-source url
```

When the app asks `Ask a question about the image`, enter this prompt:

```text
Suggest some recipes that include this fruit
```

Wait for the response, then enter `quit` at the next prompt to exit. The app
sends the guide's public
[orange image](https://microsoftlearning.github.io/mslearn-ai-vision/Labfiles/gen-ai-vision/orange.jpeg)
URL with your question.

## 4. Run the local mystery-fruit exercise

Start the app in local-image mode from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py --image-source local
```

Local mode is the default, so the shorter command below is equivalent:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\
```

At the question prompt, enter:

```text
What is this fruit? What recipes could I use it in?
```

The default image is [mystery-fruit.jpeg](mystery-fruit.jpeg), which shows
dragon fruit. After reviewing the response, enter `quit` to exit. Enter prompts
at the running app's prompt; `run-lab.ps1` does not accept pipeline input.

## How the app works

[image-chat-app.py](image-chat-app.py) follows the guide's five main steps:

1. **Add references:** import the OpenAI SDK, Azure Identity, and
   `python-dotenv`.
2. **Get configuration settings:** load the endpoint and deployment name from
   this lab's `.env`.
3. **Create an OpenAI client:** use Microsoft Entra authentication through
   `DefaultAzureCredential`.
4. **Initialize prompts:** provide grocery-store produce-assistant
   instructions.
5. **Get a response to image input:** send a developer message and a user
   message containing the text prompt and image to the Responses API.

The URL mode sends the guide's image URL. Local mode reads the JPEG beside the
script, base64-encodes it, and sends a `data:image/jpeg;base64,...` image URL.
The output is printed from `response.output_text`. Each prompt is an independent
request about the same image; the app does not retain conversation history.

The implementation also validates the endpoint and deployment setting,
resolves the local image relative to the script, rejects blank prompts, accepts
`quit` regardless of capitalization, and reports authentication, service,
file, and invalid-response errors. The credential and SDK client are closed
when the app exits.

## Troubleshooting, privacy, and costs

- **Invalid or missing endpoint:** Set `ENDPOINT` to the Azure OpenAI v1
  endpoint ending in `/openai/v1/`. Do not use the project endpoint from a
  Foundry project.
- **Missing deployment or unsupported image input:** Set
  `MODEL_DEPLOYMENT` to an existing deployment that supports image input.
- **Authentication or access error:** Sign in with an identity that can access
  the resource and deployment. If using the Azure CLI credential, run `az
  login`; installing packages does not grant Azure permissions.
- **Local image not found:** Keep `mystery-fruit.jpeg` beside
  `image-chat-app.py`; the script resolves the image relative to its own file.
- **No response or service error:** The app exits with status `1` for
  authentication, service, file, and invalid-response errors. Review the
  reported error without copying credentials or private endpoint details into
  a shared transcript.
- **Privacy and usage:** The text prompt and image are sent to the configured
  model service. Each non-`quit` prompt may incur usage charges. Avoid
  sensitive images or prompts.
- **Resources:** This code does not create or modify Azure resources or
  deployments.

## Images and optional playground exercise

- [mystery-fruit.jpeg](mystery-fruit.jpeg) is used by the final local-image
  exercise.
- [orange.jpeg](orange.jpeg) is a local reference copy; URL mode uses the
  guide's public image URL instead.
- [mango.jpeg](mango.jpeg) is for an optional Foundry chat playground exercise:
  attach it in the playground and ask, `What desserts could I make with this
  fruit?`

The playground upload was not automated or tested. This README documents the
Python client and its two image modes.

## Validation and conclusion

| Evidence | What it establishes |
|---|---|
| Current client syntax check | The Python source compiled successfully without creating bytecode files. |
| Current launcher dry run | The launcher started local mode and returned status `0` after `quit`; no image question or model request was sent. |
| Current live run, November 15, 2026 | One local-image question completed using Azure authentication and the configured deployment; the app returned status `0` after `quit`. |
| Historical live runs, October 30, 2026 | Both image modes were previously exercised with Azure authentication and real model requests; see the historical summary below. |
| Limits | The current live run tested one local-image prompt only; it did not freshly test URL mode or the optional playground exercise. Model responses may vary. |

**Conclusion:** The lab demonstrates image-plus-text prompts with both a
public image URL and a local JPEG. It requires a configured, accessible
vision-capable deployment; it does not provision one.

## Captured output

The live run below made one image-question request through the configured
deployment and then exited after `quit`. The separate dry run sent no question.
No packages were installed, no Azure CLI command was run, and no Azure
resources or deployments were created or changed. The displayed excerpts omit
the terminal-clear control character; the app does not echo redirected input.

### 1. Current live local-image run

Run on November 15, 2026, from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py --image-source local
```

Input at the app prompt: `What is this fruit? What recipes could I use it in?`
The input stream then supplied `quit` after the response.

Captured response excerpt (verbatim ASCII lines from the live response):

```text
Image source: local

Ask a question about the image
(or type 'quit' to exit)
Getting a response ...

### How to use it
To prepare it: slice it in half lengthwise, then scoop out the flesh with a spoon or peel off the skin and dice it. The **skin is not typically eaten**, but the flesh and seeds are edible.

### Recipe ideas

**1. Dragon Fruit Smoothie**
Blend dragon fruit with banana, mango, pineapple, yogurt or coconut milk, and a little lime juice.

**2. Smoothie Bowl**
Blend frozen dragon fruit with banana and coconut milk, then top with granola, chia seeds, berries, coconut flakes, and honey.
```

The complete answer identified dragon fruit (pitaya) and continued with
additional recipe ideas and a selection tip. A few non-ASCII characters in
the captured PowerShell stream appeared as replacement characters, so this
excerpt includes only response lines that were captured as ASCII; no
replacement wording has been inferred.

**Exit status: `0`.** The question received a model response, and the app
returned to its prompt before exiting on `quit`. This confirms one successful
local-image inference with the current configuration; it does not establish
that future responses will be identical.

### 2. Current no-request dry run

Command, from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py
```

Input at the app prompt: `quit`.

Captured output excerpt:

```text
Image source: local

Ask a question about the image
(or type 'quit' to exit)
```

**Exit status: `0`.** The app exits without printing a goodbye message. Since
the input was `quit`, it did not read or send the image and did not request an
Azure token or call the model service.

### 3. Initial input-capture attempt

An initial attempt piped `quit` into the PowerShell launcher. That launcher
does not accept pipeline input, so the child Python process received end of
input instead. The command exited with status `1`; this was a shell-input
capture error, not a missing dependency or an Azure failure. No model request
was sent.

Attempted command:

```powershell
'quit' | .\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py
```

Error excerpt (the machine-specific traceback path is omitted):

```text
The input object cannot be bound to any parameters for the command either because the command does not take pipeline input or the input and its properties do not match any of the parameters that take pipeline input.
EOFError: EOF when reading a line
```

For normal use, start the launcher and type the prompt into the running app.

### 4. Historical live tests

The following results are retained from the README's earlier validation and
are **historical results from October 30, 2026**, not runs from this update.
They used Azure authentication and real model requests; no responses were
mocked:

| Historical mode | Prompt | Previously recorded result |
|---|---|---|
| Local | `What is this fruit? What recipes could I use it in?` | Identified dragon fruit/pitaya and suggested smoothies, fruit salad, salsa, sorbet, and other recipes. |
| URL | `Suggest some recipes that include this fruit` | Identified an orange and suggested salad, glaze, smoothie, marmalade, cake, and other recipes. |

The earlier record states that both runs exited with status `0` after `quit`.
It also records separate isolated checks for blank input, uppercase `QUIT`,
local JPEG data-URL encoding, request structure, and invalid endpoints or
responses. Those historical checks do not replace a fresh live test of the
configured Azure resource.
