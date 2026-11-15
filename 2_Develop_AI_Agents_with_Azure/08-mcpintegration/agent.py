import os
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam

PROMPT = "Give me the Azure CLI commands to create an Azure Container App with a managed identity."
SERVER_LABEL = "api-specs"
SERVER_URL = "https://learn.microsoft.com/api/mcp"


def resolve_approvals(client, agent_name, response):
    while True:
        if response.status != "completed":
            raise RuntimeError(f"Agent response did not complete: {response.status}; {response.error}")
        approvals: ResponseInputParam = []
        for item in response.output:
            if item.type == "mcp_list_tools":
                if item.error:
                    raise RuntimeError(f"MCP tool discovery failed: {item.error}")
                print(f"[MCP] Foundry discovered {len(item.tools)} tools from {item.server_label}.", flush=True)
            elif item.type == "mcp_call":
                if item.error or item.status != "completed":
                    raise RuntimeError(f"Remote MCP call failed: {item.name}; {item.error}; {item.status}")
                print(f"[MCP] Completed remote tool call: {item.server_label} / {item.name}", flush=True)
            elif item.type == "mcp_approval_request":
                if item.server_label != SERVER_LABEL or not item.id:
                    raise ValueError(f"Cannot approve an unexpected MCP request from {item.server_label}.")
                print(f"[Approval] Automatically approving {item.name} on the configured Microsoft Learn server.", flush=True)
                approvals.append(McpApprovalResponse(
                    type="mcp_approval_response", approve=True, approval_request_id=item.id,
                ))
        if not approvals:
            if not response.output_text or not response.output_text.strip():
                raise RuntimeError("The agent returned no final text answer.")
            return response.output_text
        print(f"[Request] Returning {len(approvals)} approval(s). Waiting for tool execution and the next response...", flush=True)
        response = client.responses.create(
            input=approvals, previous_response_id=response.id,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )


def main():
    print("[1/4] Loading the Foundry project and deployment configuration...", flush=True)
    load_dotenv(Path(__file__).with_name(".env"))
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
    if not project_endpoint or "<" in project_endpoint:
        raise ValueError("Configure PROJECT_ENDPOINT in this lab's .env.")
    if not model_deployment or "<" in model_deployment or model_deployment.startswith("your-"):
        raise ValueError("Configure MODEL_DEPLOYMENT_NAME in this lab's .env.")
    print(f"Selected deployment: {model_deployment}", flush=True)
    print("This example retrieves public documentation and prints commands; it does not run them or deploy resources.", flush=True)
    print("[2/4] Connecting to Foundry with Microsoft Entra authentication...", flush=True)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as client,
    ):
        print(f"[3/4] Creating an agent version with remote MCP server {SERVER_URL}...", flush=True)
        print("Requests from this configured server are automatically approved for this demonstration.", flush=True)
        agent = project_client.agents.create_version(
            agent_name="MyAgent",
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions="Use the Microsoft Learn MCP tools to verify Azure CLI guidance before answering. Return commands and explanations; do not execute infrastructure changes.",
                tools=[MCPTool(server_label=SERVER_LABEL, server_url=SERVER_URL, require_approval="always")],
            ),
        )
        print(f"Created agent version: {agent.name} / {agent.version}", flush=True)
        try:
            print("[4/4] Creating a conversation and sending the fixed sample prompt...", flush=True)
            conversation = client.conversations.create()
            print(f"Conversation created: {conversation.id}", flush=True)
            print(f"Prompt: {PROMPT}", flush=True)
            print("[Request] Waiting for the agent's response or MCP approval requests...", flush=True)
            response = client.responses.create(
                conversation=conversation.id, input=PROMPT,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            )
            answer = resolve_approvals(client, agent.name, response)
            print(f"\nAgent response:\n{answer}", flush=True)
        finally:
            print(f"[Cleanup] Deleting only the created agent version: {agent.name} / {agent.version}...", flush=True)
            project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("[Cleanup] Created agent version deleted.", flush=True)
    print("[Complete] Hosted MCP example finished. The cloud conversation is not deleted.", flush=True)


if __name__ == "__main__":
    main()
