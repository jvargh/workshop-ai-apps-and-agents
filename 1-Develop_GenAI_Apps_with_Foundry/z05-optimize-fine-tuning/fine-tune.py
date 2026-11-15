import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import completed_text, load_config, model_client, required, run, save_report

TRAVEL_INSTRUCTIONS = (
    "You are an AI travel assistant that helps people plan their trips. Your objective "
    "is to offer support for travel-related inquiries, such as visa requirements, "
    "weather forecasts, local attractions, and cultural norms. You should not provide "
    "any hotel, flight, rental car or restaurant recommendations. Ask engaging questions "
    "to help someone plan their trip and think about what they want to do on their holiday."
)
QUESTIONS = [
    "Where in Rome should I stay?",
    "I'm mostly there for the food. Where should I stay to be within walking distance of affordable restaurants?",
    "What are some local delicacies I should try?",
    "When is the best time of year to visit in terms of the weather?",
    "What's the best way to get around the city?",
]


def validate_dataset(path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("Training JSONL must be UTF-8 without a BOM.")
    rows = []
    prompts = set()
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"Blank training row at line {number}.")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Line {number}: expected a JSON object.")
        messages = row.get("messages")
        if not isinstance(messages, list) or not all(
            isinstance(item, dict) for item in messages
        ) or [
            item.get("role") for item in messages
        ] != ["system", "user", "assistant"]:
            raise ValueError(f"Line {number}: expected system/user/assistant messages.")
        if any(not isinstance(item.get("content"), str) or not item["content"].strip()
               for item in messages):
            raise ValueError(f"Line {number}: message content must be nonempty text.")
        prompt = messages[1]["content"].strip().casefold()
        if prompt in prompts:
            raise ValueError(f"Line {number}: duplicate user prompt.")
        prompts.add(prompt)
        rows.append(row)
    if len(rows) < 10:
        raise ValueError("Supervised fine-tuning requires at least ten training examples.")
    return {
        "success": True, "scope": "Local SFT format validation only",
        "rows": len(rows), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "training_submitted": False, "fine_tuned_deployment_validated": False,
    }


def baseline(client, model):
    variants = (
        "You are a helpful assistant.",
        "You are an AI assistant that helps people plan their travel.",
        TRAVEL_INSTRUCTIONS,
    )
    total = len(variants) + len(QUESTIONS)
    print(f"\n[Baseline] Testing deployment {model} with {total} live model requests.", flush=True)
    print("The first three requests vary the instructions; the Rome questions form a separate conversation.", flush=True)
    results = []
    for number, instructions in enumerate(variants, 1):
        print(f"\n[Prompt {number}/{total}] Instruction experiment; independent request.", flush=True)
        print(f"Instructions: {instructions}", flush=True)
        print("Prompt: What can you do?", flush=True)
        print("[Request] Sending prompt using Responses. Waiting for the complete response...", flush=True)
        response = client.responses.create(
            model=model, instructions=instructions, input="What can you do?"
        )
        answer = completed_text(response)
        results.append({
            "instructions": instructions, "query": "What can you do?",
            "answer": answer, "usage": response.usage.model_dump(),
        })
        print(f"[Response] Model answer:\n{answer}", flush=True)
    print("\n[History] Starting a new Rome conversation with the detailed travel instructions.", flush=True)
    previous_id = None
    for number, query in enumerate(QUESTIONS, len(variants) + 1):
        print(f"\n[Prompt {number}/{total}] {query}", flush=True)
        if previous_id is None:
            print("[History] First Rome question; no previous response context.", flush=True)
        else:
            print("[History] Reusing the previous response context for this follow-up.", flush=True)
        print("[Request] Sending travel question. Waiting for the complete response...", flush=True)
        response = client.responses.create(
            model=model, instructions=TRAVEL_INSTRUCTIONS,
            input=query, previous_response_id=previous_id,
        )
        answer = completed_text(response)
        results.append({"instructions": TRAVEL_INSTRUCTIONS, "query": query,
                        "answer": answer, "usage": response.usage.model_dump()})
        previous_id = response.id
        print(f"[Response] {model} / {query}\n{answer}", flush=True)
    print(
        f"[Baseline] Completed all {total} requests for {model}. "
        "Review the answers; successful requests do not prove instruction adherence.",
        flush=True,
    )
    return results


