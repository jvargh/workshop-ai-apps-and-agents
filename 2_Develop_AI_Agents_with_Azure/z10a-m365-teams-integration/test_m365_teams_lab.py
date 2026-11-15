import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from openai.types.responses import Response, ResponseFunctionToolCall

from m365_teams_lab import M365TeamsLab
import m365_teams_lab


class M365TeamsLabTests(unittest.TestCase):
    def setUp(self):
        self.project = AIProjectClient(
            endpoint="https://example.services.ai.azure.com/api/projects/example",
            credential=DefaultAzureCredential(),
        )
        self.openai = self.project.get_openai_client()
        self.addCleanup(self.project.close)
        self.addCleanup(self.openai.close)
        self.lab = M365TeamsLab.__new__(M365TeamsLab)
        self.lab.project_client = create_autospec(self.project, spec_set=True)
        self.lab.openai_client = create_autospec(self.openai, spec_set=True)
        self.lab.model_deployment = "test-model"
        self.lab.search_endpoint = "https://example.search.windows.net"
        self.lab.search_index_name = "company-knowledge"
        self.lab.search_connection_id = "test-connection"
        self.lab.search_key = None
        self.lab.credential = MagicMock()
        self.lab.run_failed = False
        self.agent = SimpleNamespace(name="test-agent", version="1")
        self.lab.project_client.agents.create_version.return_value = self.agent
        self.lab.openai_client.conversations.create.return_value = SimpleNamespace(
            id="conv_test"
        )
        self.lab.openai_client.responses.create.return_value = Response.model_validate({
            "id": "resp_test",
            "object": "response",
            "created_at": 0,
            "model": "test-model",
            "status": "completed",
            "parallel_tool_calls": True,
            "tool_choice": "auto",
            "tools": [],
            "output": [{
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{
                    "type": "output_text",
                    "text": "Company laptops must use BitLocker. [it_security_policy.txt]",
                    "annotations": [],
                }],
            }],
        })

    def run_step(self, step, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            step()
        return output.getvalue()

    def assert_agent_deleted(self):
        self.lab.project_client.agents.delete_version.assert_called_once_with(
            agent_name="test-agent", agent_version="1"
        )

    def assert_reference(self, call):
        self.assertEqual(call.kwargs["extra_body"], {
            "agent_reference": {
                "type": "agent_reference",
                "name": "test-agent",
                "version": "1",
            }
        })

    def test_knowledge_demo_uses_project_agents_and_prints_response_text(self):
        output = self.run_step(self.lab.step_1_foundry_iq, [""])
        self.assertNotIn("❌ Error", output)
        self.assertEqual(
            output.count("Response: Company laptops must use BitLocker. [it_security_policy.txt]"), 3,
        )
        calls = self.lab.openai_client.responses.create.call_args_list
        self.assertEqual(len(calls), 3)
        for call in calls:
            self.assertTrue(call.kwargs["input"])
            self.assert_reference(call)
        self.assert_agent_deleted()

    def test_both_agents_use_the_verified_search_index(self):
        definition = self.lab.knowledge_agent_definition()
        self.assertEqual(definition["model"], "test-model")
        tool = definition["tools"][0].as_dict()
        self.assertEqual(tool["type"], "function")
        self.assertEqual(tool["name"], "search_company_documents")
        self.assertEqual(tool["parameters"]["required"], ["query"])
        self.assertFalse(tool["parameters"]["additionalProperties"])
        self.run_step(self.lab.step_1_foundry_iq, [""])
        knowledge_definition = self.lab.project_client.agents.create_version.call_args.kwargs["definition"]
        self.run_step(self.lab.step_4_production_demo, ["quit", ""])
        chat_definition = self.lab.project_client.agents.create_version.call_args.kwargs["definition"]
        self.assertEqual(
            knowledge_definition["tools"][0].as_dict(),
            chat_definition["tools"][0].as_dict(),
        )

    def test_missing_search_configuration_does_not_create_an_ungrounded_agent(self):
        self.lab.search_endpoint = None
        with patch("traceback.print_exc"):
            output = self.run_step(self.lab.step_1_foundry_iq, [""])
        self.assertIn("Run setup_search.py", output)
        self.lab.project_client.agents.create_version.assert_not_called()
        self.lab.openai_client.responses.create.assert_not_called()

    def test_full_answers_and_citation_sources_are_displayed(self):
        response = self.lab.openai_client.responses.create.return_value
        content = response.output[0].content[0]
        content.text = "Policy detail. " * 20 + "Full answer ends here."
        content.annotations = [SimpleNamespace(
            title="IT Security Policy", url="https://example.com/policy",
        )]
        output = io.StringIO()
        with redirect_stdout(output):
            self.lab.print_response(response, "Response")
        self.assertIn("Full answer ends here.", output.getvalue())
        self.assertIn("Source: IT Security Policy (https://example.com/policy)", output.getvalue())

    def test_chat_sends_each_turn_to_the_same_conversation(self):
        output = self.run_step(
            self.lab.step_4_production_demo, ["", "Hello", "Follow up", "quit", ""]
        )
        self.assertNotIn("❌ Error", output)
        self.assertEqual(
            output.count("AGENT: Company laptops must use BitLocker. [it_security_policy.txt]"), 2,
        )
        calls = self.lab.openai_client.responses.create.call_args_list
        self.assertEqual([call.kwargs["input"] for call in calls], ["Hello", "Follow up"])
        for call in calls:
            self.assertEqual(call.kwargs["conversation"], "conv_test")
            self.assert_reference(call)
        self.lab.openai_client.conversations.update.assert_not_called()
        self.lab.openai_client.conversations.delete.assert_called_once_with("conv_test")
        self.assert_agent_deleted()

    def test_chat_cleans_up_after_response_failure(self):
        self.lab.openai_client.responses.create.side_effect = RuntimeError("API failed")
        with patch("traceback.print_exc"):
            output = self.run_step(self.lab.step_4_production_demo, ["Hello", ""])
        self.assertIn("Error: API failed", output)
        self.assertNotIn("Demo complete!", output)
        self.lab.openai_client.conversations.delete.assert_called_once_with("conv_test")
        self.assert_agent_deleted()

    def test_knowledge_demo_cleans_up_after_response_failure(self):
        self.lab.openai_client.responses.create.side_effect = RuntimeError("API failed")
        with patch("traceback.print_exc"):
            output = self.run_step(self.lab.step_1_foundry_iq, [""])
        self.assertIn("Error: API failed", output)
        self.assertNotIn("Demonstration complete!", output)
        self.assert_agent_deleted()

    def test_no_text_response_is_reported(self):
        self.lab.openai_client.responses.create.return_value.output = []
        with patch("traceback.print_exc"):
            output = self.run_step(self.lab.step_4_production_demo, ["Hello", ""])
        self.assertIn("No text response generated (status: completed)", output)
        self.assertNotIn("Demo complete!", output)
        self.assert_agent_deleted()

    def tool_response(self, arguments='{"query":"remote work"}', name="search_company_documents"):
        return self.lab.openai_client.responses.create.return_value.model_copy(update={
            "id": "resp_tool",
            "output": [ResponseFunctionToolCall(
                id="fc_test", call_id="call_test", type="function_call",
                name=name, arguments=arguments, status="completed",
            )],
        })

    def test_search_tool_queries_the_configured_index_and_returns_sources(self):
        with patch("m365_teams_lab.SearchClient") as client, redirect_stdout(io.StringIO()):
            client.return_value.__enter__.return_value.search.return_value = [{
                "title": "Remote Work Policy", "content": "Minimum 25 Mbps",
                "source_file": "remote_work_policy.txt",
            }]
            result = json.loads(self.lab.search_company_documents("remote work"))
        client.assert_called_once_with(
            self.lab.search_endpoint, "company-knowledge", self.lab.credential,
        )
        self.assertEqual(result["documents"][0]["source_file"], "remote_work_policy.txt")
        client.return_value.__enter__.return_value.search.assert_called_once_with(
            search_text="remote work", search_fields=["title", "content"],
            select=["title", "content", "source_file"], top=4,
        )

    def test_tool_outputs_continue_the_original_response_without_a_conversation(self):
        final = self.lab.openai_client.responses.create.return_value
        tool = self.tool_response()
        self.lab.openai_client.responses.create.side_effect = [tool, final]
        with patch.object(self.lab, "search_company_documents", return_value='{"documents":[]}') as search:
            self.assertIs(self.lab.knowledge_response(self.agent, "What is the policy?"), final)
        search.assert_called_once_with("remote work")
        continuation = self.lab.openai_client.responses.create.call_args
        self.assertEqual(continuation.kwargs["previous_response_id"], "resp_tool")
        self.assertEqual(continuation.kwargs["input"][0]["call_id"], "call_test")
        self.assertEqual(continuation.kwargs["input"][0]["output"], '{"documents":[]}')
        self.assert_reference(continuation)

    def test_tool_outputs_preserve_the_existing_conversation(self):
        final = self.lab.openai_client.responses.create.return_value
        self.lab.openai_client.responses.create.side_effect = [self.tool_response(), final]
        with patch.object(self.lab, "search_company_documents", return_value='{"documents":[]}'):
            self.lab.knowledge_response(self.agent, "What is the policy?", "conv_test")
        for call in self.lab.openai_client.responses.create.call_args_list:
            self.assertEqual(call.kwargs["conversation"], "conv_test")
            self.assertNotIn("previous_response_id", call.kwargs)

    def test_unknown_function_and_invalid_arguments_are_rejected(self):
        cases = [
            (self.tool_response(name="unknown"), "Unknown agent function"),
            (self.tool_response(arguments="[]"), "must contain only"),
            (self.tool_response(arguments='{"query":"work","extra":1}'), "must contain only"),
        ]
        with patch.object(self.lab, "search_company_documents") as search:
            for response, message in cases:
                self.lab.openai_client.responses.create.return_value = response
                with self.assertRaisesRegex(ValueError, message):
                    self.lab.knowledge_response(self.agent, "Policy?")
        search.assert_not_called()

    def test_empty_search_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.lab.search_company_documents(" ")

    def test_tool_failures_are_not_converted_into_empty_results(self):
        self.lab.openai_client.responses.create.return_value = self.tool_response()
        with patch.object(self.lab, "search_company_documents", side_effect=RuntimeError("Search denied")):
            with self.assertRaisesRegex(RuntimeError, "Search denied"):
                self.lab.knowledge_response(self.agent, "Policy?")
        self.assertEqual(self.lab.openai_client.responses.create.call_count, 1)

    def test_repeated_tool_calls_are_bounded(self):
        self.lab.openai_client.responses.create.return_value = self.tool_response()
        with patch.object(self.lab, "search_company_documents", return_value='{"documents":[]}') as search:
            with self.assertRaisesRegex(RuntimeError, "five Search tool"):
                self.lab.knowledge_response(self.agent, "Policy?")
        self.assertEqual(search.call_count, 5)

    def test_failed_agent_status_is_not_displayed_as_success(self):
        self.lab.openai_client.responses.create.return_value.status = "failed"
        with self.assertRaisesRegex(RuntimeError, "Agent response failed"):
            self.lab.knowledge_response(self.agent, "Policy?")

    def test_teams_walkthrough_completes_without_network_calls(self):
        with patch("m365_teams_lab.time.sleep") as sleep:
            output = self.run_step(self.lab.step_2_teams_deployment, [""])
        self.assertIn("9. Users Install App", output)
        self.assertEqual(sleep.call_count, 9)
        self.lab.project_client.agents.create_version.assert_not_called()
        self.lab.openai_client.responses.create.assert_not_called()

    def test_graph_and_architecture_walkthroughs_complete_without_api_calls(self):
        graph = self.run_step(self.lab.step_3_graph_api_integration, [""])
        architecture = self.run_step(self.lab.show_architecture, [""])
        self.assertIn("AUTHENTICATION FLOW", graph)
        self.assertIn("DEPLOYMENT CHECKLIST", architecture)
        self.lab.project_client.agents.create_version.assert_not_called()
        self.lab.openai_client.responses.create.assert_not_called()

    def test_main_reports_failed_demo_and_closes_clients(self):
        self.lab.openai_client.responses.create.side_effect = RuntimeError("Search unavailable")
        with patch.object(m365_teams_lab, "M365TeamsLab", return_value=self.lab), patch.object(
            self.lab, "connect", return_value=True
        ), patch("builtins.input", side_effect=["1", "", "0"]), patch(
            "traceback.print_exc"
        ), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(m365_teams_lab.main(), 1)
        self.assertIn("not a successful validation", output.getvalue())
        self.assert_agent_deleted()
        self.lab.openai_client.close.assert_called_once()
        self.lab.project_client.close.assert_called_once()
        self.lab.credential.close.assert_called_once()

    def test_menu_exit_is_not_claimed_as_production_deployment(self):
        with patch.object(m365_teams_lab, "M365TeamsLab", return_value=self.lab), patch.object(
            self.lab, "connect", return_value=True
        ), patch("builtins.input", return_value="0"), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(m365_teams_lab.main(), 0)
        self.assertIn("Teams and Graph were not deployed", output.getvalue())
        self.assertNotIn("ready to build production", output.getvalue())
        self.lab.project_client.agents.create_version.assert_not_called()
        self.lab.openai_client.responses.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
