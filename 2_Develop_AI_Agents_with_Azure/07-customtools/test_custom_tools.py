from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import agent
import functions


def reply(*calls, text="Final answer", status="completed"):
    return SimpleNamespace(output=list(calls), output_text=text, status=status, error="Service error")


def call(name, arguments, identifier):
    return SimpleNamespace(
        type="function_call", name=name, arguments=json.dumps(arguments), call_id=identifier
    )


class LocalToolTests(unittest.TestCase):
    def test_cost_explains_the_calculation_and_preserves_result(self):
        with redirect_stdout(io.StringIO()) as output:
            result = json.loads(functions.calculate_observation_cost("standard", 2, "normal"))
        self.assertEqual(result["base_cost"], 100)
        self.assertEqual(result["priority_multiplier"], 1.25)
        self.assertEqual(result["total_cost"], 125)
        self.assertIn("= $125.00", output.getvalue())
        self.assertIn("No booking or payment", output.getvalue())

    def test_invalid_cost_inputs_return_explicit_tool_errors(self):
        for tier, hours, priority in (("unknown", 2, "normal"), ("standard", 0, "normal"), ("standard", 2, "unknown")):
            with self.subTest(tier=tier, hours=hours, priority=priority), redirect_stdout(io.StringIO()) as output:
                result = json.loads(functions.calculate_observation_cost(tier, hours, priority))
            self.assertIn("error", result)
            self.assertIn("Cannot calculate", output.getvalue())

    def test_sample_event_and_no_match_are_both_explained(self):
        with patch.object(functions, "datetime") as clock, redirect_stdout(io.StringIO()) as output:
            clock.now.return_value.strftime.return_value = "1101"
            result = json.loads(functions.next_visible_event("North America"))
            missing = json.loads(functions.next_visible_event("unknown"))
        self.assertEqual(result["event"], "Geminids Meteor Shower")
        self.assertIn("No upcoming events", missing["message"])
        self.assertIn("Searching the sample schedule", output.getvalue())
        self.assertIn("No remaining sample event", output.getvalue())

    def test_report_writes_real_file_and_reports_its_path(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()) as output:
            try:
                os.chdir(folder)
                result = json.loads(functions.generate_observation_report(
                    "Sample Session", "north_america", "standard", 2, "normal", "Lab Observer"
                ))
                report = Path(result["file"]).read_text()
                self.assertIn("Lab Observer", report)
                self.assertIn("$125.00", report)
                self.assertIn(f"Saved {result['file']}", output.getvalue())
            finally:
                os.chdir(original)


class AgentToolTests(unittest.TestCase):
    def test_multiple_rounds_execute_local_tools_and_return_matching_call_ids(self):
        client = MagicMock()
        client.responses.create.side_effect = [
            reply(call("calculate_observation_cost", {"telescope_tier": "standard", "hours": 2, "priority": "normal"}, "cost")),
            reply(text="The total is $125."),
        ]
        with patch.object(agent, "next_visible_event", return_value='{"event":"Sample event"}') as event, redirect_stdout(io.StringIO()) as output:
            answer = agent.resolve_tool_calls(
                client, "conversation", "astronomy-agent",
                reply(call("next_visible_event", {"location": "north_america"}, "event")),
            )
        self.assertEqual(answer, "The total is $125.")
        event.assert_called_once_with(location="north_america")
        requests = client.responses.create.call_args_list
        self.assertEqual([request.kwargs["input"][0]["call_id"] for request in requests], ["event", "cost"])
        self.assertEqual(json.loads(requests[1].kwargs["input"][0]["output"])["total_cost"], 125)
        self.assertTrue(all(request.kwargs["conversation"] == "conversation" for request in requests))
        self.assertIn("executing it in local Python", output.getvalue())
        self.assertEqual(output.getvalue().count("[Tool result]"), 2)

    def test_failed_incomplete_empty_and_unknown_tool_responses_are_errors(self):
        client = MagicMock()
        for response in (reply(status="failed"), reply(status="incomplete"), reply(text=" ")):
            with self.subTest(status=response.status, text=response.output_text), self.assertRaises(RuntimeError):
                agent.resolve_tool_calls(client, "conversation", "astronomy-agent", response)
        with self.assertRaisesRegex(ValueError, "unsupported local function"):
            agent.resolve_tool_calls(client, "conversation", "astronomy-agent", reply(call("unknown", {}, "unknown")))
        client.responses.create.assert_not_called()

    def run_main(self, prompts, response=None):
        project = MagicMock()
        project.__enter__.return_value = project
        client = project.get_openai_client.return_value
        client.__enter__.return_value = client
        project.agents.create_version.return_value = SimpleNamespace(name="astronomy-agent", version="42")
        client.conversations.create.return_value = SimpleNamespace(id="conversation")
        client.responses.create.return_value = response
        with patch.dict(os.environ, {"PROJECT_ENDPOINT": "https://example/api/projects/project", "MODEL_DEPLOYMENT_NAME": "model"}), patch.object(
            agent, "load_dotenv"
        ), patch.object(agent, "DefaultAzureCredential"), patch.object(
            agent, "AIProjectClient", return_value=project
        ), patch("builtins.input", side_effect=prompts), redirect_stdout(io.StringIO()) as output:
            if response is not None and response.status == "failed":
                with self.assertRaisesRegex(RuntimeError, "Service error"):
                    agent.main()
            else:
                agent.main()
        return project, client, output.getvalue()

    def test_blank_input_and_quit_do_not_invoke_model_and_delete_only_created_version(self):
        project, client, output = self.run_main(["", "quit"])
        client.responses.create.assert_not_called()
        project.agents.delete_version.assert_called_once_with(agent_name="astronomy-agent", agent_version="42")
        self.assertIn("No model request was sent", output)
        self.assertIn("[Complete]", output)

    def test_failed_model_request_still_cleans_up_without_announcing_completion(self):
        project, _, output = self.run_main(["Question"], reply(status="failed"))
        project.agents.delete_version.assert_called_once_with(agent_name="astronomy-agent", agent_version="42")
        self.assertIn("[Cleanup]", output)
        self.assertNotIn("[Complete]", output)


if __name__ == "__main__":
    unittest.main()
