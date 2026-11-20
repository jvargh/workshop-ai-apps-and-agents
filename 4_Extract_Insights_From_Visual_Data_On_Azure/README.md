# 04 - Extract insights from visual data on Azure

[All labs and shared setup](../README.md)

| Lab folder | Scope and status |
|---|---|
| [18-develop-vision-enabled-chatapp](18-develop-vision-enabled-chatapp/) | Vision-enabled chat with local and URL images. |
| [19-generate-images-with-ai](19-generate-images-with-ai/) | Image generation; earlier live API validation recorded. |
| [20-analyze-media-with-content-understanding](20-analyze-media-with-content-understanding/) | Image descriptions/tags; earlier analyzer and image tests recorded. |
| [21-extract-info-from-mm-content](21-extract-info-from-mm-content/) | Assets-only scaffold; no runnable application. |
| [22-develop-content-understanding-client-app](22-develop-content-understanding-client-app/) | Business-card analyzer creation and extraction. |
| [zcreate-knowledge-mining-with-azureai-search](zcreate-knowledge-mining-with-azureai-search/) | Search enrichment pipeline; PDF upload remains blocked by storage policy. |

Each linked guide includes its configuration, commands, and known validation
limits.

## Run an implemented lab

From the repository root, copy the selected `.env.example` to a local `.env`,
fill in your settings, and sign in with `az login`.

```powershell
.\run-lab.ps1 .\4_Extract_Insights_From_Visual_Data_On_Azure\18-develop-vision-enabled-chatapp\ image-chat-app.py -Install
```

Specify the Python file explicitly for folders with several scripts. Local
results, business-card images, multimodal inputs, and screenshots may be
excluded from Git; use each guide's instructions to obtain missing samples.

Do not treat an empty successful indexer execution as successful knowledge
mining. The [Search lab guide](zcreate-knowledge-mining-with-azureai-search/)
documents the current zero-document state and recovery steps.
