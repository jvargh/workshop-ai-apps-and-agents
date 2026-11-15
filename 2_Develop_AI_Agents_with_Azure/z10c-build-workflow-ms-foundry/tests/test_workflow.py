import contextlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


spec = importlib.util.spec_from_file_location("lab_z10c_workflow", Path(__file__).parents[1] / "workflow.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def ticket(category="Technical", confidence=0.97, issue="Synthetic API issue"):
    return json.dumps({"category": category, "confidence": confidence, "customer_issue": issue})


class FormattingTests(unittest.TestCase):
    def output(self, text):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            count = workflow.print_workflow_output(text)
        return count, output.getvalue()

    def test_three_documented_categories(self):
        text = ticket() + "\nCheck permissions.\n" + ticket("General", 0.99) + "\nExport CSV.\n"
        text += ticket("Billing", 0.98) + "\nEscalate billing issue to human support team."
        count, output = self.output(text)
        self.assertEqual(count, 3)
        for expected in ("Ticket 1: Technical (97%", "Ticket 2: General (99%", "Ticket 3: Billing (98%"):
            self.assertIn(expected, output)
        self.assertIn("Escalate billing issue to human support team.", output)

    def test_braces_in_customer_issue(self):
        count, output = self.output(ticket(issue='API payload {"invoice": {"id": "synthetic"}}') + "\nResponse.")
        self.assertEqual(count, 1)
        self.assertIn('{"invoice": {"id": "synthetic"}}', output)

    def test_plain_text_is_preserved(self):
        self.assertEqual(self.output("Plain response"), (0, "Plain response\n"))

    def test_unknown_and_malformed_json_are_preserved(self):
        for text in ('{"other": {"nested": 1}}', "{not json", '{"category": "Billing"}'):
            with self.subTest(text=text):
                self.assertEqual(self.output(text), (0, text + "\n"))

    def test_invalid_confidence_is_preserved(self):
        for confidence in ("high", True, -0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(confidence=confidence):
                text = ticket(confidence=confidence)
                self.assertEqual(self.output(text), (0, text + "\n"))

    def test_intro_and_response_braces_are_preserved(self):
        count, output = self.output("Intro\n" + ticket() + "\nUse {example}; not JSON.")
        self.assertEqual(count, 1)
        self.assertIn("Intro", output)
        self.assertIn("Use {example}; not JSON.", output)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.conversations.create.return_value = SimpleNamespace(id="synthetic-conversation")
        self.stream = self.client.responses.create.return_value.__enter__.return_value
        self.stream.__iter__.return_value = iter([
            SimpleNamespace(type="response.created"),
            SimpleNamespace(type="response.completed", response=SimpleNamespace(id="synthetic-response")),
        ])
        self.client.responses.retrieve.return_value = SimpleNamespace(
            status="completed", output_text=ticket() + "\nSynthetic response."
        )
        self.output = io.StringIO()
        self.errors = io.StringIO()
        self.stdout = contextlib.redirect_stdout(self.output)
        self.stderr = contextlib.redirect_stderr(self.errors)
        self.stdout.__enter__()
        self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def assert_deleted(self):
        self.client.conversations.delete.assert_called_once_with(conversation_id="synthetic-conversation")

    def test_start_input_and_cleanup_on_success(self):
        workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()
        self.assertEqual(self.client.responses.create.call_args.kwargs["input"], "Start")
        self.assertEqual(
            self.client.responses.create.call_args.kwargs["extra_body"],
            {"agent_reference": {"name": "synthetic-workflow", "type": "agent_reference"}},
        )
        self.assertIn("Formatted ticket records: 1", self.output.getvalue())
        self.client.responses.create.return_value.__exit__.assert_called_once()

    def test_cleanup_when_create_response_fails(self):
        self.client.responses.create.side_effect = RuntimeError("response creation failed")
        with self.assertRaisesRegex(RuntimeError, "response creation failed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_failed_incomplete_and_error_events(self):
        for event_type in ("response.failed", "response.incomplete", "error"):
            with self.subTest(event_type=event_type):
                self.client.conversations.delete.reset_mock()
                self.stream.__iter__.return_value = iter([SimpleNamespace(type=event_type)])
                with self.assertRaisesRegex(RuntimeError, event_type):
                    workflow.run_workflow(self.client, "synthetic-workflow")
                self.assert_deleted()

    def test_stream_without_completion_fails(self):
        self.stream.__iter__.return_value = iter([])
        with self.assertRaisesRegex(RuntimeError, "without a response.completed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_empty_output_fails(self):
        self.client.responses.retrieve.return_value.output_text = " "
        with self.assertRaisesRegex(RuntimeError, "no text output"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_retrieval_failure_still_cleans_up(self):
        self.client.responses.retrieve.side_effect = RuntimeError("retrieve failed")
        with self.assertRaisesRegex(RuntimeError, "retrieve failed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_noncompleted_retrieved_status_fails(self):
        self.client.responses.retrieve.return_value.status = "failed"
        with self.assertRaisesRegex(RuntimeError, "not completed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_cleanup_failure_fails_successful_run(self):
        self.client.conversations.delete.side_effect = RuntimeError("cleanup failed")
        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assertIn("Conversation cleanup failed", self.errors.getvalue())

    def test_cleanup_failure_does_not_mask_run_failure(self):
        self.client.responses.create.side_effect = RuntimeError("original failure")
        self.client.conversations.delete.side_effect = RuntimeError("cleanup failed")
        with self.assertRaisesRegex(RuntimeError, "original failure"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assertIn("cleanup failed", self.errors.getvalue())

    def test_no_delete_if_conversation_creation_fails(self):
        self.client.conversations.create.side_effect = RuntimeError("conversation creation failed")
        with self.assertRaisesRegex(RuntimeError, "conversation creation failed"):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.client.conversations.delete.assert_not_called()

    def test_keyboard_interrupt_cleans_up(self):
        self.client.responses.create.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            workflow.run_workflow(self.client, "synthetic-workflow")
        self.assert_deleted()

    def test_main_success_and_clients_close(self):
        with (
            patch.object(workflow, "load_dotenv"),
            patch.dict(workflow.os.environ, {"PROJECT_ENDPOINT": "https://synthetic.invalid", "WORKFLOW_NAME": "synthetic"}),
            patch.object(workflow, "DefaultAzureCredential") as credential,
            patch.object(workflow, "AIProjectClient") as project,
            patch.object(workflow, "run_workflow") as run,
        ):
            self.assertEqual(workflow.main(), 0)
            run.assert_called_once()
            credential.return_value.__exit__.assert_called_once()
            project.return_value.__exit__.assert_called_once()
            project.return_value.__enter__.return_value.get_openai_client.return_value.__exit__.assert_called_once()

    def test_main_bad_configuration_returns_one(self):
        for endpoint in ("", "https://<resource>.services.ai.azure.com/api/projects/<project>"):
            with self.subTest(endpoint=endpoint):
                with (
                    patch.object(workflow, "load_dotenv"),
                    patch.dict(workflow.os.environ, {"PROJECT_ENDPOINT": endpoint}),
                    patch.object(workflow, "DefaultAzureCredential") as credential,
                ):
                    self.assertEqual(workflow.main(), 1)
                    credential.assert_not_called()

    def test_main_placeholder_workflow_returns_one(self):
        with (
            patch.object(workflow, "load_dotenv"),
            patch.dict(workflow.os.environ, {"PROJECT_ENDPOINT": "https://synthetic.invalid", "WORKFLOW_NAME": "<workflow>"}),
        ):
            self.assertEqual(workflow.main(), 1)

    def test_main_runtime_failure_and_interrupt_status(self):
        for error, expected in ((RuntimeError("synthetic startup failure"), 1), (KeyboardInterrupt(), 130)):
            with self.subTest(expected=expected):
                with (
                    patch.object(workflow, "load_dotenv"),
                    patch.dict(workflow.os.environ, {"PROJECT_ENDPOINT": "https://synthetic.invalid", "WORKFLOW_NAME": "synthetic"}),
                    patch.object(workflow, "DefaultAzureCredential", side_effect=error),
                ):
                    self.assertEqual(workflow.main(), expected)


if __name__ == "__main__":
    unittest.main()
