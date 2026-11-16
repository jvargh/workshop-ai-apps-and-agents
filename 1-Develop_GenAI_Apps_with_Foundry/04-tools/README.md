# Lab 4 - Create a generative AI app that uses tools

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/04a-use-own-data.html) | [Section setup](../README.md)

[tools-app.py](tools-app.py) extends the Responses chat client with two hosted tools: **web search** for current public information and **file search** for Margie's Travel services in the six included [brochures](brochures/). A vector store is a searchable collection of uploaded documents; the application creates one, waits for brochure indexing, and makes it available to file search.

The client preserves follow-up context using `previous_response_id`. It prints the actual search calls and citations returned by the service, rather than assuming an answer used a tool. Creating a Foundry project and deploying a supported model remain manual prerequisites.

## Table of contents

- [1. Configure access](#1-configure-access)
- [2. Install dependencies once](#2-install-dependencies-once)
- [3. Run the brochure and web-search conversation](#3-run-the-brochure-and-web-search-conversation)
- [4. Review the report and cleanup](#4-review-the-report-and-cleanup)
- [Optional: compare web search in the playground](#optional-compare-web-search-in-the-playground)
- [Troubleshooting](#troubleshooting)
- [Validation](#validation)
  - [Conclusion](#conclusion)
- [Captured output](#captured-output)
  - [1. Configuration and authentication](#1-configuration-and-authentication)
  - [2. Install command and setup-only exit](#2-install-command-and-setup-only-exit)
  - [3. Conversation command and individual prompts](#3-conversation-command-and-individual-prompts)
    - [Blank input](#blank-input)
    - [What's happening in San Francisco next month?](#whats-happening-in-san-francisco-next-month)
    - [What hotels does Margie's Travel offer there?](#what-hotels-does-margies-travel-offer-there)
    - [Explicit brochure lookup: rate-limit failure](#explicit-brochure-lookup-rate-limit-failure)
    - [Fresh full-conversation retry: still rate-limited](#fresh-full-conversation-retry-still-rate-limited)
    - [Brochure-only recovery and quit](#brochure-only-recovery-and-quit)
  - [4. Cleanup and captured report](#4-cleanup-and-captured-report)
  - [5. Offline checks and remaining limits](#5-offline-checks-and-remaining-limits)

## 1. Configure access

Run the commands in **PowerShell from the repository root**. Create `.env` from the template only if it does not already exist, then sign in:

```powershell
if (-not (Test-Path .\1-Develop_GenAI_Apps_with_Foundry\04-tools\.env)) {
    Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\04-tools\.env.example .\1-Develop_GenAI_Apps_with_Foundry\04-tools\.env
}
az login
```

Edit this lab's `.env`, replacing any starter placeholders:

| Setting | What to enter |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Your resource's HTTPS Azure OpenAI v1 URL, ending `/openai/v1/`. Do not use the project `/api/projects/...` endpoint. |
| `MODEL_DEPLOYMENT` | An existing deployment that supports Responses with both `web_search` and `file_search`. The guide uses GPT-5.2; use a supported deployment available to you. |

You can use the same endpoint/deployment settings as Lab 3 if that deployment supports both tools. Authentication uses Microsoft Entra ID, not an API key. Your identity needs permission to call the model and create/delete files and vector stores.

**Costs and privacy:** This lab uploads the supplied PDFs to Azure, creates temporary vector storage, and makes billable model/search calls. Web search sends search queries to Bing and may process them outside your Azure compliance/geographic boundary; see [Microsoft's web-search guidance](https://learn.microsoft.com/azure/foundry/openai/how-to/web-search). Use only approved public data and do not enter sensitive information.

## 2. Install dependencies once

After configuring access, run:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\04-tools\ tools-app.py -Install
```

**The launcher installs packages and then starts the application.** It uploads and indexes the brochures before opening the question prompt. To finish this setup step, enter `quit` and wait for temporary-resource cleanup and the PowerShell prompt. Upload/indexing and storage costs may apply even if you ask no questions.

The separate run command in step 3 reuses the installed packages but creates a fresh brochure store and chat session; it does not need `-Install`.

## 3. Run the brochure and web-search conversation

Launch one client:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\04-tools\ tools-app.py
```

First, watch `[Store]`, `[Upload 1/6]` through `[Upload 6/6]`, and `[Index]`. Wait until all six brochures are indexed and `Enter a question (or type "quit" to exit):` appears. Then enter these inputs **one at a time in the running client, not in PowerShell**. Press Enter and wait for each answer and the next input prompt. The first two questions match the guide; the third explicitly requests a fresh brochure lookup because the model may otherwise reuse earlier search results.

| Step | Input or action | What to look for |
|---|---|---|
| 1 | Press Enter without typing anything. | `No model request was sent.` The brochure setup has already occurred. |
| 2 | `What's happening in San Francisco next month?` | Current event information, `[Tools] web_search_call: completed`, and web-source URLs. Check the cited dates: "next month" depends on when you run the lab. |
| 3 | `What hotels does Margie's Travel offer there?` | The answer retains San Francisco context. It may make a new file-search call or reuse brochure information retrieved during step 2; inspect `[Tools]` rather than assume a new search occurred. |
| 4 | `Search the uploaded brochures now for Margie's Travel San Francisco hotels. Cite the retrieved brochure rather than relying on previous answers.` | Look for `[Tools] file_search_call: completed` and `[Retrieved] Brochure: San Francisco Brochure.pdf`. Review the answer's hotel details against the retrieved brochure. |
| 5 | `quit` | Temporary-resource cleanup runs, `results\tools-chat.json` is saved, and control returns to PowerShell. |

The model chooses which tools to call; making both available does not guarantee both run on every turn. If `[Tools] No search tool was called` appears, that answer is **not** evidence of successful search. Retry with an explicit instruction such as `Search the web for events in San Francisco next month and cite your sources.` or `Search Margie's Travel brochures for its San Francisco hotels and cite the brochure.`

Compare the answer with its sources. `[Retrieved]` lists files returned by file search; `[Source]` lists citation annotations actually returned with the answer. They are different evidence: retrieved filenames are not automatically answer citations. A completed tool call proves the tool ran, not that every statement in the answer is correct. The application does not implement a custom Python function or code interpreter; these two search tools execute in the service.

## 4. Review the report and cleanup

A successfully completed, nonempty session saves `results\tools-chat.json` with the deployment, brochure names, questions, answers, response IDs, actual tool-call types/statuses, retrieved file names/IDs, citation annotations, and a temporary-resource deletion flag. The file is ignored by Git and overwritten by the next successful nonempty session. Starting again creates a fresh store and conversation, not a continuation of the saved report.

Unlike the starter guide, this implementation deletes **only the uploaded files and vector store created by its own run**, including when indexing or chat fails. It closes file handles and attempts all registered resource deletions even if one deletion fails. It does not delete your model deployment, Foundry project, resource group, or unrelated files/stores.

If cleanup fails, the script reports an error instead of success; check the resource ID in `[Cleanup]` and remove only that resource after investigating. Forced process termination or a lost create/upload response can prevent complete cleanup, so inspect your resource's files/stores if a run is interrupted. There is no need to delete a shared resource group.

Quitting or sending EOF before asking a question still cleans up the startup uploads but does not save a new transcript.

## Optional: compare web search in the playground

To follow the guide's portal exercise, use the same deployed model and set the instructions to `You are a travel assistant that provides information on travel services available from Margie's Travel.` Ask `What are some recommended tourist activities in New York next month?` before and after adding `web_search`. Review whether the second answer uses current cited sources. This is a separate manual exercise, not something the terminal client validates.

## Troubleshooting

- **Configuration error:** Replace the Lab 4 `.env` placeholders with the actual resource endpoint and deployment name. Keep working configuration in other labs unchanged.
- **Authentication/permission error:** Check `az login`, the selected tenant/subscription, and inference plus file/vector-store permissions. Do not switch to a shared resource group deletion as a workaround.
- **Unsupported tool or disabled web search:** Check your deployment, region, account policy, and tenant's web-search/Bing restrictions. A Lab 3 chat success alone does not establish support for these tools.
- **Brochure/indexing error:** Keep all six PDFs in `brochures`. A failed or partial upload/indexing run is an error; the client does not chat against incomplete data.
- **History or source mismatch:** Check `[History]`, `[Tools]`, and `[Source]`, then start a fresh session. Citation markers without a completed search call are not enough to validate the exercise.

## Validation

Dependency installation and a live launcher run passed against an existing GPT-5.5 deployment. The test used Lab 3 settings without overwriting configuration files; configure your own Lab 4 `.env` before running the walkthrough.

| Check | Observed result |
|---|---|
| Brochure setup | All **six PDFs** uploaded and indexed. |
| Current-information question | Completed web and file searches returned web citations and retrieved brochure names. |
| Hotel follow-up | Retained San Francisco context and named **The Lombard Hotel** and **The Wharf Hotel**, without a new search call. |
| Explicit brochure lookup | Completed a fresh file search and retrieved **San Francisco Brochure.pdf**. Retrieved files were recorded separately because no file-citation annotations were returned. |
| Exit and cleanup | Returned exit **0**, saved three turns in `results\tools-chat.json`, and confirmed deletion of the six uploaded files and vector store. |

**Nine offline tests passed**, covering request settings, conversation history, tool/citation evidence, missing brochures, indexing/upload failures, and cleanup errors. These results describe the tested configuration, not a guarantee that every deployment supports both tools.

### Conclusion

The client demonstrated live web search, brochure retrieval, follow-up context, and cleanup of its temporary resources. Check actual tool calls and sources rather than assume every answer performs a fresh search. Portal behavior and the factual accuracy of every generated statement were not independently validated.

## Captured output

These are actual launcher runs using the existing configuration, not a new
deployment. Inputs were supplied through a bounded UTF-8 subprocess only after
the application displayed its input prompt. Input text is included below
because piped input is not echoed by the client. Configuration values, Azure
identifiers, and absolute repository paths are replaced with placeholders;
answer wording, public citations, and event dates are preserved. Output blocks
are excerpts unless described otherwise.

| Run | Exit | Observed result |
|---|---|---|
| Documented `-Install`, then `quit` | `0` | Six brochures indexed; setup resources deleted; no new report. |
| Documented conversation | `1` | Blank input, event question, and hotel follow-up worked; explicit brochure lookup failed with HTTP `429`. |
| Fresh conversation after a 75-second cooldown | `1` | First event question also failed with HTTP `429`. |
| Brochure-only recovery after a 180-second cooldown | `0` | Explicit file search and a brochure citation succeeded; `quit` saved one response. |

Every run created only its own six uploaded files and one vector store.
All **28** created resources were subsequently checked with read-only SDK
retrievals and returned **404 Not Found**, independently confirming deletion.
No preexisting files/stores, agents, deployments, projects, configuration, or
shared environment packages were changed.

### 1. Configuration and authentication

The conditional `.env` copy in section 1 was evaluated and left the existing
file unchanged. Both required settings were present and the endpoint had the
HTTPS `/openai/v1/` shape. This read-only authentication check succeeded;
its token and account details were not printed:

```powershell
az account get-access-token --resource https://ai.azure.com --output json
```

Authentication was already valid, so interactive `az login` was not rerun.
Project creation, deployment, and the optional playground comparison remain
manual prerequisites/exercises and were not performed.

### 2. Install command and setup-only exit

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\04-tools\ tools-app.py -Install
```

Direct imports and requirement constraints were checked first.
`pip install --dry-run --no-index` confirmed there was nothing to install,
and `pip check` printed `No broken requirements found.` The actual documented
launcher then ran with process-local `PIP_NO_INDEX=1` and
`PIP_DISABLE_PIP_VERSION_CHECK=1`, ensuring its install step could not fetch
packages. All 29 direct/transitive requirement lines reported
`Requirement already satisfied`; the four direct lines were:

```text
Requirement already satisfied: python-dotenv in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\04-tools\requirements.txt (line 1)) (1.2.3)
Requirement already satisfied: azure-identity in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\04-tools\requirements.txt (line 2)) (1.25.3)
Requirement already satisfied: openai in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\04-tools\requirements.txt (line 3)) (2.54.0)
Requirement already satisfied: requests in .\.labenv\Lib\site-packages (from -r <repository-root>\1-Develop_GenAI_Apps_with_Foundry\04-tools\requirements.txt (line 4)) (2.34.2)
```

Startup and the setup-only input produced:

```text
[Setup] Loading this lab's endpoint and deployment configuration...
Selected deployment: <configured-value>; local brochures: 6.
Uploads, vector storage, model calls, and search tools may incur charges.
Web search sends search queries to Bing. Do not enter sensitive information.
[Connect] Preparing the client with Microsoft Entra authentication...
[Store] Creating a temporary travel-brochures vector store...
Vector store created: <vector-store>
[Upload 1/6] Dubai Brochure.pdf
[Upload 2/6] Las Vegas Brochure.pdf
[Upload 3/6] London Brochure.pdf
[Upload 4/6] Margies Travel Company Info.pdf
[Upload 5/6] New York Brochure.pdf
[Upload 6/6] San Francisco Brochure.pdf
[Index] Attaching the uploaded files and waiting for indexing...
[Index] All 6 brochures are ready for file search.

[Chat] Both file_search and web_search are available; the model chooses when to use them.

Enter a question (or type "quit" to exit): quit
[Input] Quit requested. Ending the conversation.
```

The cleanup tail is shown in subsection 4; the setup-only run then ended with:

```text
No questions submitted; no chat report saved.
[Complete] Tools chat ended and temporary-resource cleanup completed.
```

### 3. Conversation command and individual prompts

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\04-tools\ tools-app.py
```

This fresh session again uploaded and indexed all six brochures.

#### Blank input

```text
Enter a question (or type "quit" to exit): 
Please enter a question. No model request was sent.
```

#### What's happening in San Francisco next month?

<details>
<summary>Complete answer and returned search/citation evidence</summary>

```text
Enter a question (or type "quit" to exit): What's happening in San Francisco next month?
[History] First question; no previous response context.
[Request] Sending prompt using Responses. Waiting for the answer and any search calls...

[Response] Model answer:
Next month is **December 2026**, and San Francisco is packed with holiday events. Here are some good picks:

### Big holiday & city events
- **Downtown First Thursdays — Dec. 3**: Free street party on 2nd Street with DJs, live music, drag, street performances, fashion, food/drinks, and 21+ outdoor bars. ([sftravel.com](https://www.sftravel.com/article/san-francisco-festivals-events-december))
- **Let’s Glow SF — Dec. 4–13**: A free nighttime projection-art festival downtown, with animated light installations on major buildings; projections run nightly around **5:30–10 p.m.** ([goldengate.org](https://www.goldengate.org/events/lets-glow-sf-2026/))
- **Winter Walk Union Square — Dec. 9–27**: Maiden Lane turns into a festive pedestrian plaza/holiday marketplace with food, bars, décor, shopping, and entertainment. ([visitunionsquaresf.com](https://visitunionsquaresf.com/winter-walk))
- **Union Square Ice Rink — open all month**: Skating runs **Nov. 4, 2026–Jan. 18, 2027**, generally **10 a.m.–11 p.m.** daily. ([unionsquareicerink.com](https://unionsquareicerink.com/union-square-ice-skating/))
- **Great Dickens Christmas Fair — through Dec. 20**: At the Cow Palace in Daly City, with Victorian London-style performers, shops, pubs, music halls, and holiday atmosphere. ([dickensfair.com](https://dickensfair.com/))
- **New Year’s Eve fireworks — Dec. 31 at midnight**: Waterfront fireworks over the Bay to welcome 2027. ([sf.funcheap.com](https://sf.funcheap.com/san-francisco-new-years-eve-fireworks/))

### Performing arts & shows
- **SF Ballet’s *Nutcracker***: A classic San Francisco holiday tradition at the War Memorial Opera House; December performances are a major draw and should be booked early. ([sfballet.org](https://www.sfballet.org/productions/nutcracker/))
- **Broadway/theater options** include *The Wiz* at the Orpheum Theatre **Dec. 4–6**, *The Outsiders* **Dec. 9–27**, and *Elf the Musical* **Dec. 15–20**. ([sftourismtips.com](https://www.sftourismtips.com/san-francisco-events-in-december.html))
- **“Elf” with the San Francisco Symphony — Dec. 18–20**: The film screened with live orchestral score at Davies Symphony Hall. ([marinmommies.com](https://www.marinmommies.com/calendar/elf-concert-san-francisco-symphony))

### Sports
- **Golden State Warriors home games** at Chase Center include Dec. 1 vs. Utah, Dec. 22 vs. Dallas, Dec. 25 vs. Denver, Dec. 27 vs. Minnesota, and Dec. 30 vs. Houston. ([nba.com](https://www.nba.com/warriors/schedule?os=f&ref=app))

A quick note: event schedules can change, and SF Travel specifically advises confirming dates/locations with organizers before making plans. ([sftravel.com](https://www.sftravel.com/article/san-francisco-festivals-events-december)) If you want to turn this into a trip, Margie’s Travel can arrange **flights, accommodation, transfers, visas, currency exchange, and excursions** , and their San Francisco hotel options include **The Lombard Hotel** and **The Wharf Hotel**.
[Tools] web_search_call: completed
[Tools] file_search_call: completed
[Retrieved] Brochure: San Francisco Brochure.pdf
[Retrieved] Brochure: Margies Travel Company Info.pdf
[Retrieved] Brochure: New York Brochure.pdf
[Retrieved] Brochure: London Brochure.pdf
[Retrieved] Brochure: Dubai Brochure.pdf
[Retrieved] Brochure: Las Vegas Brochure.pdf
[Tools] web_search_call: completed
[Tools] web_search_call: completed
[Tools] web_search_call: completed
[Tools] web_search_call: completed
[Source] San Francisco Festivals and Events in December: https://www.sftravel.com/article/san-francisco-festivals-events-december
[Source] Let’s Glow SF - Opening Night | Golden Gate: https://www.goldengate.org/events/lets-glow-sf-2026/
[Source] Winter Walk Presented by JPMorganChase - Visit Union Square SF: https://visitunionsquaresf.com/winter-walk
[Source] Plan Your Visit – Union Square Ice Rink: https://unionsquareicerink.com/union-square-ice-skating/
[Source] Home | Dickens Fair: https://dickensfair.com/
[Source] San Francisco New Year’s Eve Fireworks at Midnight (2026/2027): https://sf.funcheap.com/san-francisco-new-years-eve-fireworks/
[Source] Nutcracker - San Francisco Ballet: https://www.sfballet.org/productions/nutcracker/
[Source] San Francisco Events in December 2026 - SFTourismTips: https://www.sftourismtips.com/san-francisco-events-in-december.html
[Source] Elf in Concert | San Francisco Symphony 2026 | Marin Mommies: https://www.marinmommies.com/calendar/elf-concert-san-francisco-symphony
[Source] Schedule | Golden State Warriors - NBA.com: https://www.nba.com/warriors/schedule?os=f&ref=app
[Source] San Francisco Festivals and Events in December: https://www.sftravel.com/article/san-francisco-festivals-events-december
```

</details>

The service returned **five completed web-search calls and one completed
file-search call**, rather than merely generating links. Spot checks of the
actual public sources confirmed [Let's Glow SF](https://www.goldengate.org/events/lets-glow-sf-2026/)
on December 4–13, 2026, from 5:30–10 p.m., and the
[ice rink](https://unionsquareicerink.com/union-square-ice-skating/) season and
usual daily hours. The rink page also specifies an earlier December 31 closing.
The [Winter Walk page](https://visitunionsquaresf.com/winter-walk) showed
“More details coming soon!” and 2025 sponsors; it did **not** substantiate the
answer's December 9–27, 2026 dates. Other event/sports claims were not
independently checked. A completed search therefore does not establish the
accuracy of every recommendation.

#### What hotels does Margie's Travel offer there?

```text
Enter a question (or type "quit" to exit): What hotels does Margie's Travel offer there?
[History] Reusing the previous response context.
[Request] Sending prompt using Responses. Waiting for the answer and any search calls...

[Response] Model answer:
Margie’s Travel offers these **San Francisco** accommodation options:

- **The Lombard Hotel** — a friendly, family-run hotel within easy walking distance of popular sights including the **Golden Gate Bridge** and the **Presidio**; **free parking** included.
- **The Wharf Hotel** — good-value accommodation in the **Fisherman’s Wharf** area; **continental breakfast** included.
[Tools] No search tool was called for this response.
```

The follow-up retained San Francisco context, but made no fresh search and
returned no new citation. Direct text extraction from the one-page
[San Francisco brochure](brochures/San%20Francisco%20Brochure.pdf) confirmed
both hotel names, the Lombard description/free parking, and the Wharf
location/continental breakfast.

#### Explicit brochure lookup: rate-limit failure

```text
Enter a question (or type "quit" to exit): Search the uploaded brochures now for Margie's Travel San Francisco hotels. Cite the retrieved brochure rather than relying on previous answers.
[History] Reusing the previous response context.
[Request] Sending prompt using Responses. Waiting for the answer and any search calls...
[Cleanup] Removing any files and vector store tracked by this run...
```

All seven owned resources were deleted, then the client printed:

```text
Lab failed: Error code: 429 - {'error': {'message': 'Your requests to gpt-5.5 for <configured-value> in westus3 have exceeded token rate limit.', 'type': 'too_many_requests', 'param': None, 'code': 'rate_limit_exceeded'}}
```

The launcher exited `1`. This turn has **no answer or successful tool evidence**.
The queued final `quit` was not sent because the application never returned
to its input prompt. The failed session did not save its two successful earlier
answers to `tools-chat.json`; they are retained in the console capture above.

#### Fresh full-conversation retry: still rate-limited

The same run command was retried after a 75-second cooldown, with pacing
planned between subsequent model turns. It indexed six fresh brochure uploads
and accepted blank input, but the **first** event question failed with the
same HTTP `429` message after the client's configured SDK retries
(`max_retries=2`). It exited `1`, deleted its seven resources, and wrote no
new report. No quota, deployment, or account settings were changed.

#### Brochure-only recovery and quit

After a further 180-second cooldown, one final run used the same command.
To avoid another web-heavy conversation, only the explicit brochure prompt
and `quit` were sent:

```text
Enter a question (or type "quit" to exit): Search the uploaded brochures now for Margie's Travel San Francisco hotels. Cite the retrieved brochure rather than relying on previous answers.
[History] First question; no previous response context.
[Request] Sending prompt using Responses. Waiting for the answer and any search calls...

[Response] Model answer:
Margie’s Travel’s **San Francisco Brochure** lists these San Francisco hotel options:

- **The Lombard Hotel** — a friendly, family-run hotel within easy walking distance of popular sights, including the Golden Gate Bridge and the Presidio; **free parking** is included.
- **The Wharf Hotel** — great-value accommodation in the heart of the vibrant Fisherman’s Wharf area; **continental breakfast** is included.

The brochure says these are the accommodation options Margie’s Travel offers in San Francisco.
[Tools] file_search_call: completed
[Retrieved] Brochure: San Francisco Brochure.pdf
[Retrieved] Brochure: Margies Travel Company Info.pdf
[Retrieved] Brochure: Las Vegas Brochure.pdf
[Retrieved] Brochure: New York Brochure.pdf
[Retrieved] Brochure: Dubai Brochure.pdf
[Retrieved] Brochure: London Brochure.pdf
[Source] Brochure: San Francisco Brochure.pdf

Enter a question (or type "quit" to exit): quit
[Input] Quit requested. Ending the conversation.
```

This run had a completed file search **and an actual `file_citation`
annotation** for `San Francisco Brochure.pdf`. Its hotel details matched the
local brochure. It did not make a web-search call and was a fresh response
chain, not a continuation of either failed session.

### 4. Cleanup and captured report

Each run printed the following cleanup sequence, with its own identifiers:

```text
[Cleanup] Removing any files and vector store tracked by this run...
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <uploaded-file>
[Cleanup] Deleting this run's resource: <vector-store>
```

Only successful runs printed the subsequent cleanup-success message.
The brochure-only recovery ended with:

```text
[Cleanup] This run's uploaded files and vector store were deleted.
[Report] Saving answers, tool-call evidence, and citations locally...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\04-tools\results\tools-chat.json
[Complete] Tools chat ended and temporary-resource cleanup completed.
```

Before restoring the preexisting `results\tools-chat.json` byte-for-byte, the
new successful report was copied and sanitized as
[results/tools-chat-captured.json](results/tools-chat-captured.json).
It contains **one response**, six brochure names, one completed
`file_search_call`, six retrieved-file records, the San Francisco
`file_citation`, and `temporary_resources_deleted: true`. Configuration and
response/file identifiers are placeholders, and its generated timestamp was
removed. It is not a three-turn successful walkthrough or a transcript of
the failed sessions. The results directory remains Git-ignored.

The four runs did not create agents or an explicit Conversations API resource.
Response history was reused during the first conversation through
`previous_response_id`; the runtime does not explicitly delete saved model
responses. Cleanup above covers the uploaded files and vector stores only.

### 5. Offline checks and remaining limits

The normal targeted test command genuinely failed before running `ToolsTests`:

```powershell
.\.labenv\Scripts\python.exe -B -m unittest discover -s .\1-Develop_GenAI_Apps_with_Foundry\tests -p test_foundry_labs.py -k ToolsTests -v
```

All nine tests
then ran successfully, using disposable local test directories inside this
lab:

```text
Ran 9 tests in 0.114s

OK
AST-scoped unchanged ToolsTests: 9 passed; excluded unrelated stale module imports; no test-source edits.
```

The checks cover context preservation, actual tool/citation evidence,
no-tool answers, search failure, report-after-cleanup ordering, upload/indexing
failure cleanup, cleanup errors, missing brochures, and setup-only quitting.
They do not repair the shared discovery command. Live results establish
search execution, hotel grounding, context reuse, and scoped deletion, while
also preserving genuine rate-limit failures and a public-source date
limitation. No successful uninterrupted three-question report or playground
UI validation is claimed.
