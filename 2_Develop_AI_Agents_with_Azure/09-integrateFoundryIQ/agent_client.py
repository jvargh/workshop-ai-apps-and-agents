import json
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def show_tool_activity(response):
    for item in response.output:
        if item.type == "mcp_list_tools":
            if item.error:
                raise RuntimeError(f"Knowledge-tool discovery failed: {item.error}")
            print(f"[Tools] Discovered {len(item.tools)} tools from {item.server_label}.", flush=True)
        elif item.type == "mcp_call":
            if item.error or item.status != "completed":
                raise RuntimeError(f"Knowledge tool did not complete: {item.name}; {item.status}; {item.error}")
            print(f"[Knowledge] Completed MCP call: {item.server_label} / {item.name}", flush=True)


def show_sources(response):
    seen: set[tuple[str, str]] = set()
    for item in response.output:
        if item.type != "message":
            continue
        for content in item.content:
            if content.type != "output_text":
                continue
            for annotation in content.annotations:
                if annotation.type == "url_citation":
                    key = ("url", annotation.url)
                    source = (
                        f"{annotation.title}: {annotation.url}"
                        if annotation.title and annotation.title != annotation.url
                        else annotation.url
                    )
                elif annotation.type == "file_citation":
                    key = ("file", annotation.file_id)
                    source = f"{annotation.filename} (file ID: {annotation.file_id})"
                else:
                    continue
                if key not in seen:
                    seen.add(key)
                    print(f"[Source] {source}", flush=True)
    if not seen:
        print("[Sources] No separate URL/file citation annotations were returned. Review any references in the answer.", flush=True)


def send_message_to_agent(user_message, client, agent_name, conversation_id, history):
    print("[Conversation] Adding your question to the existing cloud conversation...", flush=True)
    client.conversations.items.create(
        conversation_id=conversation_id,
        items=[{"type": "message", "role": "user", "content": user_message}],
    )
    history.append({"role": "user", "content": user_message})
    print("[Request] Asking the agent to answer or request a knowledge lookup...", flush=True)
    response = client.responses.create(
        conversation=conversation_id, input="",
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    )
    while True:
        if response.status != "completed":
            raise RuntimeError(f"Agent response did not complete: {response.status}; {response.error}")
        show_tool_activity(response)
        requests = [item for item in response.output if item.type == "mcp_approval_request"]
        if not requests:
            break
        decisions = []
        for request in requests:
            if not request.id:
                raise ValueError("Knowledge-tool approval request has no ID.")
            arguments = json.loads(request.arguments)
            print(f"\n[Approval required] Tool: {request.name}; server: {request.server_label}", flush=True)
            print(f"Arguments: {json.dumps(arguments, indent=2)}", flush=True)
            while True:
                try:
                    decision = input("Approve this action? (yes/no): ").strip().lower()
                except EOFError as exc:
                    raise RuntimeError("Input ended before an approval decision was supplied.") from exc
                if decision in ("yes", "y", "no", "n"):
                    break
                print("Enter yes or no. No approval decision has been sent.", flush=True)
            approved = decision in ("yes", "y")
            print("[Approval] Approving the request." if approved else "[Approval] Denying the request.", flush=True)
            decisions.append({
                "type": "mcp_approval_response",
                "approval_request_id": request.id,
                "approve": approved,
            })
        print(f"[Request] Returning {len(decisions)} approval decision(s) and waiting for the next response...", flush=True)
        client.conversations.items.create(conversation_id=conversation_id, items=decisions)
        response = client.responses.create(
            conversation=conversation_id, input="",
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )
    if not response.output_text or not response.output_text.strip():
        raise RuntimeError("The agent returned no final text answer.")
    print(f"\nAgent:\n{response.output_text}\n", flush=True)
    show_sources(response)
    history.append({"role": "assistant", "content": response.output_text})
    return response.output_text


def display_conversation_history(history):
    print("\nCONVERSATION HISTORY", flush=True)
    if not history:
        print("No questions have been submitted in this client session.", flush=True)
    for turn in history:
        print(f"\n{turn['role'].upper()}: {turn['content']}", flush=True)


def main():
    print("[1/4] Loading this lab's project endpoint and existing agent name...", flush=True)
    load_dotenv(Path(__file__).with_name(".env"))
    endpoint = os.getenv("PROJECT_ENDPOINT")
    name = os.getenv("AGENT_NAME")
    if not endpoint or "<" in endpoint:
        raise ValueError("Configure PROJECT_ENDPOINT in this lab's .env.")
    if not name or "<" in name or name.startswith("your-"):
        raise ValueError("Configure AGENT_NAME in this lab's .env.")
    print(f"Selected agent: {name}", flush=True)
    print("This client does not create an agent, upload documents, or change its knowledge connections.", flush=True)
    print("Model and knowledge-retrieval calls may incur charges.", flush=True)
    print("[2/4] Connecting to Foundry with Microsoft Entra authentication...", flush=True)
    with (
        DefaultAzureCredential(exclude_environment_credential=True, exclude_managed_identity_credential=True) as credential,
        AIProjectClient(credential=credential, endpoint=endpoint) as project,
        project.get_openai_client() as client,
    ):
        print("[3/4] Retrieving the existing product agent...", flush=True)
        agent = project.agents.get(agent_name=name)
        print(f"Connected to agent: {agent.name}", flush=True)
        tools = agent.as_dict()["versions"]["latest"]["definition"].get("tools", [])
        for tool in tools:
            if tool.get("type") == "mcp":
                print(f"[Configured MCP] {tool['server_label']}; approval setting: {tool.get('require_approval')}", flush=True)
                if tool.get("require_approval") == "never":
                    print("[Approval] This MCP tool runs without manual approval prompts.", flush=True)
        print("[4/4] Creating a new conversation for product questions...", flush=True)
        conversation = client.conversations.create(items=[])
        print(f"Conversation created: {conversation.id}", flush=True)
        history = []
        print("Ask about Contoso products. Use history to review this session, or quit to exit.", flush=True)
        try:
            while True:
                try:
                    text = input("You: ").strip()
                except EOFError:
                    print("\n[Input] End of input received. Ending the chat.", flush=True)
                    break
                if not text:
                    print("[Input] Please enter a question. No model request was sent.", flush=True)
                    continue
                if text.lower() == "quit":
                    print("[Input] Quit requested. Ending the chat.", flush=True)
                    break
                if text.lower() == "history":
                    display_conversation_history(history)
                    continue
                send_message_to_agent(text, client, agent.name, conversation.id, history)
        except KeyboardInterrupt:
            print("\n[Input] Interrupted by the user. Ending the chat.", flush=True)
        finally:
            print("[Cleanup] Closing SDK clients and the Azure credential. The existing agent and cloud conversation are not deleted.", flush=True)
    print("[Complete] Product-agent conversation ended.", flush=True)


if __name__ == "__main__":
    main()
