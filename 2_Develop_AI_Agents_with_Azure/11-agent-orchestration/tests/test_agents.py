"""Offline checks using real Agent Framework agents and SequentialBuilder."""

import asyncio
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

from agent_framework import AgentResponse, BaseChatClient, ChatResponse, Message


spec = importlib.util.spec_from_file_location("lab08_agents", Path(__file__).resolve().parents[1] / "agents.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class ScriptedChatClient(BaseChatClient):
    """Exercise real agent/middleware/workflow plumbing without network access."""

    def __init__(self, replies):
        super().__init__()
        self.replies = replies
        self.calls = []

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        async def respond():
            if stream:
                raise AssertionError("This lab uses non-streaming agent responses.")
            self.calls.append(list(messages))
            reply = self.replies[len(self.calls) - 1]
            if isinstance(reply, Exception):
                raise reply
            return ChatResponse(messages=Message("assistant", [reply]))

        return respond()


class Resource:
    def __init__(self, name, events, fail_close=False):
        self.name, self.events, self.fail_close = name, events, fail_close

    async def __aenter__(self):
        self.events.append(f"open:{self.name}")
        return self

    async def __aexit__(self, *_):
        self.events.append(f"close:{self.name}")
        if self.fail_close:
            raise RuntimeError(f"{self.name} cleanup failed")


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def run_sample(self, sample, replies):
        client = ScriptedChatClient(replies)
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            results = await lab.run_feedback(client, lab.SAMPLES[sample])
        return results, client.calls, capture.getvalue()

    async def test_positive_order_context_and_outputs(self):
        summary = "The customer praises prompt, polite support that quickly restored account access."
        action = "Share the praise for prompt account-access support with the support team."
        results, calls, output = await self.run_sample("positive", [summary, "Positive", action])
        self.assertEqual(tuple(results), lab.STAGES)
        self.assertEqual(results, {"summarizer": summary, "classifier": "Positive", "action": action})
        self.assertEqual(len(calls), 3)
        # Check real builder context propagation, not just nonempty mock responses.
        for call in calls:
            self.assertTrue(any(lab.SAMPLES["positive"] in message.text for message in call))
        self.assertTrue(any(message.text == summary for message in calls[1]))
        self.assertTrue(any(message.text == summary for message in calls[2]))
        self.assertTrue(any(message.text == "Positive" for message in calls[2]))
        positions = [output.index(f"[{number}/3] {stage}: starting") for number, stage in enumerate(lab.STAGES, 1)]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(output.index("summarizer: completed"), positions[1])
        self.assertLess(output.index("classifier: completed"), positions[2])
        self.assertEqual(output.count("Intermediate result ["), 2)
        self.assertEqual(output.count("Final recommendation ["), 1)
        self.assertIn(f"Final recommendation [action]: {action}", output)

    async def test_negative_meaning_and_context(self):
        summary = "Photo uploads repeatedly crash the app and lose the photos."
        action = "Investigate the repeated photo-upload crashes and data loss."
        results, calls, _ = await self.run_sample("negative", [summary, "Negative", action])
        self.assertEqual(results["classifier"], "Negative")
        self.assertIn("crash", results["summarizer"])
        self.assertIn("data loss", results["action"])
        self.assertTrue(any(message.text == summary for message in calls[2]))
        self.assertTrue(any(message.text == "Negative" for message in calls[2]))

    async def test_feature_request_is_not_generic_praise(self):
        summary = "The customer requests dashboard dark mode to reduce eye strain at night."
        action = "Consider adding a dashboard dark mode option to the product backlog."
        results, calls, _ = await self.run_sample("feature-request", [summary, "Feature request", action])
        self.assertEqual(results["classifier"], "Feature request")
        self.assertIn("dark mode", results["summarizer"])
        self.assertIn("dark mode", results["action"])
        self.assertTrue(any(message.text == "Feature request" for message in calls[2]))

    async def test_invalid_classification_stops_before_action(self):
        client = ScriptedChatClient(["Support resolved account access quickly.", "Satisfied", "Never used"])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "classifier must return exactly"):
            await lab.run_feedback(client, lab.SAMPLES["positive"])
        self.assertEqual(len(client.calls), 2)

    async def test_empty_summary_stops_before_classifier(self):
        client = ScriptedChatClient(["   "])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "summarizer returned no text"):
            await lab.run_feedback(client, lab.SAMPLES["positive"])
        self.assertEqual(len(client.calls), 1)

    async def test_empty_action_is_failure(self):
        client = ScriptedChatClient(["Support promptly restored access.", "Positive", ""])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "action returned no text"):
            await lab.run_feedback(client, lab.SAMPLES["positive"])
        self.assertEqual(len(client.calls), 3)

    async def test_provider_failure_stops_workflow(self):
        client = ScriptedChatClient([RuntimeError("Synthetic provider failure")])
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(RuntimeError, "Synthetic provider failure"):
            await lab.run_feedback(client, lab.SAMPLES["positive"])
        self.assertEqual(len(client.calls), 1)
        self.assertNotIn("completed", output.getvalue())
        self.assertNotIn("Final recommendation", output.getvalue())

    async def test_no_outputs_is_failure(self):
        workflow = AsyncMock()
        workflow.run.return_value = Mock()
        workflow.run.return_value.get_outputs.return_value = []
        workflow.run.return_value.get_intermediate_outputs.return_value = []
        with patch.object(lab, "SequentialBuilder") as builder:
            builder.return_value.build.return_value = workflow
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "did not produce"):
                await lab.run_feedback(ScriptedChatClient([]), lab.SAMPLES["positive"])


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def run_main(self, replies, *, fail_close=False, timeout=False):
        events = []
        credential = Resource("credential", events)
        project = Resource("project", events)
        client = ScriptedChatClient(replies)
        client.client = Resource("openai", events, fail_close=fail_close)
        patches = (
            patch.object(lab, "get_configuration", return_value=("https://<resource>/api/projects/<project>", "<deployment>")),
            patch.object(lab, "AzureCliCredential", return_value=credential),
            patch.object(lab, "AIProjectClient", return_value=project),
            patch.object(lab, "FoundryChatClient", return_value=client),
        )
        output = io.StringIO()
        with contextlib.ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            stack.enter_context(contextlib.redirect_stdout(output))
            if timeout:
                async def slow(*_):
                    await asyncio.sleep(1)
                stack.enter_context(patch.object(lab, "run_feedback", side_effect=slow))
                stack.enter_context(patch.object(lab, "WORKFLOW_TIMEOUT_SECONDS", 0.01))
            error = None
            try:
                await lab.main()
            except Exception as exc:
                error = exc
        return events, output.getvalue(), error

    async def test_success_closes_all_owned_clients(self):
        events, output, error = await self.run_main(["Support promptly restored access.", "Positive", "Share the praise with support."])
        self.assertIsNone(error)
        self.assertEqual(events, ["open:credential", "open:project", "open:openai", "close:openai", "close:project", "close:credential"])
        self.assertIn("[Complete] 3/3 stages", output)
        self.assertIn("no remote agent/workflow was created", output)

    async def test_failed_model_call_still_closes_clients(self):
        events, output, error = await self.run_main([RuntimeError("Synthetic model failure")])
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(events[-3:], ["close:openai", "close:project", "close:credential"])
        self.assertIn("[Cleanup] Closing", output)
        self.assertNotIn("[Complete]", output)

    async def test_cleanup_failure_cannot_report_success(self):
        events, output, error = await self.run_main(["Support restored access.", "Positive", "Share the praise."], fail_close=True)
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(events[-3:], ["close:openai", "close:project", "close:credential"])
        self.assertNotIn("[Complete]", output)
        self.assertNotIn("SDK clients and credential closed", output)

    async def test_timeout_closes_clients_without_completion(self):
        events, output, error = await self.run_main([], timeout=True)
        self.assertIsInstance(error, TimeoutError)
        self.assertEqual(events[-3:], ["close:openai", "close:project", "close:credential"])
        self.assertNotIn("[Complete]", output)


