# Lab 19 - Generate images with AI

[Visual data labs](../README.md) | [Repository setup](../../README.md)

This lab runs a Python client that sends a text prompt to an existing Azure
image-generation model deployment. It does not create an Azure resource or
deploy a model. Each non-empty prompt makes a model request and may incur
charges.

## Table of contents

- [1. Configure the endpoint and sign-in](#1-configure-the-endpoint-and-sign-in)
- [2. Install the Python dependencies](#2-install-the-python-dependencies)
- [3. Run the client and enter a prompt](#3-run-the-client-and-enter-a-prompt)
- [4. Inspect the generated image](#4-inspect-the-generated-image)
- [How the client works](#how-the-client-works)
- [Troubleshooting and safe file handling](#troubleshooting-and-safe-file-handling)
- [Validation and conclusion](#validation-and-conclusion)
- [Captured output](#captured-output)
  - [Live image-generation request](#live-image-generation-request)
  - [Non-generating dry run](#non-generating-dry-run)

## 1. Configure the endpoint and sign-in

From the repository root, keep an existing `.env` file. Copy the example only
if this lab does not already have one:

```powershell
if (-not (Test-Path .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\.env)) {
    Copy-Item .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\.env.example .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\.env
}
```

In the lab's `.env`, set:

| Variable | Value |
|---|---|
| `ENDPOINT` | The Azure OpenAI resource's OpenAI v1 endpoint, such as `https://<resource>.openai.azure.com/openai/v1/`. |
| `MODEL_DEPLOYMENT` | The exact name of an image-generation model deployment available through that endpoint. |

This client uses Microsoft Entra authentication through
`DefaultAzureCredential` with the `https://cognitiveservices.azure.com/.default`
scope. Sign in with an identity that has permission to use the deployment; for
Azure CLI sign-in, run this only if needed:

```powershell
az login
```

The script loads `.env` from beside `image-client.py`; existing process
environment variables take precedence. Keep `.env` private and do not paste
tokens or endpoint values into shared logs.

## 2. Install the Python dependencies

The shared launcher uses the repository's `.labenv` environment. If the
dependencies are not installed, run this from the repository root:

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\ image-client.py -Install
```

The launcher installs `requirements.txt` and then starts the client. At its
first prompt, type `quit` and press Enter to finish setup without requesting an
image. Do not use `-Install` when the dependencies are already available; it
installs packages into the shared environment. For later runs, omit `-Install`.

## 3. Run the client and enter a prompt

The client numbers output images from `image_1.png` on every start. If the lab
already contains `images\image_1.png`, a normal launch from the lab folder
would overwrite that file on the first successful generation. To preserve any
existing image, run the client from a fresh output directory instead. From the
repository root, after `.labenv` is ready:

```powershell
$client = (Resolve-Path .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\image-client.py).Path
$python = (Resolve-Path .\.labenv\Scripts\python.exe).Path
$output = Join-Path $PWD ("lab19-output-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
if (Test-Path -LiteralPath $output) { throw "Choose a new output directory; this one already exists." }
New-Item -ItemType Directory -Path $output | Out-Null
Push-Location $output
try {
    & $python $client
} finally {
    Pop-Location
}
```

When the client displays `Enter the prompt (or type 'quit' to exit):`, enter a
natural-language description, for example:

```text
Create an image of a cheerful blue robot eating pizza at a kitchen table, in a colorful editorial illustration style.
```

Wait for the generation request to finish and for the client to show the next
prompt before entering another description. Each non-empty prompt sends a
separate request. To finish without another request, type `quit` and press
Enter. A blank line is rejected locally with `Please enter a prompt.` and does
not call the image service.

## 4. Inspect the generated image

The isolated working directory keeps generated files out of the lab's existing
`images` folder. While still in the same PowerShell session, list the new
outputs with:

```powershell
Get-ChildItem (Join-Path $output 'images') -Filter 'image_*.png' |
    Select-Object Name, Length
```

The script prints `Image saved as ...` after writing each returned image. Check
the image before sharing it. Starting another client in the same working
directory starts numbering at `image_1.png` again; use a new output directory
or preserve previous results first.

## How the client works

`image-client.py` loads the adjacent `.env`, obtains an Entra token provider,
and creates an OpenAI client with `ENDPOINT` as its base URL. For each
non-empty input it calls `client.images.generate` with the configured
deployment, the prompt, and `n=1`. It decodes the returned base64 image and
writes a PNG beneath `images` in the process's current working directory.

The filename counter resets each time the process starts. The client does not
keep a prompt history or delete old files.

## Troubleshooting and safe file handling

- **HTTP 401:** A previous setup used a Foundry project endpoint and received
  HTTP 401. That is historical evidence, not a test of the current
  configuration. This client needs the Azure OpenAI OpenAI v1 endpoint ending
  in `/openai/v1/`, not a Foundry project URL ending in
  `/api/projects/<project>`.
- **Authentication or access denied:** Check the active `DefaultAzureCredential`
  sign-in and the identity's access to the configured model deployment. The
  dry run below does not validate authentication or permissions.
- **Deployment not found or unsupported model:** Verify the exact deployment
  name and that the deployment supports image generation. This lab does not
  create or change model deployments.
- **Protect existing images:** The shared launcher runs with the lab folder as
  its working directory. Since numbering restarts at `image_1.png`, generating
  there can replace an existing file. Use a fresh output directory as shown
  above.
- **An error with exit code 0:** The script catches exceptions and prints the
  error without setting a nonzero exit status. Read the console output; an exit
  code of 0 alone does not establish that generation succeeded.
- **Costs and cleanup:** A successful prompt may incur model usage charges.
  The client creates only local image files; it does not provision or delete
  Azure resources. Review generated files before removing them.

## Validation and conclusion

One live request successfully generated a PNG using the configured deployment.
A separate non-generating dry run exercised startup, blank-input handling, and
the `quit` path without an Azure request. The pre-existing
`images\image_1.png` was verified unchanged, and the isolated live output was
removed after verification. No packages were installed and no Azure resources
were created or updated.

An initial attempt to pipe input directly into `run-lab.ps1` was rejected by
PowerShell's parameter binder; the Python client then received EOF. Because
the client catches exceptions, that attempt still returned exit code 0. The
captured run below instead launched the same launcher in a child PowerShell
process with redirected standard input.

**Conclusion:** The live request confirms that the current configuration,
authentication, and deployment could generate one image during this run. It
does not guarantee future availability or identical results.

## Captured output

The captures below distinguish one live image-generation request from a
non-generating dry run. The shared `.labenv` already existed; no packages were
installed. Local paths are redacted, and no `.env` values, credentials, or
signed URLs are included.

### Live image-generation request

On November 15, 2026, one prompt was sent to the configured deployment. To
preserve the existing lab image, the client was launched directly with the
shared environment's Python interpreter and `image-client.py`; its working
directory was a fresh, isolated folder under the repository root. This
one-off validation does not replace the lab launch instructions above. The
client loaded its existing adjacent `.env`; no configuration was copied or
printed.

```text
Process: <repository>\.labenv\Scripts\python.exe "<repository>\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\image-client.py"
Working directory: <fresh .lab19-live-* directory under the repository root>
Input: A simple flat illustration of a red apple with a green leaf, centered on a pale blue background.
Next input: quit
```

The client does not echo redirected input. The following is the actual
`Image saved as ...` output line with only the isolated local path redacted:

```text
Image saved as <isolated-output>\images\image_1.png
```

The process exited with code `0`. The returned file had a valid PNG signature,
dimensions `1254 x 1254`, and size `426,978` bytes. The scratch image was
removed after verification; the existing lab `images\image_1.png` remained
unchanged. One image-generation request was made and may incur usage charges;
no Azure resource was created or updated.

### Non-generating dry run

The separate dry run launched the shared launcher from the repository root
with `image-client.py`; its inputs were a blank line and then `quit`. The app
does not echo redirected input. The console-clear control character is
omitted from this excerpt.

```powershell
pwsh -NoLogo -NoProfile -File .\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\19-generate-images-with-ai\ image-client.py
```

```text
Enter the prompt (or type 'quit' to exit): Please enter a prompt.
Enter the prompt (or type 'quit' to exit):
```

The child process exited with code `0`. A read-only before/after check reported
`EXISTING_IMAGE_UNCHANGED=True` for `images\image_1.png` and
`IMAGE_2_EXISTS=False`. These results confirm the blank-input and quit paths
only; no image-generation request or live Azure validation was performed.
