import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from mcp.types import CallToolResult, TextContent, Tool
from openai.types.responses import Response, ResponseFunctionToolCall

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workiq_lab import WorkIQLab


class WorkIQLabTests(unittest.TestCase):
    def setUp(self):
        self.project = AIProjectClient(
            endpoint="https://example.services.ai.azure.com/api/projects/example",
            credential=DefaultAzureCredential(),
        )
        self.openai = self.project.get_openai_client()
        self.addCleanup(self.project.close)
        self.addCleanup(self.openai.close)
        self.lab = WorkIQLab.__new__(WorkIQLab)
        self.lab.model_deployment = "test-model"
        self.lab.credential = MagicMock()
        self.lab.run_failed = False
        self.lab.project_client = create_autospec(self.project, spec_set=True)
        self.lab.openai_client = create_autospec(self.openai, spec_set=True)
        self.lab.agent = SimpleNamespace(name="workplace-test", version="2")
        self.lab.project_client.agents.create_version.return_value = self.lab.agent
        self.schema = {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "conversationId": {"type": "string"},
            },
            "required": ["question"],
        }
        self.tool = Tool(
            name="ask_work_iq", description="Ask a workplace question", inputSchema=self.schema,
        )
        self.lab.raw_tools_map = {self.tool.name: self.tool}
        self.lab.openai_client.conversations.create.return_value = SimpleNamespace(id="conv_test")
        self.response = Response.model_validate({
            "id": "resp_final", "object": "response", "created_at": 0, "model": "test-model",
            "status": "completed", "parallel_tool_calls": True, "tool_choice": "auto", "tools": [],
            "output": [{
                "id": "msg_test", "type": "message", "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": "WORKIQ_OK", "annotations": []}],
            }],
        })
        self.lab.openai_client.responses.create.return_value = self.response

    def tool_response(self, name="ask_work_iq", arguments='{"question":"A test question"}'):
        return self.response.model_copy(update={
            "id": "resp_tool",
            "output": [ResponseFunctionToolCall(
                id="fc_test", call_id="call_test", type="function_call",
                name=name, arguments=arguments, status="completed",
            )],
        })

    def run_query(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = self.lab._execute_query("A test question")
        return result, output.getvalue()

    def test_mcp_protocol_schema_alias_converts_without_losing_optional_fields(self):
        with patch.object(self.lab, "_get_workiq_tools", return_value=[self.tool]), \
                redirect_stdout(io.StringIO()):
            self.lab._create_workplace_agent()
        definition = self.lab.project_client.agents.create_version.call_args.kwargs["definition"]
        tool = definition.tools[0]
        self.assertEqual(tool.name, "ask_work_iq")
        self.assertEqual(tool.parameters, self.schema)
        self.assertFalse(tool.strict)

    def test_legal_and_diagnostic_consent_tools_are_not_exposed(self):
        tools = [
            self.tool,
            Tool(name="accept_eula", inputSchema={"type": "object"}),
            Tool(name="get_debug_link", inputSchema={"type": "object"}),
        ]
        with patch.object(self.lab, "_get_workiq_tools", return_value=tools), \
                redirect_stdout(io.StringIO()):
            self.lab._create_workplace_agent()
        self.assertEqual(set(self.lab.raw_tools_map), {"ask_work_iq"})
        definition = self.lab.project_client.agents.create_version.call_args.kwargs["definition"]
        self.assertEqual([tool.name for tool in definition.tools], ["ask_work_iq"])

    def test_missing_query_tool_fails_before_agent_creation(self):
        with patch.object(self.lab, "_get_workiq_tools", return_value=[]), \
                redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "required ask_work_iq"):
                self.lab._create_workplace_agent()
        self.lab.project_client.agents.create_version.assert_not_called()

    def test_final_answer_uses_versioned_agent_and_cleans_up_conversation(self):
        result, output = self.run_query()
        self.assertTrue(result)
        self.assertIn("WORKIQ_OK", output)
        call = self.lab.openai_client.responses.create.call_args
        self.assertEqual(call.kwargs["input"], "")
        self.assertEqual(call.kwargs["extra_body"]["agent_reference"]["version"], "2")
        self.lab.openai_client.conversations.delete.assert_called_once_with("conv_test")

    def test_all_text_and_structured_tool_output_are_preserved(self):
        self.lab.openai_client.responses.create.side_effect = [self.tool_response(), self.response]
        tool_result = CallToolResult(
            content=[TextContent(type="text", text="First"), TextContent(type="text", text="Second")],
            structuredContent={"answer": "Complete result"}, isError=False,
        )
        with patch.object(self.lab, "_call_workiq_tool", return_value=tool_result) as execute:
            result, _ = self.run_query()
        self.assertTrue(result)
        execute.assert_called_once_with("ask_work_iq", {"question": "A test question"})
        call = self.lab.openai_client.responses.create.call_args
        payload = json.loads(call.kwargs["input"][0]["output"])
        self.assertEqual([block["text"] for block in payload["content"]], ["First", "Second"])
        self.assertEqual(payload["structuredContent"], {"answer": "Complete result"})
        self.assertEqual(call.kwargs["conversation"], "conv_test")
        self.assertNotIn("previous_response_id", call.kwargs)

    def test_structured_only_tool_output_is_supported(self):
        self.lab.openai_client.responses.create.side_effect = [self.tool_response(), self.response]
        with patch.object(self.lab, "_call_workiq_tool", return_value=CallToolResult(
            content=[], structuredContent={"answer": "Structured result"},
        )):
            result, _ = self.run_query()
        self.assertTrue(result)

    def test_mcp_error_is_reported_not_sent_as_a_successful_result(self):
        self.lab.openai_client.responses.create.return_value = self.tool_response()
        with patch.object(self.lab, "_call_workiq_tool", return_value=CallToolResult(
            content=[TextContent(type="text", text="Explicit access denial")], isError=True,
        )):
            result, output = self.run_query()
        self.assertFalse(result)
        self.assertIn("Work IQ tool failed", output)
        self.assertIn("Explicit access denial", output)
        self.assertEqual(self.lab.openai_client.responses.create.call_count, 1)
        self.lab.openai_client.conversations.delete.assert_called_once_with("conv_test")

    def test_empty_tool_output_is_reported(self):
        self.lab.openai_client.responses.create.return_value = self.tool_response()
        with patch.object(self.lab, "_call_workiq_tool", return_value=CallToolResult(content=[])):
            result, output = self.run_query()
        self.assertFalse(result)
        self.assertIn("no content or structured result", output)

    def test_unknown_tool_and_invalid_argument_shape_do_not_execute(self):
        for response in [self.tool_response(name="accept_eula"), self.tool_response(arguments="[]")]:
            with self.subTest(response=response.output[0].name):
                self.lab.openai_client.responses.create.return_value = response
                with patch.object(self.lab, "_call_workiq_tool") as execute:
                    result, _ = self.run_query()
                self.assertFalse(result)
                execute.assert_not_called()

    def test_failed_response_status_is_not_success(self):
        self.lab.openai_client.responses.create.return_value = self.response.model_copy(
            update={"status": "failed"},
        )
        result, output = self.run_query()
        self.assertFalse(result)
        self.assertIn("Response failed", output)

    def test_empty_final_response_is_not_success(self):
        self.lab.openai_client.responses.create.return_value = self.response.model_copy(
            update={"output": []},
        )
        result, output = self.run_query()
        self.assertFalse(result)
        self.assertIn("No response received", output)

    def test_tool_rounds_are_bounded(self):
        self.lab.openai_client.responses.create.return_value = self.tool_response()
        with patch.object(self.lab, "_call_workiq_tool", return_value=CallToolResult(
            content=[TextContent(type="text", text="Result")],
        )) as execute:
            result, output = self.run_query()
        self.assertFalse(result)
        self.assertIn("ten Work IQ tool response rounds", output)
        self.assertEqual(execute.call_count, 10)

    def test_cleanup_uses_current_delete_version_parameter_and_closes_clients(self):
        with redirect_stdout(io.StringIO()):
            self.lab.cleanup()
        self.lab.project_client.agents.delete_version.assert_called_once_with(
            agent_name="workplace-test", agent_version="2",
        )
        self.lab.openai_client.close.assert_called_once()
        self.lab.project_client.close.assert_called_once()
        self.lab.credential.close.assert_called_once()

    def test_validation_fails_closed_if_workiq_cannot_be_found(self):
        self.lab.workiq_command = None
        with redirect_stdout(io.StringIO()):
            self.assertFalse(self.lab.validate_workiq_setup())

    def test_failed_query_makes_the_menu_run_fail_and_still_cleans_up(self):
        self.lab.openai_client.responses.create.return_value = self.response.model_copy(update={"status": "failed"})
        with patch.object(self.lab, "connect", return_value=True), patch(
            "builtins.input", side_effect=["5", "A test question", "", "0"]
        ), redirect_stdout(io.StringIO()) as output:
            self.assertFalse(self.lab.run())
        self.assertIn("not a successful validation", output.getvalue())
        self.assertNotIn("[Complete]", output.getvalue())
        self.lab.project_client.agents.delete_version.assert_called_once()
        self.lab.openai_client.close.assert_called_once()

    def test_input_eof_runs_cleanup_without_model_calls(self):
        with patch.object(self.lab, "connect", return_value=True), patch(
            "builtins.input", side_effect=EOFError
        ), redirect_stdout(io.StringIO()):
            self.assertTrue(self.lab.run())
        self.lab.openai_client.responses.create.assert_not_called()
        self.lab.project_client.agents.delete_version.assert_called_once()
        self.lab.credential.close.assert_called_once()

    def test_cleanup_failure_is_reported_while_all_clients_close(self):
        self.lab.project_client.agents.delete_version.side_effect = RuntimeError("Deletion denied")
        with redirect_stdout(io.StringIO()) as output:
            self.assertFalse(self.lab.cleanup())
        self.assertIn("Deletion denied", output.getvalue())
        self.lab.openai_client.close.assert_called_once()
        self.lab.project_client.close.assert_called_once()
        self.lab.credential.close.assert_called_once()

    def test_research_option_does_not_claim_an_unattached_foundry_iq_tool(self):
        with patch("builtins.input", return_value="Sample topic"), patch.object(
            self.lab, "_execute_query"
        ) as execute, redirect_stdout(io.StringIO()) as output:
            self.lab.scenario_4_combined_intelligence()
        self.assertIn("using Work IQ only", execute.call_args.args[0])
        self.assertNotIn("using both workplace data and knowledge base", execute.call_args.args[0])
        self.assertIn("No separate Foundry IQ", output.getvalue())


if __name__ == "__main__":
    unittest.main()