class ContractAndCliTests(unittest.TestCase):
    def test_valid_labels_are_accepted(self):
        for label in lab.CLASSIFICATIONS:
            with self.subTest(label=label):
                response = AgentResponse(messages=Message("assistant", [label]))
                self.assertEqual(lab.response_text(response, "classifier"), label)

    def test_non_response_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "AgentResponse"):
            lab.response_text("Positive", "classifier")

    def test_user_message_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "assistant messages"):
            lab.response_text(AgentResponse(messages=Message("user", ["Positive"])), "classifier")

    def test_configuration_reports_missing_keys_without_values(self):
        with patch.object(lab, "load_dotenv"), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME"):
                lab.get_configuration()

    def test_configuration_uses_lab_env_without_overrides(self):
        with patch.object(lab, "load_dotenv") as load, patch.dict(
            os.environ, {"AZURE_AI_PROJECT_ENDPOINT": "https://synthetic.invalid/api/projects/synthetic", "AZURE_AI_MODEL_DEPLOYMENT_NAME": "synthetic"}, clear=True
        ):
            self.assertEqual(lab.get_configuration(), ("https://synthetic.invalid/api/projects/synthetic", "synthetic"))
            load.assert_called_once_with(Path(lab.__file__).with_name(".env"), override=False)

    def test_placeholder_configuration_is_rejected(self):
        with patch.object(lab, "load_dotenv"), patch.dict(
            os.environ, {"AZURE_AI_PROJECT_ENDPOINT": "https://<resource>/api/projects/<project>", "AZURE_AI_MODEL_DEPLOYMENT_NAME": "<deployment>"}, clear=True
        ):
            with self.assertRaisesRegex(ValueError, "placeholders"):
                lab.get_configuration()

    def test_cli_defaults_to_original_positive_sample(self):
        with patch.object(sys, "argv", ["agents.py"]), patch.object(lab, "main", new_callable=AsyncMock) as main:
            self.assertEqual(lab.run_cli(), 0)
            main.assert_awaited_once_with("positive")

    def test_cli_selects_feature_request(self):
        with patch.object(sys, "argv", ["agents.py", "--sample", "feature-request"]), patch.object(lab, "main", new_callable=AsyncMock) as main:
            self.assertEqual(lab.run_cli(), 0)
            main.assert_awaited_once_with("feature-request")

    def test_cli_failure_returns_one(self):
        error = io.StringIO()
        with patch.object(sys, "argv", ["agents.py"]), patch.object(lab, "main", new_callable=AsyncMock, side_effect=RuntimeError("Synthetic failure")), contextlib.redirect_stderr(error):
            self.assertEqual(lab.run_cli(), 1)
        self.assertIn("[Failed] RuntimeError: Synthetic failure", error.getvalue())

    def test_cli_timeout_returns_one(self):
        error = io.StringIO()
        with patch.object(sys, "argv", ["agents.py"]), patch.object(lab, "main", new_callable=AsyncMock, side_effect=TimeoutError), contextlib.redirect_stderr(error):
            self.assertEqual(lab.run_cli(), 1)
        self.assertIn("partial stages are not success", error.getvalue())

    def test_cli_cancellation_returns_130(self):
        error = io.StringIO()
        with patch.object(sys, "argv", ["agents.py"]), patch.object(lab, "main", new_callable=AsyncMock, side_effect=asyncio.CancelledError), contextlib.redirect_stderr(error):
            self.assertEqual(lab.run_cli(), 130)
        self.assertIn("[Failed] Run interrupted", error.getvalue())

    def test_unknown_sample_is_not_silently_replaced(self):
        with patch.object(sys, "argv", ["agents.py", "--sample", "unknown"]), patch.object(lab, "main", new_callable=AsyncMock) as main, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_info:
                lab.run_cli()
        self.assertEqual(exit_info.exception.code, 2)
        main.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
