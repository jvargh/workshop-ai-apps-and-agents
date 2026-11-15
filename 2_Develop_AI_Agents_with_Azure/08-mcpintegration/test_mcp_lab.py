import asyncio
from contextlib import AsyncExitStack, redirect_stdout
import io
import os
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.types import CallToolResult, TextContent, Tool

import agent
import client


def response(identifier="response", output=(), text="Answer", status="completed"):
    return SimpleNamespace(id=identifier, output=list(output), output_text=text, status=status, error="Service error")


def function(name, identifier):
    return SimpleNamespace(type="function_call", name=name, call_id=identifier, arguments="{}")


class RemoteMCPTests(unittest.TestCase):
    def test_approval_rounds_keep_matching_request_and_response_ids(self):
        api = MagicMock()
        first = SimpleNamespace(type="mcp_approval_request", server_label="api-specs", id="approve-1", name="search")
        second = SimpleNamespace(type="mcp_approval_request", server_label="api-specs", id="approve-2", name="fetch")
        call = SimpleNamespace(type="mcp_call", server_label="api-specs", name="fetch", status="completed", error=None)
        api.responses.create.side_effect = [
            response("second", [second]), response("final", [call], text="Verified CLI guidance"),
        ]
        with redirect_stdout(io.StringIO()) as output:
            answer = agent.resolve_approvals(api, "MyAgent", response("first", [first]))
        self.assertEqual(answer, "Verified CLI guidance")
        calls = api.responses.create.call_args_list
        self.assertEqual([call.kwargs["previous_response_id"] for call in calls], ["first", "second"])
        self.assertEqual([call.kwargs["input"][0]["approval_request_id"] for call in calls], ["approve-1", "approve-2"])
        self.assertIn("Completed remote tool call", output.getvalue())

    def test_foreign_server_and_failed_remote_calls_are_not_approved(self):
        api = MagicMock()
        foreign = SimpleNamespace(type="mcp_approval_request", server_label="other", id="request", name="search")
        with self.assertRaisesRegex(ValueError, "unexpected MCP request"):
            agent.resolve_approvals(api, "MyAgent", response(output=[foreign]))
        failed = SimpleNamespace(type="mcp_call", name="search", status="failed", error="Search failed")
        with self.assertRaisesRegex(RuntimeError, "Search failed"):
            agent.resolve_approvals(api, "MyAgent", response(output=[failed]))
        api.responses.create.assert_not_called()

    def test_failed_response_deletes_only_the_created_version(self):
        project = MagicMock()
        project.__enter__.return_value = project
        api = project.get_openai_client.return_value
        api.__enter__.return_value = api
        project.agents.create_version.return_value = SimpleNamespace(name="MyAgent", version="7")
        api.responses.create.return_value = response(status="failed")
        with patch.dict(os.environ, {"PROJECT_ENDPOINT": "https://example/api/projects/project", "MODEL_DEPLOYMENT_NAME": "model"}), patch.object(
            agent, "load_dotenv"
        ), patch.object(agent, "DefaultAzureCredential"), patch.object(
            agent, "AIProjectClient", return_value=project
        ), redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, "Service error"):
                agent.main()
        project.agents.delete_version.assert_called_once_with(agent_name="MyAgent", agent_version="7")
        self.assertNotIn("[Complete]", output.getvalue())


class LocalMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_server_returns_expected_sample_decisions(self):
        with redirect_stdout(io.StringIO()):
            async with AsyncExitStack() as stack:
                session = await client.connect_to_server(stack)
                tools = (await session.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, {"get_inventory_levels", "get_weekly_sales"})
                inventory = await session.call_tool("get_inventory_levels", {})
                sales = await session.call_tool("get_weekly_sales", {})
        import json
        stock = json.loads(client.tool_result_text(inventory))
        weekly = json.loads(client.tool_result_text(sales))
        self.assertEqual(len(stock), 10)
        self.assertEqual({name for name in stock if stock[name] < 10 and weekly[name] > 15},
                         {"Moisturizer", "Shampoo", "Skin Serum"})
        self.assertEqual({name for name in stock if stock[name] > 20 and weekly[name] < 5},
                         {"Body Spray", "Cleanser"})

    async def test_chained_calls_return_only_current_results_with_matching_ids(self):
        api = MagicMock()
        session = MagicMock()
        session.call_tool = AsyncMock(side_effect=[
            CallToolResult(content=[], structured_content={"Moisturizer": 6}),
            CallToolResult(content=[], structured_content={"Moisturizer": 22}),
        ])
        api.responses.create.side_effect = [
            response(output=[function("get_weekly_sales", "sales")]),
            response(text="Restock Moisturizer"),
        ]
        with redirect_stdout(io.StringIO()):
            answer = await client.resolve_tool_calls(
                api, session, "conversation", "inventory-agent",
                {"get_inventory_levels", "get_weekly_sales"},
                response(output=[function("get_inventory_levels", "inventory")]),
            )
        self.assertEqual(answer, "Restock Moisturizer")
        calls = api.responses.create.call_args_list
        self.assertEqual([len(call.kwargs["input"]) for call in calls], [1, 1])
        self.assertEqual([call.kwargs["input"][0]["call_id"] for call in calls], ["inventory", "sales"])
        self.assertEqual(session.call_tool.await_count, 2)

    async def test_unknown_tool_is_rejected_before_calling_server(self):
        api = MagicMock()
        session = MagicMock()
        session.call_tool = AsyncMock()
        with self.assertRaisesRegex(ValueError, "unknown MCP tool"):
            await client.resolve_tool_calls(api, session, "conversation", "inventory-agent", {"known"},
                                            response(output=[function("other", "call")]))
        session.call_tool.assert_not_called()

    async def test_failed_chat_cleans_up_the_created_agent_version(self):
        session = MagicMock()
        session.list_tools = AsyncMock(return_value=SimpleNamespace(tools=[
            Tool(name="get_inventory_levels", description="Sample inventory", input_schema={"type": "object", "properties": {}})
        ]))
        project = MagicMock()
        project.__enter__.return_value = project
        api = project.get_openai_client.return_value
        api.__enter__.return_value = api
        project.agents.create_version.return_value = SimpleNamespace(name="inventory-agent", version="9")
        api.responses.create.return_value = response(status="failed")
        with patch.object(client, "DefaultAzureCredential"), patch.object(
            client, "AIProjectClient", return_value=project
        ), patch("builtins.input", return_value="Question"), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "Service error"):
                await client.chat_loop(session, "endpoint", "model")
        project.agents.delete_version.assert_called_once_with(agent_name="inventory-agent", agent_version="9")

    async def test_blank_input_and_quit_do_not_call_the_model(self):
        session = MagicMock()
        session.list_tools = AsyncMock(return_value=SimpleNamespace(tools=[
            Tool(name="get_inventory_levels", description="Sample inventory", input_schema={"type": "object", "properties": {}})
        ]))
        project = MagicMock()
        project.__enter__.return_value = project
        api = project.get_openai_client.return_value
        api.__enter__.return_value = api
        project.agents.create_version.return_value = SimpleNamespace(name="inventory-agent", version="9")
        with patch.object(client, "DefaultAzureCredential"), patch.object(
            client, "AIProjectClient", return_value=project
        ), patch("builtins.input", side_effect=["", "quit"]), redirect_stdout(io.StringIO()) as output:
            await client.chat_loop(session, "endpoint", "model")
        api.responses.create.assert_not_called()
        self.assertIn("No model request was sent", output.getvalue())
        project.agents.delete_version.assert_called_once()

    async def test_error_empty_and_multiple_text_results_are_handled_explicitly(self):
        with self.assertRaisesRegex(RuntimeError, "returned an error"):
            client.tool_result_text(CallToolResult(content=[], is_error=True))
        with self.assertRaisesRegex(RuntimeError, "no structured data"):
            client.tool_result_text(CallToolResult(content=[]))
        result = CallToolResult(content=[TextContent(type="text", text="first"), TextContent(type="text", text="second")])
        self.assertEqual(client.tool_result_text(result), "first\nsecond")


if __name__ == "__main__":
    unittest.main()
