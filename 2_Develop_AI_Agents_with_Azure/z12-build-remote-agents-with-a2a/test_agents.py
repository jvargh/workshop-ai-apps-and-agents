import importlib
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from a2a.types import SendMessageResponse, Task, TaskState
from openai.types.responses import ResponseFunctionToolCall

from outline_agent.agent import OutlineAgent
from routing_agent.agent import RoutingAgent
from title_agent.agent import TitleAgent
from title_agent.agent_executor import FoundryAgentExecutor


def response(text="", output=None, status="completed", error=None):
    return SimpleNamespace(
        status=status, output_text=text, output=output or [],
        error=error, incomplete_details=None,
    )


class AgentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "PROJECT_ENDPOINT": "https://example.test/api/projects/test",
            "MODEL_DEPLOYMENT_NAME": "reasoning-model",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def make_agent(self, agent_class):
        module = importlib.import_module(agent_class.__module__)
        project = patch.object(module, "AIProjectClient").start()
        patch.object(module, "DefaultAzureCredential").start()
        self.addCleanup(patch.stopall)
        client = project.return_value
        client.agents.create_version.return_value = SimpleNamespace(
            name="test-agent", version="1",
        )
        client.get_openai_client.return_value.conversations.create.return_value.id = "conversation-1"
        agent = agent_class()
        return agent, client

    async def test_specialists_use_responses_without_sampling_parameters(self):
        for agent_class in (TitleAgent, OutlineAgent):
            with self.subTest(agent=agent_class.__name__):
                agent, client = self.make_agent(agent_class)
                agent.openai_client.responses.create.return_value = response("React result")
                self.assertEqual(await agent.run_conversation("React"), ["React result"])
                self.assertEqual(await agent.run_conversation("React again"), ["React result"])
                client.agents.create_version.assert_called_once()
                definition = client.agents.create_version.call_args.kwargs["definition"].as_dict()
                self.assertEqual(definition["model"], "reasoning-model")
                for parameter in ("temperature", "top_p"):
                    self.assertNotIn(parameter, definition)
                    self.assertNotIn(parameter, agent.openai_client.responses.create.call_args.kwargs)

    async def test_specialists_surface_failed_and_empty_responses(self):
        for agent_class in (TitleAgent, OutlineAgent):
            agent, _ = self.make_agent(agent_class)
            for result in (response(status="failed", error="model error"), response()):
                agent.openai_client.responses.create.return_value = result
                with self.assertRaises(RuntimeError):
                    await agent.run_conversation("React")

    async def test_router_continues_function_calls_in_same_conversation(self):
        agent, client = self.make_agent(RoutingAgent)
        agent.cards = {"title": SimpleNamespace(name="title", description="Titles")}
        agent.create_agent()
        definition = client.agents.create_version.call_args.kwargs["definition"].as_dict()
        self.assertNotIn("top_p", definition)
        self.assertNotIn("temperature", definition)
        agent.send_message = AsyncMock(return_value=Task(
            id="task-1", context_id="context-1", status={"state": "completed"},
        ))
        call = ResponseFunctionToolCall(
            type="function_call", name="send_message", call_id="call-1",
            arguments=json.dumps({"agent_name": "title", "task": "React"}),
        )
        agent.openai_client.responses.create.side_effect = [
            response(output=[call]), response("Final title and outline"),
        ]
        result = await agent.process_user_message("Write about React")
        self.assertEqual(result, "Final title and outline")
        agent.send_message.assert_awaited_once_with(agent_name="title", task="React")
        calls = agent.openai_client.responses.create.call_args_list
        self.assertEqual(calls[0].kwargs["conversation"], calls[1].kwargs["conversation"])
        self.assertEqual(calls[1].kwargs["input"][0]["call_id"], "call-1")
        self.assertEqual(calls[1].kwargs["input"][0]["type"], "function_call_output")

    async def test_router_surfaces_model_and_remote_errors(self):
        agent, _ = self.make_agent(RoutingAgent)
        agent.create_agent()
        agent.openai_client.responses.create.return_value = response(status="failed", error="model error")
        self.assertIn("model error", await agent.process_user_message("React"))
        call = ResponseFunctionToolCall(
            type="function_call", name="send_message", call_id="call-1",
            arguments=json.dumps({"agent_name": "title", "task": "React"}),
        )
        agent.openai_client.responses.create.return_value = response(output=[call])
        agent.send_message = AsyncMock(side_effect=RuntimeError("remote failed"))
        self.assertIn("remote failed", await agent.process_user_message("React"))

    async def test_router_uses_selected_remote_connection_and_rejects_failed_tasks(self):
        agent, _ = self.make_agent(RoutingAgent)
        remote = SimpleNamespace(send_message=AsyncMock())
        agent.remote_agent_connections["title"] = remote
        for state in ("completed", "failed"):
            remote.send_message.return_value = SendMessageResponse.model_validate({
                "jsonrpc": "2.0", "id": "request-1",
                "result": {
                    "kind": "task", "id": "task-1", "contextId": "context-1",
                    "status": {"state": state},
                },
            })
            if state == "completed":
                task = await agent.send_message("title", "React")
                self.assertEqual(task.id, "task-1")
            else:
                with self.assertRaisesRegex(RuntimeError, "did not complete"):
                    await agent.send_message("title", "React")
        request = remote.send_message.call_args.kwargs["message_request"]
        self.assertEqual(request.params.message.parts[0].root.text, "React")
        with self.assertRaises(ValueError):
            await agent.send_message("missing", "React")

    async def test_router_accepts_exactly_ten_tool_rounds_and_rejects_an_eleventh(self):
        for exceeds_limit in (False, True):
            agent, _ = self.make_agent(RoutingAgent)
            agent.create_agent()
            agent.send_message = AsyncMock(return_value=Task(
                id="task-1", context_id="context-1", status={"state": "completed"},
            ))
            call = ResponseFunctionToolCall(
                type="function_call", name="send_message", call_id="call-1",
                arguments=json.dumps({"agent_name": "title", "task": "React"}),
            )
            agent.openai_client.responses.create.side_effect = [
                *[response(output=[call]) for _ in range(10)],
                response(output=[call]) if exceeds_limit else response("Final answer"),
            ]
            result = await agent.process_user_message("React")
            self.assertEqual(agent.send_message.await_count, 10)
            self.assertEqual(agent.openai_client.responses.create.call_count, 11)
            if exceeds_limit:
                self.assertIn("exceeded ten", result)
            else:
                self.assertEqual(result, "Final answer")

    async def test_router_rejects_unknown_tools_and_malformed_arguments(self):
        for name, arguments in (
            ("unknown", "{}"),
            ("send_message", "[]"),
            ("send_message", '{"agent_name": "title"}'),
            ("send_message", '{"agent_name": "title", "task": 12}'),
            ("send_message", '{"agent_name": "title", "task": ""}'),
            ("send_message", "not-json"),
        ):
            agent, _ = self.make_agent(RoutingAgent)
            agent.create_agent()
            agent.send_message = AsyncMock()
            call = ResponseFunctionToolCall(
                type="function_call", name=name, call_id="call-1", arguments=arguments,
            )
            agent.openai_client.responses.create.return_value = response(output=[call])
            self.assertIn("Error processing request:", await agent.process_user_message("React"))
            agent.send_message.assert_not_awaited()

    async def test_title_executor_processes_request_and_completes_task(self):
        executor = FoundryAgentExecutor(MagicMock())
        writer = SimpleNamespace(run_conversation=AsyncMock(return_value=["React title"]))
        executor._get_or_create_agent = AsyncMock(return_value=writer)
        context = SimpleNamespace(
            task_id="task-1", context_id="context-1",
            message=SimpleNamespace(parts=[SimpleNamespace(root=SimpleNamespace(text="React"))]),
        )
        with patch("title_agent.agent_executor.TaskUpdater") as updater_class:
            updater = AsyncMock()
            updater_class.return_value = updater
            await executor.execute(context, MagicMock())
        writer.run_conversation.assert_awaited_once_with("React")
        updater.complete.assert_awaited_once()
        updater.failed.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