def chat(client, model):
    results = []
    previous_id = None
    print(f"\n[Chat] Using base deployment {model} with Responses and conversation history.", flush=True)
    print(f"Instructions applied to every request: {TRAVEL_INSTRUCTIONS}", flush=True)
    print("Travel assistant ready. Enter a travel question, or type quit to exit.", flush=True)
    while True:
        try:
            query = input("\nYou: ").strip()
        except EOFError:
            print("\n[Input] End of input received. Ending the travel conversation.", flush=True)
            break
        if query.lower() == "quit":
            print("[Input] Quit requested. Ending the travel conversation.", flush=True)
            break
        if not query:
            print("Please enter a travel question. No model request was sent.", flush=True)
            continue
        if previous_id is None:
            print("[History] First question; no previous response context.", flush=True)
        else:
            print("[History] Reusing the previous response context for this follow-up.", flush=True)
        print(
            f"[Request {len(results) + 1}] Sending travel question. Waiting for the complete response...",
            flush=True,
        )
        response = client.responses.create(
            model=model, instructions=TRAVEL_INSTRUCTIONS,
            input=query, previous_response_id=previous_id,
        )
        answer = completed_text(response)
        results.append({
            "instructions": TRAVEL_INSTRUCTIONS, "query": query,
            "answer": answer, "usage": response.usage.model_dump(),
        })
        previous_id = response.id
        print(f"\nAssistant: {answer}", flush=True)
        print("[History] Context updated for the next question in this session.", flush=True)
    print(f"[Chat] Conversation ended after {len(results)} answered question(s).", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate SFT data, chat, and compare deployed models.")
    parser.add_argument(
        "--mode", choices=["validate", "baseline", "compare", "chat"], default="validate",
        help="validate: offline data checks (default); baseline: eight live prompts; "
        "chat: interactive travel questions; compare: eight prompts per base/trained deployment.",
    )
    args = parser.parse_args()
    print(f"[Mode] {args.mode}. This script does not submit training jobs or create deployments.", flush=True)
    folder = Path(__file__).resolve().parent
    if args.mode != "chat":
        print(
            "[Dataset] Checking the local JSONL file: UTF-8 without a BOM, message roles, "
            "nonempty text, unique prompts, and at least ten examples...",
            flush=True,
        )
        report = validate_dataset(folder / "data" / "travel-finetune-hotel.jsonl")
        print(f"[Dataset] Format checks passed for {report['rows']} examples; no model has been trained.", flush=True)
        print("[Report] Saving the local dataset-validation report...", flush=True)
        save_report(folder, "dataset-validation.json", report)
        if args.mode == "validate":
            print(f"Validated {report['rows']} official SFT examples. No training was submitted.", flush=True)
            return
    else:
        print("[Dataset] Skipping dataset validation; chat uses the existing base deployment only.", flush=True)
    print("[Setup] Loading the endpoint and base deployment from this lab's configuration...", flush=True)
    _, endpoint, model = load_config(__file__)
    print(f"Base deployment: {model}", flush=True)
    if args.mode == "compare":
        print("[Comparison] Checking that a separate, already trained deployment is configured...", flush=True)
    fine_tuned = required("FINE_TUNED_DEPLOYMENT") if args.mode == "compare" else None
    if fine_tuned == model:
        raise ValueError("FINE_TUNED_DEPLOYMENT must differ from the base deployment.")
    print("Live model calls may incur inference charges; no training will be started.", flush=True)
    print("[Connect] Preparing the Responses client with Microsoft Entra authentication...", flush=True)
    with model_client(endpoint) as client:
        base_responses = chat(client, model) if args.mode == "chat" else baseline(client, model)
        if args.mode == "chat" and not base_responses:
            print("No questions submitted; no chat report saved.", flush=True)
            print("[Cleanup] Closing the model client and Azure credential...", flush=True)
            return
        result = {
            "success": True,
            "scope": "Interactive travel assistant" if args.mode == "chat" else "Live prompt-engineering baseline",
            "base_deployment": model, "base_responses": base_responses,
            "training_submitted": False, "fine_tuned_deployment_validated": False,
        }
        if fine_tuned:
            print(
                f"\n[Comparison] Repeating the same eight prompts against {fine_tuned}. "
                "The script trusts your deployment setting; it does not verify training lineage.",
                flush=True,
            )
            result.update({
                "scope": "Live base versus separately deployed fine-tuned model",
                "fine_tuned_deployment": fine_tuned,
                "fine_tuned_responses": baseline(client, fine_tuned),
                "fine_tuned_deployment_validated": True,
            })
        print(f"[Report] Saving {args.mode} results, including answers, instructions, and token usage...", flush=True)
        save_report(folder, f"{args.mode}.json", result)
        print("[Cleanup] Closing the model client and Azure credential...", flush=True)
    print(f"[Complete] {args.mode} finished and its report was saved. No training was submitted.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
