# Text analysis client

[Lab 12](../README.md) | [Language labs](../../README.md)

## What it does

[text-analysis.py](text-analysis.py) reads every text file in [reviews](reviews/)
and uses `TextAnalyticsClient` to display:

- The detected language.
- Named entities and categories.
- PII entities and the service's redacted version of the review.

It does not currently request sentiment or key-phrase analysis.

## Configure and run

Copy [.env.example](.env.example) to a local `.env`. Set `FOUNDRY_ENDPOINT`
to the Azure AI resource endpoint supporting the Language service, not a
Foundry project URL. Sign in with `az login`; the code uses
`DefaultAzureCredential`, not a key.

From the repository root:

```powershell
.\run-lab.ps1 .\3_Develop_Language_Soltns_with_AzureAI\12-analyze-text\text-analysis\ text-analysis.py -Install
```

The launcher sets the working directory so the relative `reviews` path works.
The application processes the files without an interactive prompt.

## Privacy and validation

The client prints the original reviews **and** detected PII before printing
redacted text. Console output is therefore not a privacy-safe export. Use
synthetic samples and do not publish real input or captured output.

Requests can incur Language-service usage charges. This guide describes the
checked-in implementation; no fresh live requests were made for the
documentation update.
