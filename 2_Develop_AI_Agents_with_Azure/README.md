# 02 - Develop AI agents with Azure

[All labs and shared setup](../README.md)

| Lab folder | Guide scope |
|---|---|
| [06-buildaiagents](06-buildaiagents/) | Existing-agent chat and generated-file downloads. |
| [07-customtools](07-customtools/) | Local astronomy function tools. |
| [08-mcpintegration](08-mcpintegration/) | Hosted Learn MCP and local inventory MCP. |
| [09-integrateFoundryIQ](09-integrateFoundryIQ/) | Existing Foundry IQ agent and tool approvals. |
| [10-agent-framework](10-agent-framework/) | Expense-claim drafting; local recipient configuration. |
| [11-agent-orchestration](11-agent-orchestration/) | Sequential feedback-processing agents. |
| [z10a-m365-teams-integration](z10a-m365-teams-integration/) | Search-grounded chat and deployment walkthroughs. |
| [z10b-work-iq-integration](z10b-work-iq-integration/) | Work IQ via local MCP stdio. |
| [z10c-build-workflow-ms-foundry](z10c-build-workflow-ms-foundry/) | Existing customer-support workflow. |
| [z12-build-remote-agents-with-a2a](z12-build-remote-agents-with-a2a/) | Three local A2A agent services and a client. |

## Shared setup

From the repository root, copy the chosen folder's `.env.example` to a local
`.env`, fill in its settings, and sign in with `az login`. Use the deployment
name available in your project, not merely a model family name.

```powershell
.\run-lab.ps1 .\2_Develop_AI_Agents_with_Azure\07-customtools\ agent.py -Install
```

The folder and script are separate launcher arguments. Requirements vary
between labs; installing every lab into the shared environment can introduce
SDK version conflicts. An existing Foundry project alone does not provide the
agent, workflow, Search connection, or permissions needed by every exercise.

Read each guide's prerequisites and validation status. Agent creation and
model inference can be billable; cleanup behavior differs between clients.
