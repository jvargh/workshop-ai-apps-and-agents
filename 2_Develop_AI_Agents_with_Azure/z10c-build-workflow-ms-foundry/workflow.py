import json
import math
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def print_workflow_output(output_text):
    decoder = json.JSONDecoder()
    tickets = []
    position = 0
    while position < len(output_text):
        start = output_text.find("{", position)
        if start < 0:
            break
        try:
            ticket, end = decoder.raw_decode(output_text, start)
        except json.JSONDecodeError:
            position = start + 1
            continue
        position = end
        if (
            isinstance(ticket, dict)
            and isinstance(ticket.get("category"), str)
            and isinstance(ticket.get("customer_issue"), str)
            and isinstance(ticket.get("confidence"), (int, float))
            and not isinstance(ticket["confidence"], bool)
            and math.isfinite(ticket["confidence"])
            and 0 <= ticket["confidence"] <= 1
        ):
            tickets.append((start, end, ticket))

    if not tickets:
        print(output_text)
        return 0

    if output_text[:tickets[0][0]].strip():
        print(output_text[:tickets[0][0]].strip())
    for index, (_, end, ticket) in enumerate(tickets):
        next_start = tickets[index + 1][0] if index + 1 < len(tickets) else len(output_text)
        response_text = output_text[end:next_start]

        print("\n" + "=" * 80)
        print(f"Ticket {index + 1}: {ticket['category']} ({ticket['confidence']:.0%} confidence)")
        print("-" * 80)
        print(f"Issue: {ticket['customer_issue']}")
        print("\nResponse:")
        print(response_text.strip())
    print("=" * 80 + "\n")
    return len(tickets)


def run_workflow(openai_client, workflow_name):
    conversation = None
    try:
        print("[3/6] Creating a temporary Foundry conversation...", flush=True)
        conversation = openai_client.conversations.create()
        print(f"Created conversation (id: {conversation.id})", flush=True)
        print("[4/6] Sending initial input: Start. Waiting for the remote workflow...", flush=True)
        completed = False
        with openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": workflow_name, "type": "agent_reference"}},
            input="Start",
            stream=True,
        ) as stream:
            for event in stream:
                if event.type == "response.created":
                    print("[Workflow] Response accepted; remote steps are running.", flush=True)
                elif event.type in ("response.failed", "response.incomplete", "error"):
                    raise RuntimeError(f"Workflow stream reported {event.type}: {event}")
                elif event.type == "response.completed":
                    print("[5/6] Response completed; retrieving and formatting output...", flush=True)
                    response = openai_client.responses.retrieve(event.response.id)
                    if response.status != "completed":
                        raise RuntimeError(f"Retrieved response status is {response.status}, not completed.")
                    if not response.output_text or not response.output_text.strip():
                        raise RuntimeError("The completed workflow returned no text output.")
                    count = print_workflow_output(response.output_text)
                    print(f"Formatted ticket records: {count}", flush=True)
                    completed = True
        if not completed:
            raise RuntimeError("Workflow stream ended without a response.completed event.")
    finally:
        run_failed = sys.exc_info()[0] is not None
        if conversation is not None:
            print("[6/6] Deleting this run's conversation...", flush=True)
            try:
                openai_client.conversations.delete(conversation_id=conversation.id)
                print("Conversation deleted", flush=True)
            except Exception as error:
                print(f"Conversation cleanup failed (id: {conversation.id}): {error}", file=sys.stderr)
                if not run_failed:
                    raise


def main():
    try:
        print("[1/6] Loading this lab's configuration...", flush=True)
        load_dotenv(Path(__file__).with_name(".env"))
        endpoint = os.getenv("PROJECT_ENDPOINT", "").strip()
        if not endpoint or "<" in endpoint or ">" in endpoint:
            raise ValueError("Set PROJECT_ENDPOINT to your full Foundry project URL in this lab's .env.")
        workflow_name = os.getenv("WORKFLOW_NAME", "ContosoPay-Customer-Support-Triage").strip()
        if not workflow_name or "<" in workflow_name or ">" in workflow_name:
            raise ValueError("Set WORKFLOW_NAME to an existing published workflow name, or omit the override.")

        print("[2/6] Opening Azure project and Responses clients...", flush=True)
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            run_workflow(openai_client, workflow_name)
        print("Workflow run finished; SDK clients and credential closed.", flush=True)
        return 0
    except KeyboardInterrupt:
        print("Workflow run interrupted; cleanup was attempted for any created conversation.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Workflow run failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
