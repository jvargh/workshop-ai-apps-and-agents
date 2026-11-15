import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import completed_text, load_config, model_client, required, run, save_report

PUZZLE = (
    "I have a fox, a chicken, and a bag of grain to take over a river in a boat. "
    "I can take only one at a time. The chicken eats unattended grain and the "
    "fox eats an unattended chicken. How can I transport all three safely?"
)
TRAVEL_PROMPT = (
    "You are a helpful travel assistant that provides accurate, detailed, and "
    "practical travel advice to help users plan their trips."
)


def compare_models(client, deployments):
    print("\n[Comparison] Each model receives the same puzzle and a contextual follow-up.", flush=True)
    print("These live model calls may incur inference charges.", flush=True)
    print(f"Puzzle: {PUZZLE}", flush=True)
    results = []
    for number, model in enumerate(deployments, 1):
        print(f"\n[Comparison {number}] Sending the river puzzle to deployment {model}...", flush=True)
        started = time.monotonic()
        first = client.responses.create(model=model, input=PUZZLE)
        first_text = completed_text(first)
        print(
            "Puzzle response received. Sending follow-up: Explain your reasoning. "
            "The previous response provides the conversation context.",
            flush=True,
        )
        second = client.responses.create(
            model=model, input="Explain your reasoning.", previous_response_id=first.id
        )
        second_text = completed_text(second)
        results.append({
            "deployment": model, "answer": first_text, "follow_up": second_text,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "usage": [first.usage.model_dump(), second.usage.model_dump()],
        })
        print(f"\n{model}:\n{first_text}\n\nFollow-up:\n{second_text}", flush=True)
    print("Comparison finished. These answers and timings are not controlled catalog benchmarks.", flush=True)
    return results


def evaluation_definition(model):
    return {
        "name": "travel-assistant-eval",
        "data_source_config": {
            "type": "azure_ai_source", "scenario": "synthetic_data_gen_preview"
        },
        "testing_criteria": [{
            "type": "azure_ai_evaluator",
            "name": name,
            "evaluator_name": f"builtin.{name}",
            "initialization_parameters": {"model": model},
            "data_mapping": {
                "query": "{{item.query}}", "response": "{{sample.output_text}}"
            },
        } for name in ("coherence", "fluency", "relevance")],
    }


def synthetic_source(model, samples, dataset_name):
    return {
        "type": "azure_ai_synthetic_data_gen_preview",
        "item_generation_params": {
            "type": "synthetic_data_gen_preview",
            "samples_count": samples,
            "prompt": (
                "Create varied travel-related questions. Include safe content-safety "
                "and security scenarios such as protecting travel documents and "
                "recognizing booking scams. Use no personal data, offensive text, "
                "or instructions for wrongdoing."
            ),
            "model_deployment_name": model,
            "output_dataset_name": dataset_name,
        },
        "target": {"type": "azure_ai_model", "model": model},
        "input_messages": {
            "type": "template",
            "template": [{
                "type": "message", "role": "system",
                "content": {"type": "input_text", "text": TRAVEL_PROMPT},
            }],
        },
    }


def validate_evaluation_items(items, expected_count):
    if len(items) != expected_count:
        raise RuntimeError(f"Expected {expected_count} evaluated rows; received {len(items)}.")
    expected = {"coherence", "fluency", "relevance"}
    for number, item in enumerate(items, 1):
        data = item.model_dump()
        results = data.get("results") or []
        if data.get("status") == "error" or len(results) != len(expected) or {
            result.get("name") for result in results
        } != expected:
            raise RuntimeError(f"Evaluated row {number} is errored or missing required quality metrics.")
        for result in results:
            score = result.get("score")
            if result.get("error") or type(score) not in (int, float) or not math.isfinite(score):
                raise RuntimeError(f"Evaluated row {number} has no valid score for {result['name']}.")


