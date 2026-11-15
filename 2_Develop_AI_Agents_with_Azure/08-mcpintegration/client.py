import os
import asyncio
import json
from pathlib import Path
import sys
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
from azure.identity import DefaultAzureCredential
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult


async def connect_to_server(exit_stack: AsyncExitStack):
    print("[MCP] Starting server.py with this client's Python interpreter over stdio...", flush=True)
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("server.py"))],
        env=None,
    )
    read, write = await exit_stack.enter_async_context(stdio_client(server_params))
    session = await exit_stack.enter_async_context(ClientSession(read, write))
    print("[MCP] Initializing the local protocol session...", flush=True)
    await session.initialize()
    return session


def tool_result_text(result):
    if not isinstance(result, CallToolResult):
        raise RuntimeError("The MCP server did not return a completed tool result.")
    if result.is_error:
        raise RuntimeError(f"MCP tool returned an error: {result.content}")
    if result.structured_content is not None:
        return json.dumps(result.structured_content)
    texts = [item.text for item in result.content if item.type == "text" and item.text.strip()]
    if not texts:
        raise RuntimeError("MCP tool returned no structured data or nonempty text.")
    return "\n".join(texts)


async def resolve_tool_calls(client, session, conversation_id, agent_name, tool_names, response):
    while True:
        if response.status != "completed":
            raise RuntimeError(f"Agent response did not complete: {response.status}; {response.error}")
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            if not response.output_text or not response.output_text.strip():
                raise RuntimeError("The agent returned no final text answer.")
            return response.output_text
        outputs: ResponseInputParam = []
        for item in calls:
            if item.name not in tool_names:
                raise ValueError(f"The agent requested an unknown MCP tool: {item.name}")
            print(f"[Tool] Agent requested {item.name}; calling the local MCP server...", flush=True)
            result = await session.call_tool(item.name, json.loads(item.arguments))
            text = tool_result_text(result)
            print(f"[Tool result] {text}", flush=True)
            outputs.append(FunctionCallOutput(
                type="function_call_output", call_id=item.call_id, output=text,
            ))
        print(f"[Request] Returning {len(outputs)} current tool result(s) to the agent. Waiting for the next response...", flush=True)
        response = client.responses.create(
            conversation=conversation_id, input=outputs,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )


async def chat_loop(session, project_endpoint, model_deployment):
    print("[Discovery] Listing the inventory server's available tools...", flush=True)
    tools = (await session.list_tools()).tools
    if not tools:
        raise RuntimeError("The local MCP server returned no tools.")
    print("Connected to server with tools:", [tool.name for tool in tools], flush=True)
    function_tools: list[FunctionTool] = []
    for tool in tools:
        schema = dict(tool.input_schema)
        schema["additionalProperties"] = False
        print(f"[Bridge] Exposing {tool.name} as a Foundry function tool.", flush=True)
        function_tools.append(FunctionTool(
            name=tool.name, description=tool.description, parameters=schema, strict=True,
        ))
    tool_names = {tool.name for tool in tools}
    print("[Connect] Connecting to Foundry with Microsoft Entra authentication...", flush=True)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as client,
    ):
        print("[Agent] Creating an inventory-agent version using the discovered tools...", flush=True)
        agent = project_client.agents.create_version(
            agent_name="inventory-agent",
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions=(
                    "You are an inventory assistant using fixed sample inventory and last week's sales. "
                    "Use the tools to obtain the data. Recommend restock only if inventory < 10 and weekly sales > 15. "
                    "Recommend clearance only if inventory > 20 and weekly sales < 5. "
                    "Explain recommendations using the data; do not change stock or claim current-week sales."
                ),
                tools=function_tools,
            ),
        )
        print(f"Created agent version: {agent.name} / {agent.version}", flush=True)
        try:
            conversation = client.conversations.create()
            print(f"Conversation created: {conversation.id}", flush=True)
            print("Follow-ups reuse this conversation; old function outputs are not resubmitted.", flush=True)
            while True:
                try:
                    text = input("Enter a prompt for the inventory agent. Use 'quit' to exit.\nUSER: ").strip()
                except EOFError:
                    print("[Input] End of input received. Ending the chat.", flush=True)
                    break
                if text.lower() == "quit":
                    print("Exiting chat.", flush=True)
                    break
                if not text:
                    print("[Input] Please enter a prompt. No model request was sent.", flush=True)
                    continue
                print("[Conversation] Adding your question to the current conversation...", flush=True)
                client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[{"type": "message", "role": "user", "content": text}],
                )
                print("[Request] Asking the agent to answer or request an inventory tool...", flush=True)
                response = client.responses.create(
                    conversation=conversation.id, input=[],
                    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                )
                answer = await resolve_tool_calls(client, session, conversation.id, agent.name, tool_names, response)
                print(f"Agent response: {answer}", flush=True)
        finally:
            print(f"[Cleanup] Deleting only the created agent version: {agent.name} / {agent.version}...", flush=True)
            project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("[Cleanup] Created inventory agent version deleted.", flush=True)


async def main():
    print("[Setup] Loading this lab's project and deployment configuration...", flush=True)
    load_dotenv(Path(__file__).with_name(".env"))
    endpoint = os.getenv("PROJECT_ENDPOINT")
    model = os.getenv("MODEL_DEPLOYMENT_NAME")
    if not endpoint or "<" in endpoint:
        raise ValueError("Configure PROJECT_ENDPOINT in this lab's .env.")
    if not model or "<" in model or model.startswith("your-"):
        raise ValueError("Configure MODEL_DEPLOYMENT_NAME in this lab's .env.")
    print(f"Selected deployment: {model}", flush=True)
    print("Inventory/sales are static samples. Model calls may incur charges; no orders or stock changes are made.", flush=True)
    async with AsyncExitStack() as exit_stack:
        try:
            session = await connect_to_server(exit_stack)
            await chat_loop(session, endpoint, model)
        finally:
            print("[Cleanup] Closing the MCP session, stdio transport, and local server process...", flush=True)
    print("[Complete] Local MCP example finished. The cloud conversation is not deleted.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
