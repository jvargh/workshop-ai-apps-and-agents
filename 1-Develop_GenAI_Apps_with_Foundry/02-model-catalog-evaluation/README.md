# Lab 2 - Evaluate models with the Foundry model catalog

[Official lab](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/02-model-catalog-evaluation.html)
| [Downloaded guide](upstream-guide.md) | [Section setup](../README.md)

[evaluate-models.py](evaluate-models.py) compares two deployed models on the
fox/chicken/grain puzzle, including a contextual follow-up. It then submits
a real Foundry cloud evaluation with **45** synthetic travel questions.
The three retained quality criteria are coherence, fluency, and relevance;
Agent and Safety evaluators are not included.

## Table of contents

- [Configure and run](#configure-and-run)
  - [Runtime progress](#runtime-progress)
- [Portal steps and interpretation](#portal-steps-and-interpretation)
- [Results and recovery](#results-and-recovery)
- [Actual validation (2026-11-01)](#actual-validation-2026-11-01)
- [Captured output](#captured-output)
  - [1. Dependency precheck and normal command](#1-dependency-precheck-and-normal-command)
  - [2. Two-model puzzle and contextual follow-up](#2-two-model-puzzle-and-contextual-follow-up)
  - [3. Explicit resume and verified evaluation results](#3-explicit-resume-and-verified-evaluation-results)
  - [4. Help, focused test failure, and scope limits](#4-help-focused-test-failure-and-scope-limits)
  - [5. Scoped execution of the unchanged EvaluationTests](#5-scoped-execution-of-the-unchanged-evaluationtests)

## Configure and run

From the repository root:

```powershell
Copy-Item .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\.env.example .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\.env
az login
```

| `.env` setting | Meaning |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Resource URL ending `/openai/v1/`. |
| `MODEL_DEPLOYMENT` | Primary model, also used to generate questions and judge quality. |
| `COMPARE_DEPLOYMENT` | A second deployed model for puzzle comparison. |
| `PROJECT_ENDPOINT` | Foundry project URL: `https://<resource>.services.ai.azure.com/api/projects/<project>`. |

```powershell
# Normal run: start initially, automatically resume when saved state exists.
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py -Install

# Only the two-model puzzle comparison.
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --compare-only

# Resume an existing run, or retrieve its completed results, without a new job.
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --resume

# Start from scratch: archive previous local reports, then create a new run.
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --reset
```

`--samples 1` is available for a small diagnostic run; it is **not** completion
of the guide's 45-question evaluation. `--timeout` controls polling seconds
(default 1200); a timeout fails explicitly and leaves the remote run resumable.

The normal command now automatically resumes an existing evaluation instead
of failing with `A saved evaluation already exists`. Resume also works after
the cloud run completes: it downloads and validates the existing results
without repeating the model comparison, generating questions, or submitting
another evaluation. `--resume` remains available to explicitly require saved
state. Use `--compare-only` to repeat just the puzzle comparison.

`--reset` explicitly starts a **new, billable** evaluation, repeating the
model comparison and synthetic generation. It archives the previous five
evaluation reports, including the state and job IDs, under
`results\archive\<UTC-timestamp>`. It preserves `.env` and unrelated files,
and does **not** delete or cancel existing Azure jobs, datasets, or evaluations.
If an old run is still active, it may continue incurring charges alongside
the new run. Reset does not waive authentication, quota, or service errors.

`--reset`, `--resume`, and `--compare-only` cannot be combined. `--samples`
applies to a new/reset run; resuming retains the saved run's sample count.

### Runtime progress

The script prints the selected mode and stage-labelled progress messages before
model requests, report archiving, cloud submission, status polling, result
downloads, and score validation. It displays the puzzle and explains the
contextual follow-up, along with warnings about billable work.

Comparison-only success is announced after its report is saved. Cloud evaluation
completion is announced only after all requested rows and scores are validated
and the successful state is saved. Timeout messages explain that the remote job
is not canceled and can be resumed. Use `--help` for option descriptions.

## Portal steps and interpretation

1. In Foundry, browse the model catalog and compare GPT-5.2/GPT-5-mini
   leaderboard quality, cost, throughput, and safety as described in the guide.
2. Run the client, then locate its saved evaluation/run ID under the project's
   evaluations.
3. Inspect the generated questions, response quality metrics, individual
   failures, and the portal's analysis view.

The synthetic instructions include benign document-protection and booking-scam
awareness scenarios without personal data or wrongdoing instructions. The
travel system prompt matches the guide.

Puzzle timing/token usage is not a controlled benchmark or a retail-price
comparison. Quality scores are model-judged signals, not factual guarantees;
this compact companion retains three representative quality evaluators, not
every quality evaluator the portal may offer.

## Results and recovery

Private reports are written under `results`:

- `model-comparison.json`: both puzzle answers, follow-ups, elapsed time, usage.
- `evaluation-state.json`: project, evaluation ID, run ID, expected count/status.
- `cloud-evaluation.json`: latest service details, saved on completion or timeout.
- `evaluation-items.json`: individual rows/results, written only after completion.
- `evaluation-progress.json`: historical timeout snapshot from the initial
  validation; use the state/run/items reports for the latest completed results.

Success requires a completed cloud run, exactly the requested row count, and
all three metrics on every row. An existing state file triggers automatic
resume to prevent duplicate job submission. Use `--reset` only when you
intend to start a new job; do not delete the file merely because polling
timed out. If submission failed after evaluation creation but before a run ID
was returned, inspect that evaluation in Foundry before taking recovery action.

## Actual validation (2026-11-01)

The live comparison passed using existing GPT-5.5 and GPT-5-mini deployments
instead of the guide's GPT-5.2: both puzzle requests and both contextual
follow-ups completed.

The original 45-question synthetic run completed in Azure. Running the actual
launcher with `--resume --timeout 1` retrieved and validated its results and
exited **0**. No new evaluation job was submitted.

| Check | Observed result |
|---|---|
| Run status | `completed` |
| Expected rows | 45 |
| Scored rows (`result_counts.total`) | **45** |
| Available output rows | **45** |
| Service passed / failed / errored / skipped | **45 / 0 / 0 / 0** |
| Completed cloud evaluation validated | **Yes** |

Every row contains valid numerical scores for all three quality criteria:

| Criterion | Rows | Mean score | Minimum | Maximum |
|---|---|---|---|---|
| Coherence | 45 | 4.978 | 4 | 5 |
| Fluency | 45 | 4.844 | 4 | 5 |
| Relevance | 45 | 4.889 | 3 | 5 |

Historical note: on 2026-10-30, the first 20-minute polling attempt and a
10-minute resume both timed out with zero available rows. The job continued
remotely and was not canceled. That earlier snapshot is not the current
status; saved IDs allowed retrieval of the completed run without duplication.

Azure's preview synthetic-data-source fields do not match the OpenAI SDK's
standard run serialization schema. The client now retrieves runs with
`with_raw_response`, uses the parsed model for status checks, and saves the
original HTTP JSON for completed, failed, and timed-out run reports. This
preserves Azure-specific fields without triggering Pydantic serializer
warnings or suppressing warnings globally. API failures remain explicit.

Offline tests cover 45-row score validation, missing/invalid metrics, duplicate
prevention before inference, resume project matching, completed-run handling,
and bounded polling with persistent state. These mocked tests supplement the
live scores above. Portal leaderboards and analysis UI were not automated.

The normal command without flags also passed live after the auto-resume change,
returning exit 0 and validating the same 45 rows. Reset archival and exactly
one fresh-job submission were regression-tested with temporary files and a
mock service; no additional paid cloud job was started to test reset.
The same normal command also passed live with `UserWarning` treated as an
error after the report-export fix: all 45 rows validated, with no serializer
warnings. Regression tests verify raw preview fields are preserved and
service-reported failures still fail rather than appearing successful.

Cloud generation and scoring incur charges and create persistent evaluation
objects/data. Your identity needs project evaluation permissions, inference
access, and available model quota. Review/delete only your own disposable
evaluation artifacts in Foundry after use, not the shared project.

## Captured output

These are actual repository-root runs using the existing configuration and
deployments, anonymized as **model A** and **model B**. The saved cloud state
initially said `in_progress`; its existing run was already `completed` when
retrieved. Both automatic resume and explicit resume downloaded and validated
the **same 45-question run**. Neither submitted another evaluation.

The separate comparison sent the river puzzle and `Explain your reasoning.`
to each model: **four completed inference requests**, with conversation context
preserved for each follow-up. There are no interactive terminal prompts.
The existing `.env` and valid authentication were preserved rather than
overwriting configuration or repeating `az login`. No model, project, suite,
monitor, or dataset was created for this capture.

Resource URLs, deployment/job identifiers, contact data, and absolute personal
paths are redacted in the published logs and exported JSON. The inline puzzle
output normalizes Unicode punctuation to ASCII; answer wording is otherwise
unchanged, with trailing whitespace removed. Full UTF-8 transcripts and
redacted results are linked below.

### 1. Dependency precheck and normal command

All direct constraints and imports passed, including the 29-package dependency
closure. An offline `pip install --dry-run --no-index` exited `0` and proposed
no changes. The documented `-Install` command then ran with process-local
`PIP_NO_INDEX=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1`; every dependency was
already satisfied, and installed-package inventories were unchanged.

| Direct requirement | Installed version |
|---|---|
| `openai>=2.54.0,<3` | `2.54.0` |
| `azure-identity>=1.25.0,<2` | `1.25.3` |
| `python-dotenv>=1.2.0,<2` | `1.2.3` |
| `requests>=2.32.0,<3` | `2.34.2` |

The supported `--timeout 60` bounded polling while retaining the saved run's
45 samples:

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py -Install --timeout 60
```

Application output after the already-satisfied dependency lines:

```text
[Setup] Loading this lab's configuration and primary deployment...
[Mode] Checking the selected option and saved evaluation state...
Saved evaluation found; automatically resuming it. Use --reset to start fresh.
Mode: automatic resume. Reusing the saved run; skipping comparison and new job submission.
An existing active cloud run may continue incurring charges.
[Setup] Validating the Foundry project endpoint...

[Cloud evaluation] Connecting to the Foundry project using Microsoft Entra authentication...
Loading saved run details and checking the project and deployment match...
Using the saved run's sample count; --samples does not change it.
[Polling] Checking the saved cloud run for up to 60 seconds. A local timeout does not cancel the Azure job.
Retrieving the latest cloud run status...
Cloud evaluation: completed
[Report] Saving the cloud run's final status...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\results\cloud-evaluation.json
[Results] Cloud run completed. Downloading individual scored responses...
[Report] Saving 45 evaluated rows before validation...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\results\evaluation-items.json
[Validation] Checking for exactly 45 rows, each with valid numerical scores for coherence, fluency, and relevance...
[Report] All rows passed score validation. Saving the successful evaluation state...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\results\evaluation-state.json
Completed cloud evaluation of 45 synthetic travel questions.
Quality scores are model-judged signals, not guarantees of factual accuracy or safety.

Exit code: 0; outer timeout: False
```

Full logs: [dependency dry-run](results/captured-dependency-precheck.txt) and
[normal command, including dependency output](results/captured-normal.txt).

### 2. Two-model puzzle and contextual follow-up

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --compare-only
```

<details>
<summary>Full captured comparison output</summary>

```text
[Setup] Loading this lab's configuration and primary deployment...
[Mode] Checking the selected option and saved evaluation state...
Mode: --compare-only. Compare two models without starting or resuming cloud evaluation.
[Comparison] Connecting to the models using Microsoft Entra authentication...

[Comparison] Each model receives the same puzzle and a contextual follow-up.
These live model calls may incur inference charges.
Puzzle: I have a fox, a chicken, and a bag of grain to take over a river in a boat. I can take only one at a time. The chicken eats unattended grain and the fox eats an unattended chicken. How can I transport all three safely?

[Comparison 1] Sending the river puzzle to deployment <model-A>...
Puzzle response received. Sending follow-up: Explain your reasoning. The previous response provides the conversation context.

<model-A>:
1. Take the **chicken** across.
2. Return **alone**.
3. Take the **fox** across.
4. Bring the **chicken** back.
5. Take the **grain** across.
6. Return **alone**.
7. Take the **chicken** across again.

Now the fox, chicken, and grain are all across safely.

Follow-up:
The key is that the **chicken must never be left alone with the grain**, and the **fox must never be left alone with the chicken** unless you are there too.

So the chicken has to act as the "shuttle item":

1. **Take the chicken across first.**
   - Left bank: fox + grain - safe, because the fox doesn't eat grain.
   - Right bank: chicken with you - safe.

2. **Return alone.**
   - Left bank: fox + grain + you - safe.
   - Right bank: chicken alone - safe.

3. **Take the fox across.**
   - Left bank: grain alone - safe.
   - Right bank: fox + chicken + you - safe because you are there.

4. **Bring the chicken back.**
   - Left bank: chicken + grain + you - safe because you are there.
   - Right bank: fox alone - safe.

5. **Take the grain across.**
   - Left bank: chicken alone - safe.
   - Right bank: fox + grain + you - safe.

6. **Return alone.**
   - Left bank: chicken + you - safe.
   - Right bank: fox + grain - safe.

7. **Take the chicken across again.**
   - Right bank: fox + chicken + grain + you - all transported safely.

The reason this works is that the fox is never left alone with the chicken, and the chicken is never left alone with the grain.

[Comparison 2] Sending the river puzzle to deployment <model-B>...
Puzzle response received. Sending follow-up: Explain your reasoning. The previous response provides the conversation context.

<model-B>:
Solution (7 one-way crossings):

1. Take the chicken across. (Now other side: chicken. Near side: fox, grain.)
2. Return alone. (Other side: chicken. Near side: fox, grain.)
3. Take the fox across. (Other side: fox, chicken.)
4. Bring the chicken back. (Other side: fox. Near side: chicken, grain.)
5. Take the grain across. (Other side: fox, grain. Near side: chicken.)
6. Return alone. (Other side: fox, grain. Near side: chicken.)
7. Take the chicken across. (Other side: fox, chicken, grain - done.)

At no point are the chicken and grain left alone unattended, nor the fox and chicken, so all three arrive safely.

Follow-up:
Start by listing the dangerous pairings: chicken + grain (chicken will eat the grain) and fox + chicken (fox will eat the chicken). Any time those two are left alone on the same bank without you, something gets eaten. The boat can carry you plus exactly one of the three.

Key observation: the chicken is the only item that is dangerous with either of the other two. That forces the first move: if you take the fox first, the chicken and grain are left together and the grain is eaten; if you take the grain first, the fox and chicken are left together and the chicken is eaten. So you must take the chicken across on the first trip.

Now reason through what to do after that first trip:

1. You take the chicken to the far bank and leave it there. The near bank now has fox + grain (which is safe).
2. You must return to the near bank to get something else. Returning alone is safe (you can't leave the chicken alone with something it eats while you're gone because the near bank is safe).
3. If you now take the fox across, you cannot leave fox and chicken together unattended on the far bank, so after you bring the fox over you must bring the chicken back with you. (If instead you took the grain next, you'd leave chicken and fox together on opposite banks while you return, which is unsafe.)
4. So bring the fox across, then bring the chicken back to the near bank. At that point the far bank has only the fox, the near bank has chicken + grain (safe).
5. Take the grain across and leave it with the fox (fox doesn't eat grain). Return alone to the near bank.
6. Finally, take the chicken across.

That sequence avoids leaving any dangerous pair alone at any time. In short: chicken first, fox next but bring chicken back, grain next, then chicken - which is the step-by-step plan I gave.
Comparison finished. These answers and timings are not controlled catalog benchmarks.
[Report] Saving the two-model comparison results...
Saved local report: <repository-root>\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\results\model-comparison.json

Comparison-only completed successfully. No cloud evaluation was started or resumed; saved cloud state was left unchanged.

Exit code: 0; outer timeout: False
```

</details>

| Model | Puzzle + follow-up elapsed seconds | Puzzle total tokens | Follow-up total tokens |
|---|---|---|---|
| A | 10.49 | 235 | 501 |
| B | 11.26 | 538 | 1,015 |

Both initial answers give a safe seven-crossing sequence. **Model B's follow-up
contains a reasoning error:** its parenthetical calls the alternative grain
ordering unsafe because the fox and chicken would be on opposite banks.
Opposite banks are not the dangerous condition; taking grain after the first
chicken trip is also valid if the chicken is brought back before returning
for the fox. The original error is retained above, not silently corrected.

These timings/tokens are single-run observations, not leaderboard performance,
retail cost, or an accuracy score. The travel evaluation below does not grade
these puzzle answers.

Full evidence: [UTF-8 console transcript](results/captured-compare.txt) and
[redacted comparison answers, follow-ups, and usage](results/captured-model-comparison.json).
The previous private comparison report was preserved as
`results\model-comparison-before-capture.json` before the documented command
replaced its intended output file.

### 3. Explicit resume and verified evaluation results

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --resume --timeout 60
```

The explicit-resume run also exited `0`, printed `Cloud evaluation: completed`
and `Completed cloud evaluation of 45 synthetic travel questions.`, and saved
the three cloud reports. It printed:

```text
Mode: --resume. Reusing the saved run; skipping comparison and new job submission.
```

The [full resume transcript](results/captured-resume.txt) records every stage.
Both retrievals matched the saved evaluation/run IDs and retained sample
count; comparison-only left the cloud state alone.

| Check | Captured result |
|---|---|
| Cloud status / saved success | `completed` / `true` |
| Requested questions / distinct queries | **45 / 45** |
| Service total / downloaded distinct output items | **45 / 45** |
| Completed rows containing a query and response | **45** |
| Service passed / failed / errored / skipped | **45 / 0 / 0 / 0** |
| Rows with all three finite numerical quality scores | **45** |
| Missing metrics / null criterion pass flags | **0 / 0** |

| Criterion | Scored rows | Mean | Minimum | Maximum | Score distribution |
|---|---|---|---|---|---|
| Coherence | 45 | 5.000 | 5 | 5 | 45 at 5 |
| Fluency | 45 | 4.867 | 4 | 5 | 6 at 4; 39 at 5 |
| Relevance | 45 | 5.000 | 5 | 5 | 45 at 5 |

All 135 criterion results had status `completed` and `passed: true`.
These are service-reported threshold results and model-judged quality signals,
**not 45 independently proven correct or safe answers**. No Agent or Safety
evaluator was added. The earlier validation section remains historical
evidence; this table describes the artifacts retrieved in this capture.

Exports: [verified counts and metrics](results/captured-evaluation-summary.json)
and [all 45 redacted question/response/result rows](results/captured-evaluation-items.json).
The normal client also retained its private state, raw cloud report, and
individual items in the documented `results` files.

### 4. Help, focused test failure, and scope limits

```powershell
.\run-lab.ps1 .\1-Develop_GenAI_Apps_with_Foundry\02-model-catalog-evaluation\ evaluate-models.py --help
```

Help exited `0` and listed all documented options:
[captured help output](results/captured-help.txt).

Only the relevant existing `EvaluationTests` class was selected, with the
tests directory on the child process's `PYTHONPATH`:

```powershell
$env:PYTHONPATH = (Resolve-Path .\1-Develop_GenAI_Apps_with_Foundry\tests).Path
.\.labenv\Scripts\python.exe -m unittest -v test_foundry_labs.EvaluationTests
```

It exited **1 before any test ran**. The shared test module imports a missing
legacy fine-tuning implementation during discovery:

```text
  File "<repository-root>\1-Develop_GenAI_Apps_with_Foundry\tests\test_foundry_labs.py", line 31, in <module>
    tuning = module("tuning", "05-optimize-fine-tuning/fine-tune.py")
```

The resulting error was `FileNotFoundError` for
`05-optimize-fine-tuning\fine-tune.py`; the
[full failed-test transcript](results/captured-tests.txt) is preserved.
This is a shared-test discovery blocker, not a successful regression suite.
No shared test or sibling implementation was changed to bypass it.

The live application commands all succeeded; no timeout or HTTP 429 was
reported by those runs. Existing SDK retry settings were unchanged.
`--reset` and `--samples 1` were deliberately **not** executed: a completed
45-question run already existed, and reset would create another billable
evaluation rather than recover it. Portal leaderboards and analysis UI were
not automated. Existing cloud evaluation objects were left intact.

Checks confirmed exact puzzle/follow-up text against the saved JSON, the
45 unique question/output pairs and all score shapes, matching saved IDs,
and unchanged `.env`, implementation, requirements, shared launcher, and
shared helper: [captured checks](results/captured-checks.txt).
No ToC, shared-runtime edit, commit, or push was made.

### 5. Scoped execution of the unchanged EvaluationTests

The standard discovery attempt above still exited **1 with zero tests run**.
A separate, scoped loader then executed the existing **17 `EvaluationTests`**:
**17 passed, zero failures/errors/skips, exit 0**. It selected the original
imports, `ROOT`/path setup, `module` and `response` helpers, the `evaluation`
module assignment, and the unchanged class directly from the shared test
file's AST. Unrelated implementation assignments were not executed.

This is not a repaired full-suite discovery run. The tests' original mocks
were retained; their reset/submission cases made no model or cloud requests.
Temporary test files were confined to this lab and removed. Class AST and
test/implementation/configuration hashes were unchanged.

<details>
<summary>Actual scoped command, including transcript capture and preservation checks</summary>

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; @'
import ast
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import unittest

root = Path.cwd()
lab = root / '1-Develop_GenAI_Apps_with_Foundry' / '02-model-catalog-evaluation'
source = lab.parent / 'tests' / 'test_foundry_labs.py'
protected = [source, lab / 'evaluate-models.py', lab / '.env', lab / 'requirements.txt', lab.parent / 'lab_common.py', root / 'run-lab.ps1']
before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
readme_before = hashlib.sha256((lab / 'README.md').read_bytes()).hexdigest()
tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
body = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        body.append(node)
    elif isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'ROOT', 'evaluation'} for target in node.targets):
        body.append(node)
    elif isinstance(node, ast.Expr) and ast.unparse(node).startswith('sys.path.insert('):
        body.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in {'module', 'response'}:
        body.append(node)
    elif isinstance(node, ast.ClassDef) and node.name == 'EvaluationTests':
        body.append(node)
class_nodes = [node for node in body if isinstance(node, ast.ClassDef)]
assert len(class_nodes) == 1 and class_nodes[0].name == 'EvaluationTests'
original_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'EvaluationTests')
assert ast.dump(class_nodes[0], include_attributes=True) == ast.dump(original_class, include_attributes=True)
work = lab / '.scoped-evaluation-work'
work.mkdir()
old_tempdir = tempfile.tempdir
tempfile.tempdir = str(work)
output = io.StringIO()
try:
    with redirect_stdout(output), redirect_stderr(output):
        namespace = {'__name__': 'scoped_evaluation_tests', '__file__': str(source)}
        exec(compile(ast.Module(body=body, type_ignores=tree.type_ignores), str(source), 'exec'), namespace)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['EvaluationTests'])
        expected = suite.countTestCases()
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
finally:
    tempfile.tempdir = old_tempdir
    if any(work.iterdir()):
        raise RuntimeError('Scoped test scratch directory unexpectedly contains files; not deleting them blindly.')
    work.rmdir()
assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in before.items())
assert hashlib.sha256((lab / 'README.md').read_bytes()).hexdigest() == readme_before
code = 0 if result.wasSuccessful() and result.testsRun == expected else 1
text = output.getvalue()
for actual, replacement in ((str(root).replace('\\', '\\\\'), '<repository-root>'), (str(root), '<repository-root>'), (os.environ.get('USERPROFILE', ''), '<user-home>')):
    if actual:
        text = text.replace(actual, replacement)
text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '<contact>', text)
text += f'\nScoped selected/executed tests: {expected}/{result.testsRun}; failures: {len(result.failures)}; errors: {len(result.errors)}; skipped: {len(result.skipped)}\n'
text += 'Unchanged EvaluationTests AST and original test/source/configuration hashes verified. No model requests or shared-file edits. Scoped scratch directory removed.\n'
text += f'Exit code: {code}\n'
(lab / 'results' / 'captured-scoped-tests.txt').write_text(text, encoding='utf-8')
(lab / 'results' / 'captured-scoped-test-summary.json').write_text(json.dumps({'selector': 'EvaluationTests', 'selected': expected, 'executed': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'exit_code': code, 'unchanged_test_class_ast': True, 'shared_test_and_implementation_configuration_unchanged': True, 'standard_discovery_executed_tests': 0, 'standard_discovery_exit_code': 1, 'readme_before_followup_sha256': readme_before}, indent=2) + '\n', encoding='utf-8')
print(text, end='')
raise SystemExit(code)
'@ | & '.\.labenv\Scripts\python.exe' -
```

</details>

Captured result tail:

```text
----------------------------------------------------------------------
Ran 17 tests in 0.300s

OK

Scoped selected/executed tests: 17/17; failures: 0; errors: 0; skipped: 0
Unchanged EvaluationTests AST and original test/source/configuration hashes verified. No model requests or shared-file edits. Scoped scratch directory removed.
Exit code: 0
```

The [full scoped-test transcript](results/captured-scoped-tests.txt) records
every test name and its actual output. The
[scoped-test summary](results/captured-scoped-test-summary.json) retains both
the successful scoped counts and the original failed discovery's zero-test
count. No shared test, dependency, runtime, or other lab was edited.