def archive_reports(folder):
    results = folder / "results"
    names = (
        "model-comparison.json", "cloud-evaluation.json", "evaluation-items.json",
        "evaluation-progress.json", "evaluation-state.json",
    )
    files = [results / name for name in names if (results / name).exists()]
    if not files:
        print("No previous local evaluation reports to archive.", flush=True)
        return None
    if any(not path.is_file() for path in files):
        raise ValueError("Cannot reset: an evaluation report path is not a file.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = results / "archive" / stamp
    archive.mkdir(parents=True)
    for path in files:
        path.rename(archive / path.name)
    print(f"Archived previous evaluation reports: {archive}", flush=True)
    return archive


def main():
    parser = argparse.ArgumentParser(description="Compare models and run cloud synthetic evaluation.")
    parser.add_argument(
        "--compare-only", action="store_true",
        help="Run only the two-model puzzle comparison; leave saved cloud evaluation state untouched.",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Poll or retrieve the saved cloud run without repeating comparison or submitting a new job.",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Archive local evaluation reports and submit a fresh, billable cloud run.",
    )
    parser.add_argument("--samples", type=int, default=45, help="Questions for a new run (1..45; default 45).")
    parser.add_argument("--timeout", type=int, default=1200, help="Polling timeout in seconds (default 1200).")
    args = parser.parse_args()
    if not 1 <= args.samples <= 45 or args.timeout <= 0:
        raise ValueError("--samples must be 1..45 and --timeout must be positive.")
    if sum((args.resume, args.reset, args.compare_only)) > 1:
        raise ValueError("--resume, --reset, and --compare-only cannot be combined.")
    print("[Setup] Loading this lab's configuration and primary deployment...", flush=True)
    folder, endpoint, model = load_config(__file__)
    state_path = folder / "results" / "evaluation-state.json"
    print("[Mode] Checking the selected option and saved evaluation state...", flush=True)
    resume = args.resume or (state_path.exists() and not args.reset and not args.compare_only)
    if resume and not state_path.is_file():
        raise ValueError("No saved evaluation found. Run without --resume to start a new evaluation.")
    if resume and not args.resume:
        print("Saved evaluation found; automatically resuming it. Use --reset to start fresh.", flush=True)
    if resume:
        mode = "--resume" if args.resume else "automatic resume"
        print(f"Mode: {mode}. Reusing the saved run; skipping comparison and new job submission.", flush=True)
        print("An existing active cloud run may continue incurring charges.", flush=True)
    elif args.compare_only:
        print("Mode: --compare-only. Compare two models without starting or resuming cloud evaluation.", flush=True)
    elif args.reset:
        print("Mode: --reset. Archive local reports, repeat comparison, and start a fresh cloud run.", flush=True)
    else:
        print("Mode: new evaluation. No saved state found; compare models and submit a cloud run.", flush=True)
    if not args.compare_only:
        print("[Setup] Validating the Foundry project endpoint...", flush=True)
        project = required("PROJECT_ENDPOINT").rstrip("/")
        if "/api/projects/" not in project:
            raise ValueError("PROJECT_ENDPOINT must include /api/projects/<project>.")
        if not project.startswith("https://") or "?" in project or "#" in project:
            raise ValueError("PROJECT_ENDPOINT must be an HTTPS project root.")
    if not resume:
        comparison_model = required("COMPARE_DEPLOYMENT")
        if comparison_model == model:
            raise ValueError("COMPARE_DEPLOYMENT must be a different deployment.")
        if args.reset:
            print(
                "Reset requested: starting a new billable evaluation. "
                "Existing Azure evaluations are not deleted or canceled and may still incur charges.",
                flush=True,
            )
            print("[Archive] Moving previous local evaluation reports into a timestamped archive...", flush=True)
            archive_reports(folder)
        print("[Comparison] Connecting to the models using Microsoft Entra authentication...", flush=True)
        with model_client(endpoint) as client:
            comparison = compare_models(client, [model, comparison_model])
        print("[Report] Saving the two-model comparison results...", flush=True)
        save_report(folder, "model-comparison.json", {
            "success": True, "scope": "Two-model river puzzle with follow-up context",
            "models": comparison, "catalog_benchmarks_measured": False,
        })
        if args.compare_only:
            print(
                "\nComparison-only completed successfully. "
                "No cloud evaluation was started or resumed; saved cloud state was left unchanged.",
                flush=True,
            )
            return

    print("\n[Cloud evaluation] Connecting to the Foundry project using Microsoft Entra authentication...", flush=True)
    with model_client(project + "/openai/v1/") as client:
        if resume:
            print("Loading saved run details and checking the project and deployment match...", flush=True)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state["project"] != project or state["deployment"] != model:
                raise ValueError("Saved evaluation belongs to a different project/deployment.")
            print("Using the saved run's sample count; --samples does not change it.", flush=True)
        else:
            print(
                "Creating an evaluation for coherence, fluency, and relevance. "
                "Synthetic generation and model-based scoring incur charges.",
                flush=True,
            )
            evaluation = client.evals.create(**evaluation_definition(model))
            state = {
                "project": project, "deployment": model,
                "eval_id": evaluation.id, "samples": args.samples,
                "success": False, "status": "evaluation_created",
            }
            print("[Report] Saving the evaluation ID before submitting the cloud run...", flush=True)
            save_report(folder, state_path.name, state)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            print(
                f"Submitting a new billable cloud run for {args.samples} synthetic travel questions. "
                f"Deployment {model} generates questions, answers them, and judges quality.",
                flush=True,
            )
            job = client.evals.runs.create(
                evaluation.id,
                name=f"travel-assistant-eval-{stamp}",
                data_source=synthetic_source(model, args.samples, f"travel-questions-{stamp}"),
            )
            state.update({"run_id": job.id, "status": job.status})
            print("[Report] Saving the run ID so this evaluation can be resumed...", flush=True)
            save_report(folder, state_path.name, state)
        if "run_id" not in state:
            raise RuntimeError(
                "Evaluation was created but run submission did not finish. Inspect the "
                "saved eval_id in Foundry before starting another run."
            )
        print(
            f"[Polling] Checking the saved cloud run for up to {args.timeout} seconds. "
            "A local timeout does not cancel the Azure job.",
            flush=True,
        )
        deadline = time.monotonic() + args.timeout
        while True:
            print("Retrieving the latest cloud run status...", flush=True)
            response = client.evals.runs.with_raw_response.retrieve(
                state["run_id"], eval_id=state["eval_id"]
            )
            job = response.parse()
            job_report = response.http_response.json()
            state["status"] = job.status
            print(f"Cloud evaluation: {job.status}", flush=True)
            if job.status in ("completed", "failed", "canceled", "cancelled"):
                break
            if job.status not in ("queued", "in_progress", "running"):
                raise RuntimeError(f"Unexpected evaluation status: {job.status}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print(
                    "[Recovery] Polling timed out. Saving the latest status and resumable state; "
                    "the cloud run is not canceled.",
                    flush=True,
                )
                save_report(folder, "cloud-evaluation.json", job_report)
                save_report(folder, state_path.name, state)
                raise TimeoutError("Cloud run is still active; rerun with --resume.")
            interval = min(15, remaining)
            print(f"Cloud run is still active; checking again in {interval:g} seconds...", flush=True)
            time.sleep(interval)

        print("[Report] Saving the cloud run's final status...", flush=True)
        save_report(folder, "cloud-evaluation.json", job_report)
        if job.status != "completed":
            save_report(folder, state_path.name, state)
            raise RuntimeError(f"Cloud evaluation did not complete: {job_report}")
        print("[Results] Cloud run completed. Downloading individual scored responses...", flush=True)
        items = list(client.evals.runs.output_items.list(
            state["run_id"], eval_id=state["eval_id"], limit=100,
        ))
        print(f"[Report] Saving {len(items)} evaluated rows before validation...", flush=True)
        save_report(folder, "evaluation-items.json", {
            "items": [item.model_dump() for item in items]
        })
        print(
            f"[Validation] Checking for exactly {state['samples']} rows, each with valid numerical "
            "scores for coherence, fluency, and relevance...",
            flush=True,
        )
        validate_evaluation_items(items, state["samples"])
        state["success"] = True
        print("[Report] All rows passed score validation. Saving the successful evaluation state...", flush=True)
        save_report(folder, state_path.name, state)
        print(f"Completed cloud evaluation of {len(items)} synthetic travel questions.", flush=True)
        print("Quality scores are model-judged signals, not guarantees of factual accuracy or safety.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
