import asyncio
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
import importlib.util
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lab_common


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


chat = module("sync_chat", "03-foundry-sdk/chat-app.py")
async_chat = module("async_chat", "03-foundry-sdk/chat-async.py")
safety = module("safety", "05-responsible-ai-content-filters/audit-guardrails.py")
evaluation = module("evaluation", "02-model-catalog-evaluation/evaluate-models.py")
project_check = module("project_check", "01-plan-and-prepare/verify-project.py")
tools_app = module("tools_app", "04-tools/tools-app.py")


def response(identifier="response-1", text="answer"):
    return SimpleNamespace(id=identifier, status="completed", output_text=text)


class ConfigurationTests(unittest.TestCase):
    def test_rejects_missing_and_placeholder_values(self):
        for value in ("", "your-deployment", "<resource>"):
            with self.subTest(value=value), patch.dict(os.environ, {"TEST_KEY": value}):
                with self.assertRaises(ValueError):
                    lab_common.required("TEST_KEY")

    def test_resource_endpoint_and_deployment(self):
        with patch.object(lab_common, "load_dotenv"), patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/openai/v1",
            "MODEL_DEPLOYMENT": "model",
        }):
            _, endpoint, model = lab_common.load_config(__file__)
            self.assertTrue(endpoint.endswith("/openai/v1/"))
            self.assertEqual(model, "model")

    def test_rejects_wrong_endpoint_shapes(self):
        endpoints = [
            "http://example/openai/v1/", "https://example/",
            "https://example/api/projects/project", "https://example/openai/v1/?key=x",
            "https://user:password@example/openai/v1/", "https://example/openai/v1/#x",
        ]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint), patch.object(lab_common, "load_dotenv"), patch.dict(
                os.environ, {"AZURE_OPENAI_ENDPOINT": endpoint, "MODEL_DEPLOYMENT": "model"}
            ):
                with self.assertRaises(ValueError):
                    lab_common.load_config(__file__)

    def test_response_must_be_completed_and_nonempty(self):
        self.assertEqual(lab_common.completed_text(response(text=" answer ")), "answer")
        for value in (SimpleNamespace(status="failed", error="failed"), response(text=" ")):
            with self.assertRaises(RuntimeError):
                lab_common.completed_text(value)

    def test_failures_have_nonzero_exit(self):
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(lab_common.run(lambda: (_ for _ in ()).throw(ValueError("bad"))), 1)
            self.assertIn("Lab failed: bad", stderr.getvalue())


class ProjectValidationTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.output = self.enterContext(redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(
            project_check, "load_config", return_value=(self.folder, "endpoint", "model")
        ))
        self.enterContext(patch.object(project_check, "DefaultAzureCredential"))
        self.enterContext(patch.object(project_check, "account_path", return_value="/accounts/test"))
        self.enterContext(patch.object(project_check, "required", return_value="project"))
        self.arm = self.enterContext(patch.object(project_check, "arm_get", side_effect=[
            {"location": "test-region"},
            {"properties": {"provisioningState": "Succeeded"}},
            {"value": [{
                "name": "model",
                "properties": {"provisioningState": "Succeeded", "model": {"name": "test-model"}},
            }]},
        ]))
        client_context = self.enterContext(patch.object(project_check, "model_client"))
        self.client = client_context.return_value.__enter__.return_value
        self.reply = response()
        self.reply.usage = MagicMock()
        self.reply.usage.model_dump.return_value = {"total_tokens": 10}
        self.client.responses.create.return_value = self.reply

    def test_progress_precedes_inference_and_success_follows_report_save(self):
        def infer(**kwargs):
            output = self.output.getvalue()
            self.assertIn(f"Prompt: {kwargs['input']}", output)
            self.assertIn("Waiting for the model response...", output)
            self.assertNotIn("Validation completed successfully.", output)
            return self.reply

        def save(folder, name, report):
            self.assertIn("Saving the validation results", self.output.getvalue())
            self.assertNotIn("Validation completed successfully.", self.output.getvalue())
            return lab_common.save_report(folder, name, report)

        self.client.responses.create.side_effect = infer
        with patch.object(project_check, "save_report", side_effect=save):
            project_check.main()

        output = self.output.getvalue()
        self.assertEqual(re.findall(r"\[(\d)/8\]", output), [str(n) for n in range(1, 9)])
        self.assertIn("Model response:\nanswer", output)
        self.assertLess(output.index("Saved local report:"), output.index("Validation completed successfully."))
        report = json.loads((self.folder / "results" / "project-validation.json").read_text())
        self.assertEqual(report["response"], "answer")
        self.assertEqual(report["usage"], {"total_tokens": 10})
        self.assertFalse(report["new_resources_created"])
        self.assertFalse(report["portal_and_toolkit_ui_validated"])
        self.assertEqual(self.arm.call_count, 3)
        self.client.responses.create.assert_called_once_with(
            model="model",
            instructions="You are an AI assistant that provides advice about AI software development.",
            input="Describe three key considerations for working with Large Language Models for AI application development.",
        )

    def test_failed_inference_does_not_report_success_or_save_results(self):
        self.client.responses.create.side_effect = RuntimeError("Model unavailable")
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(lab_common.run(project_check.main), 1)
        self.assertIn("Model unavailable", stderr.getvalue())
        self.assertIn("[7/8]", self.output.getvalue())
        self.assertNotIn("[8/8]", self.output.getvalue())
        self.assertNotIn("Validation completed successfully.", self.output.getvalue())
        self.assertFalse((self.folder / "results").exists())

    def test_report_write_failure_does_not_report_success(self):
        with patch.object(project_check, "save_report", side_effect=OSError("Disk full")), patch(
            "sys.stderr", new_callable=io.StringIO
        ) as stderr:
            self.assertEqual(lab_common.run(project_check.main), 1)
        self.assertIn("Disk full", stderr.getvalue())
        self.assertIn("[8/8]", self.output.getvalue())
        self.assertNotIn("Validation completed successfully.", self.output.getvalue())


class ChatTests(unittest.TestCase):
    def exercise(self, arguments):
        client = MagicMock()
        client.responses.create.side_effect = [response("first"), response("second")]
        client.chat.completions.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="answer"))
        ])

        @contextmanager
        def fake_client(_):
            yield client

        with patch.object(chat, "load_config", return_value=(ROOT, "endpoint", "model")), patch.object(
            chat, "model_client", fake_client
        ), patch("sys.argv", ["chat-app.py", *arguments]), patch(
            "builtins.input", side_effect=["", "first question", "follow-up", "QUIT"]
        ), redirect_stdout(io.StringIO()):
            chat.main()
        return client

    def test_responses_preserve_history(self):
        calls = self.exercise([]).responses.create.call_args_list
        self.assertIsNone(calls[0].kwargs["previous_response_id"])
        self.assertEqual(calls[1].kwargs["previous_response_id"], "first")

    def test_no_history_makes_independent_requests(self):
        calls = self.exercise(["--no-history"]).responses.create.call_args_list
        self.assertTrue(all(call.kwargs["previous_response_id"] is None for call in calls))

    def test_chat_completions_preserve_full_messages(self):
        calls = self.exercise(["--api", "chat-completions"]).chat.completions.create.call_args_list
        self.assertEqual([x["role"] for x in calls[1].kwargs["messages"]],
                         ["system", "user", "assistant", "user"])

    def test_chat_completions_can_disable_history(self):
        calls = self.exercise(["--api", "chat-completions", "--no-history"]).chat.completions.create.call_args_list
        self.assertTrue(all(len(call.kwargs["messages"]) == 2 for call in calls))

    def test_progress_precedes_requests_and_keeps_streamed_text_contiguous(self):
        for arguments, api_name in (
            ([], "Responses"), (["--no-history"], "Responses"),
            (["--stream"], "Responses"), (["--api", "chat-completions"], "Chat Completions"),
        ):
            with self.subTest(arguments=arguments), patch.object(
                chat, "load_config", return_value=(ROOT, "endpoint", "model")
            ), patch.object(chat, "model_client") as factory, patch(
                "sys.argv", ["chat-app.py", *arguments]
            ), patch("builtins.input", side_effect=["", "question", EOFError]), redirect_stdout(
                io.StringIO()
            ) as output:
                client = factory.return_value.__enter__.return_value
                reply = response(text="hello world")
                stream = MagicMock()
                stream.__iter__.return_value = iter([
                    SimpleNamespace(type="response.output_text.delta", delta="hello "),
                    SimpleNamespace(type="response.output_text.delta", delta="world"),
                    SimpleNamespace(type="response.completed", response=reply),
                ])

                def create(**kwargs):
                    self.assertIn(f"[Request] Sending prompt using {api_name}", output.getvalue())
                    self.assertIn("may incur inference charges", output.getvalue())
                    self.assertIn("[History]", output.getvalue())
                    self.assertNotIn("[Response]", output.getvalue())
                    if api_name == "Chat Completions":
                        return SimpleNamespace(choices=[
                            SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="hello world"))
                        ])
                    return stream if kwargs["stream"] else reply

                client.responses.create.side_effect = create
                client.chat.completions.create.side_effect = create
                chat.main()
                text = output.getvalue()
                self.assertIn("No model request was sent.", text)
                self.assertIn("End of input received.", text)
                self.assertLess(text.index("[Cleanup]"), text.index("[Exit] Chat session closed."))
                if "--stream" in arguments:
                    self.assertIn("hello world\n[Response] Stream completed and text validated.", text)
                else:
                    self.assertIn("[Response] Model answer:\nhello world", text)
                if "--no-history" in arguments:
                    self.assertIn("The next prompt will be independent of this turn.", text)
                    self.assertNotIn("Context updated for the next prompt", text)
                else:
                    self.assertIn("Context updated for the next prompt", text)
                self.assertEqual(
                    client.responses.create.call_count + client.chat.completions.create.call_count, 1
                )

    def stream(self, events):
        stream = MagicMock()
        stream.__iter__.return_value = iter(events)
        with redirect_stdout(io.StringIO()):
            return chat.stream_text(stream)

    def test_stream_requires_completion(self):
        events = [SimpleNamespace(type="response.output_text.delta", delta="answer"),
                  SimpleNamespace(type="response.completed", response=response("finished"))]
        self.assertEqual(self.stream(events), "finished")
        with self.assertRaises(RuntimeError):
            self.stream(events[:1])

    def test_stream_rejects_service_errors(self):
        for kind in ("response.failed", "response.incomplete", "error"):
            with self.subTest(kind=kind), self.assertRaises(RuntimeError):
                self.stream([SimpleNamespace(type=kind)])

    def test_async_history_and_cleanup(self):
        credential = MagicMock()
        credential.__aenter__ = AsyncMock(return_value=credential)
        credential.__aexit__ = AsyncMock(return_value=None)
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        replies = iter([response("first"), response("second")])

        async def create(**kwargs):
            self.assertIn("[Request] Sending prompt using async Responses.", output.getvalue())
            if kwargs["previous_response_id"] is None:
                self.assertIn("First turn: no previous response context.", output.getvalue())
            else:
                self.assertIn("Reusing the previous response context", output.getvalue())
            return next(replies)

        client.responses.create = AsyncMock(side_effect=create)
        with patch.object(async_chat, "load_config", return_value=(ROOT, "endpoint", "model")), patch.object(
            async_chat, "DefaultAzureCredential", return_value=credential
        ), patch.object(async_chat, "AsyncOpenAI", return_value=client), patch.object(
            async_chat, "get_bearer_token_provider", return_value="token-provider"
        ), patch("builtins.input", side_effect=["", "question", "follow-up", "quit"]), redirect_stdout(
            io.StringIO()
        ) as output:
            asyncio.run(async_chat.main())
        self.assertIn("[Mode] Async Responses API", output.getvalue())
        self.assertIn("[Response] Model answer:\nanswer", output.getvalue())
        self.assertIn("[Exit] Chat session closed.", output.getvalue())
        self.assertEqual(client.responses.create.await_count, 2)
        self.assertEqual(client.responses.create.call_args_list[1].kwargs["previous_response_id"], "first")
        client.__aexit__.assert_awaited_once()
        credential.__aexit__.assert_awaited_once()

    def test_async_failed_response_is_not_announced_as_completed(self):
        credential = MagicMock()
        credential.__aenter__ = AsyncMock(return_value=credential)
        credential.__aexit__ = AsyncMock(return_value=None)
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.responses.create = AsyncMock(return_value=SimpleNamespace(status="failed", error="service error"))
        with patch.object(async_chat, "load_config", return_value=(ROOT, "endpoint", "model")), patch.object(
            async_chat, "DefaultAzureCredential", return_value=credential
        ), patch.object(async_chat, "AsyncOpenAI", return_value=client), patch.object(
            async_chat, "get_bearer_token_provider", return_value="token-provider"
        ), patch("builtins.input", return_value="question"), redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, "service error"):
                asyncio.run(async_chat.main())
        self.assertIn("[Request]", output.getvalue())
        self.assertNotIn("[Response] Model answer:", output.getvalue())
        self.assertNotIn("Context updated for the next prompt", output.getvalue())
        self.assertNotIn("[Exit] Chat session closed.", output.getvalue())
        client.__aexit__.assert_awaited_once()
        credential.__aexit__.assert_awaited_once()


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        brochures = self.folder / "brochures"
        brochures.mkdir()
        for name in ("Rome", "San Francisco"):
            (brochures / f"{name}.pdf").write_bytes(b"%PDF-1.4\n")
        self.output = self.enterContext(redirect_stdout(io.StringIO()))
        self.input = self.enterContext(patch("builtins.input", return_value="quit"))
        self.enterContext(patch("sys.argv", ["tools-app.py"]))
        self.enterContext(patch.object(tools_app, "load_config", return_value=(self.folder, "endpoint", "model")))
        self.factory = self.enterContext(patch.object(tools_app, "model_client"))
        self.client = self.factory.return_value.__enter__.return_value
        self.client.vector_stores.create.return_value = SimpleNamespace(id="store")
        self.client.files.create.side_effect = [SimpleNamespace(id=f"file-{n}") for n in range(2)]
        self.client.files.delete.return_value = SimpleNamespace(deleted=True)
        self.client.vector_stores.delete.return_value = SimpleNamespace(deleted=True)
        self.client.vector_stores.file_batches.create_and_poll.return_value = SimpleNamespace(
            status="completed", file_counts=SimpleNamespace(completed=2)
        )

    def reply(self, identifier, kind=None, annotations=()):
        reply = response(identifier)
        reply.output = [
            SimpleNamespace(type="message", content=[
                SimpleNamespace(type="output_text", annotations=annotations)
            ]),
        ]
        if kind is not None:
            reply.output.insert(0, SimpleNamespace(type=kind, status="completed", results=[
                SimpleNamespace(filename="San Francisco.pdf", file_id="file-1")
            ] if kind == "file_search_call" else None))
        return reply

    def test_chat_preserves_context_and_reports_actual_tools_and_citations(self):
        replies = iter([
            self.reply("web", "web_search_call", [
                SimpleNamespace(type="url_citation", title="Events", url="https://example.com/events")
            ]),
            self.reply("files", "file_search_call", [
                SimpleNamespace(type="file_citation", filename="San Francisco.pdf", file_id="file-1")
            ]),
        ])
        self.input.side_effect = ["", "What is happening in San Francisco next month?", "What hotels are offered there?", "QUIT"]

        def create(**kwargs):
            self.assertIn("[Request] Sending prompt using Responses.", self.output.getvalue())
            return next(replies)

        self.client.responses.create.side_effect = create
        results = tools_app.chat(self.client, "model", "store")
        calls = self.client.responses.create.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIsNone(calls[0].kwargs["previous_response_id"])
        self.assertEqual(calls[1].kwargs["previous_response_id"], "web")
        self.assertEqual(calls[0].kwargs["tools"], [
            {"type": "file_search", "vector_store_ids": ["store"]}, {"type": "web_search"},
        ])
        self.assertEqual(calls[0].kwargs["include"], ["file_search_call.results"])
        self.assertTrue(all(call.kwargs["instructions"] == tools_app.INSTRUCTIONS for call in calls))
        self.assertEqual(results[0]["tool_calls"][0]["type"], "web_search_call")
        self.assertEqual(results[1]["citations"][0]["filename"], "San Francisco.pdf")
        self.assertEqual(results[1]["tool_calls"][0]["files"][0]["filename"], "San Francisco.pdf")
        self.assertIn("[Retrieved] Brochure: San Francisco.pdf", self.output.getvalue())
        self.assertIn("No model request was sent.", self.output.getvalue())
        self.assertIn("[Source] Events: https://example.com/events", self.output.getvalue())

    def test_response_without_tool_call_does_not_claim_search_was_used(self):
        calls, citations = tools_app.response_evidence(self.reply("plain"))
        self.assertEqual((calls, citations), ([], []))
        self.assertIn("No search tool was called", self.output.getvalue())

    def test_failed_search_call_is_an_error(self):
        reply = self.reply("failed", "file_search_call")
        reply.output[0].status = "failed"
        with self.assertRaisesRegex(RuntimeError, "Search tool did not complete"):
            tools_app.response_evidence(reply)

    def test_successful_session_saves_report_only_after_resource_cleanup(self):
        self.input.side_effect = ["Brochure hotels?", "quit"]
        self.client.responses.create.return_value = self.reply("files", "file_search_call")

        def save(folder, name, report):
            self.assertEqual(self.client.files.delete.call_count, 2)
            self.client.vector_stores.delete.assert_called_once_with("store")
            return lab_common.save_report(folder, name, report)

        with patch.object(tools_app, "save_report", side_effect=save):
            tools_app.main()
        report = json.loads((self.folder / "results" / "tools-chat.json").read_text())
        self.assertTrue(report["temporary_resources_deleted"])
        self.assertEqual(report["responses"][0]["tool_calls"][0]["type"], "file_search_call")
        for call in self.client.files.create.call_args_list:
            self.assertTrue(call.kwargs["file"].closed)

    def test_upload_failure_closes_files_and_deletes_only_created_resources(self):
        self.client.files.create.side_effect = [SimpleNamespace(id="first"), RuntimeError("Upload failed")]
        with self.assertRaisesRegex(RuntimeError, "Upload failed"):
            tools_app.main()
        self.client.files.delete.assert_called_once_with("first")
        self.client.vector_stores.delete.assert_called_once_with("store")
        self.assertTrue(all(call.kwargs["file"].closed for call in self.client.files.create.call_args_list))
        self.assertFalse((self.folder / "results").exists())

    def test_partial_indexing_fails_before_chat_and_cleans_up(self):
        self.client.vector_stores.file_batches.create_and_poll.return_value.file_counts.completed = 1
        with self.assertRaisesRegex(RuntimeError, "completed=1/2"):
            tools_app.main()
        self.input.assert_not_called()
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.client.files.delete.call_count, 2)
        self.client.vector_stores.delete.assert_called_once_with("store")

    def test_cleanup_failure_still_attempts_other_deletions_without_success(self):
        self.client.files.delete.side_effect = [RuntimeError("Cleanup failed"), SimpleNamespace(deleted=True)]
        with self.assertRaisesRegex(RuntimeError, "Cleanup failed"):
            tools_app.main()
        self.assertEqual(self.client.files.delete.call_count, 2)
        self.client.vector_stores.delete.assert_called_once_with("store")
        self.assertNotIn("[Complete]", self.output.getvalue())
        self.assertFalse((self.folder / "results").exists())

    def test_missing_brochures_fails_before_connecting(self):
        for path in (self.folder / "brochures").glob("*.pdf"):
            path.unlink()
        with self.assertRaisesRegex(ValueError, "No PDF brochures"):
            tools_app.main()
        self.factory.assert_not_called()

    def test_quit_without_questions_cleans_up_without_saving_a_transcript(self):
        tools_app.main()
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.client.files.delete.call_count, 2)
        self.client.vector_stores.delete.assert_called_once_with("store")
        self.assertFalse((self.folder / "results").exists())


class GuardrailTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "05-responsible-ai-content-filters/guardrail-policy.json").read_text())

    def test_all_eight_category_source_pairs(self):
        self.assertEqual(len(self.policy["properties"]["contentFilters"]), 8)
        for mode in ("Blocking", "Default"):
            with self.subTest(mode=mode):
                policy = deepcopy(self.policy)
                policy["properties"]["mode"] = mode
                self.assertTrue(safety.validate_strict_policy(policy))

    def test_each_filter_must_be_present(self):
        for index in range(8):
            policy = deepcopy(self.policy)
            policy["properties"]["contentFilters"].pop(index)
            with self.subTest(index=index), self.assertRaises(ValueError):
                safety.validate_strict_policy(policy)

    def test_each_filter_must_block_low_severity(self):
        for mode in ("Blocking", "Default"):
            for key, value in (("enabled", False), ("blocking", False),
                               ("enabled", "true"), ("severityThreshold", "Medium")):
                policy = deepcopy(self.policy)
                policy["properties"]["mode"] = mode
                policy["properties"]["contentFilters"][0][key] = value
                with self.subTest(mode=mode, key=key, value=value), self.assertRaises(ValueError):
                    safety.validate_strict_policy(policy)

    def test_blocking_mode_and_unique_filters(self):
        for mode in ("Asynchronous_filter", "Deferred", "unknown", None):
            policy = deepcopy(self.policy)
            policy["properties"]["mode"] = mode
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                safety.validate_strict_policy(policy)
        policy = deepcopy(self.policy)
        policy["properties"]["contentFilters"].append(policy["properties"]["contentFilters"][0])
        with self.assertRaises(ValueError):
            safety.validate_strict_policy(policy)


class GuardrailAuditTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.template = json.loads((ROOT / "05-responsible-ai-content-filters/guardrail-policy.json").read_text())
        (self.folder / "guardrail-policy.json").write_text(json.dumps(self.template))
        self.output = self.enterContext(redirect_stdout(io.StringIO()))
        self.enterContext(patch("sys.argv", ["audit-guardrails.py"]))
        self.enterContext(patch.object(safety, "load_config", return_value=(self.folder, "endpoint", "model")))
        self.enterContext(patch.object(safety, "DefaultAzureCredential"))
        self.enterContext(patch.object(safety, "account_path", return_value="/accounts/test"))
        self.arm = self.enterContext(patch.object(safety, "arm_get", side_effect=[
            {"properties": {"raiPolicyName": "custom-policy"}}, self.template,
        ]))
        self.factory = self.enterContext(patch.object(safety, "model_client"))
        self.client = self.factory.return_value.__enter__.return_value
        self.raw = {
            "choices": [{"finish_reason": "stop", "message": {"content": "Sightseeing answer"}}]
        }
        self.client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="Sightseeing answer"))],
            model_dump=lambda: self.raw,
        )

    def test_progress_precedes_inference_and_completion_follows_report_save(self):
        reply = self.client.chat.completions.create.return_value

        def create(**kwargs):
            self.assertIn(f"Prompt: {kwargs['messages'][0]['content']}", self.output.getvalue())
            self.assertIn("Waiting for the model response...", self.output.getvalue())
            self.assertNotIn("[7/8]", self.output.getvalue())
            return reply

        def save(folder, name, report):
            self.assertIn("[8/8]", self.output.getvalue())
            self.assertNotIn("[Complete]", self.output.getvalue())
            return lab_common.save_report(folder, name, report)

        self.client.chat.completions.create.side_effect = create
        with patch.object(safety, "save_report", side_effect=save):
            safety.main()
        text = self.output.getvalue()
        self.assertEqual(re.findall(r"\[(\d)/8\]", text), [str(n) for n in range(1, 9)])
        self.assertIn("Skipping applied strict-policy checks", text)
        self.assertLess(text.index("Saved local report:"), text.index("[Complete]"))
        report = json.loads((self.folder / "results" / "guardrail-audit.json").read_text())
        self.assertFalse(report["strict_guardrail_verified"])
        self.assertFalse(report["shared_settings_changed"])
        self.assertFalse(report["harmful_prompts_executed"])
        self.assertEqual(report["smoke_response"], self.raw)
        self.client.chat.completions.create.assert_called_once_with(
            model="model",
            messages=[{"role": "user", "content": "Suggest three safe daytime sightseeing activities in Rome."}],
        )

    def test_expected_custom_policy_is_checked_before_inference(self):
        self.template["properties"]["mode"] = "Default"
        self.template["properties"]["contentFilters"].append({
            "name": "Indirect Attack", "source": "Prompt", "enabled": True, "blocking": False,
        })
        with patch("sys.argv", ["audit-guardrails.py", "--expect-policy", "custom-policy"]):
            safety.main()
        self.assertIn("Applied custom policy passed", self.output.getvalue())
        report = json.loads((self.folder / "results" / "guardrail-audit.json").read_text())
        self.assertTrue(report["strict_guardrail_verified"])
        self.assertEqual(report["policy_mode"], "Default")

    def test_builtin_404_remains_an_explicit_limitation_not_strict_success(self):
        error = safety.requests.HTTPError(response=SimpleNamespace(status_code=404))
        self.arm.side_effect = [{"properties": {"raiPolicyName": "Microsoft.DefaultV2"}}, error]
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            safety.main()
        self.assertIn("Thresholds are NOT verified", stderr.getvalue())
        self.assertNotIn("Applied custom policy passed", self.output.getvalue())
        report = json.loads((self.folder / "results" / "guardrail-audit.json").read_text())
        self.assertFalse(report["policy_definition_available"])
        self.assertFalse(report["strict_guardrail_verified"])

    def test_wrong_assignment_fails_before_inference_or_completion(self):
        with patch("sys.argv", ["audit-guardrails.py", "--expect-policy", "other-policy"]):
            with self.assertRaisesRegex(ValueError, "Expected policy other-policy"):
                safety.main()
        self.assertIn("[4/8]", self.output.getvalue())
        self.factory.assert_not_called()
        self.assertNotIn("[Complete]", self.output.getvalue())

    def test_invalid_applied_policy_fails_before_inference(self):
        self.template["properties"]["contentFilters"][0]["severityThreshold"] = "Medium"
        with patch("sys.argv", ["audit-guardrails.py", "--expect-policy", "custom-policy"]):
            with self.assertRaisesRegex(ValueError, "must block Low and above"):
                safety.main()
        self.assertIn("[5/8]", self.output.getvalue())
        self.assertNotIn("Applied custom policy passed", self.output.getvalue())
        self.factory.assert_not_called()

    def test_failed_benign_response_does_not_reach_report_or_completion(self):
        self.client.chat.completions.create.return_value.choices[0].finish_reason = "length"
        with self.assertRaisesRegex(RuntimeError, "did not complete with text"):
            safety.main()
        self.assertIn("[7/8]", self.output.getvalue())
        self.assertNotIn("Model answer:", self.output.getvalue())
        self.assertNotIn("[8/8]", self.output.getvalue())
        self.assertFalse((self.folder / "results").exists())

    def test_failed_report_save_does_not_announce_completion(self):
        with patch.object(safety, "save_report", side_effect=OSError("Disk full")):
            with self.assertRaisesRegex(OSError, "Disk full"):
                safety.main()
        self.assertIn("[8/8]", self.output.getvalue())
        self.assertNotIn("[Complete]", self.output.getvalue())


class EvaluationTests(unittest.TestCase):
    def test_comparison_explains_each_request_before_sending_it(self):
        client = MagicMock()
        answer = response("puzzle-answer")
        follow_up = response("follow-up-answer")
        for item in (answer, follow_up):
            item.usage = MagicMock()
            item.usage.model_dump.return_value = {"total_tokens": 10}
        with redirect_stdout(io.StringIO()) as output:
            def create(**kwargs):
                if "previous_response_id" in kwargs:
                    self.assertIn("Sending follow-up: Explain your reasoning.", output.getvalue())
                    self.assertEqual(kwargs["previous_response_id"], answer.id)
                    return follow_up
                self.assertIn("Sending the river puzzle to deployment model", output.getvalue())
                self.assertIn("may incur inference charges", output.getvalue())
                self.assertEqual(kwargs["input"], evaluation.PUZZLE)
                return answer

            client.responses.create.side_effect = create
            results = evaluation.compare_models(client, ["model"])
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertEqual(results[0]["answer"], "answer")
        self.assertEqual(results[0]["follow_up"], "answer")
        self.assertIn("not controlled catalog benchmarks", output.getvalue())

    def test_quality_only_definition(self):
        definition = evaluation.evaluation_definition("judge")
        self.assertEqual({item["name"] for item in definition["testing_criteria"]},
                         {"coherence", "fluency", "relevance"})
        self.assertTrue(all(item["initialization_parameters"]["model"] == "judge"
                            for item in definition["testing_criteria"]))

    def test_full_guide_sample_size_and_system_only_template(self):
        source = evaluation.synthetic_source("model", 45, "dataset")
        self.assertEqual(source["item_generation_params"]["samples_count"], 45)
        self.assertEqual(source["target"]["model"], "model")
        self.assertEqual([item["role"] for item in source["input_messages"]["template"]], ["system"])

    def test_invalid_sample_count_and_flags(self):
        for arguments in (["--samples", "0"], ["--samples", "46"], ["--timeout", "0"],
                          ["--resume", "--compare-only"], ["--reset", "--resume"],
                          ["--reset", "--compare-only"]):
            with self.subTest(arguments=arguments), patch("sys.argv", ["eval.py", *arguments]), patch.object(
                evaluation, "load_config", return_value=(ROOT, "endpoint", "model")
            ), self.assertRaises(ValueError):
                evaluation.main()

    def item(self, results=None, status="pass"):
        data = {"status": status, "results": results if results is not None else
                [{"name": name, "score": 5.0} for name in ("coherence", "fluency", "relevance")]}
        return SimpleNamespace(model_dump=lambda: data)

    def test_exact_forty_five_scored_rows(self):
        evaluation.validate_evaluation_items([self.item() for _ in range(45)], 45)
        with self.assertRaises(RuntimeError):
            evaluation.validate_evaluation_items([self.item() for _ in range(44)], 45)

    def test_missing_duplicate_and_errored_metrics_fail(self):
        for item in (self.item([]), self.item(status="error"),
                     self.item([{"name": "coherence", "score": 5}] * 3)):
            with self.assertRaises(RuntimeError):
                evaluation.validate_evaluation_items([item], 1)

    def test_scores_must_be_real_numbers(self):
        for value in (None, float("nan"), float("inf"), True, "5"):
            results = self.item().model_dump()["results"]
            results[0]["score"] = value
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                evaluation.validate_evaluation_items([self.item(results)], 1)

    def test_default_automatically_resumes_before_billed_comparison(self):
        client = self.completed_client()
        with tempfile.TemporaryDirectory() as folder, patch.object(
            evaluation, "compare_models"
        ) as compare:
            output = self.resume(Path(folder), client, explicit=False)
        self.assertIn("automatically resuming", output)
        self.assertIn("Mode: automatic resume", output)
        self.assertIn("skipping comparison and new job submission", output)
        compare.assert_not_called()
        client.evals.create.assert_not_called()
        client.evals.runs.create.assert_not_called()

    def test_resume_rejects_another_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "results").mkdir()
            (root / "results/evaluation-state.json").write_text(json.dumps({
                "project": "https://example/api/projects/other", "deployment": "model"
            }))
            with patch("sys.argv", ["eval.py", "--resume"]), patch.object(
                evaluation, "load_config", return_value=(root, "endpoint", "model")
            ), patch.object(evaluation, "required", return_value="https://example/api/projects/current"), patch.object(
                evaluation, "model_client"
            ), self.assertRaises(ValueError):
                evaluation.main()

    def resume(self, root, client, *arguments, explicit=True):
        project = "https://example/api/projects/current"
        (root / "results").mkdir(exist_ok=True)
        (root / "results/evaluation-state.json").write_text(json.dumps({
            "project": project, "deployment": "model", "eval_id": "evaluation",
            "run_id": "run", "samples": 45, "success": False,
        }))
        with patch("sys.argv", ["eval.py", *(["--resume"] if explicit else []), *arguments]), patch.object(
            evaluation, "load_config", return_value=(root, "endpoint", "model")
        ), patch.object(evaluation, "required", side_effect=lambda name:
                         project if name == "PROJECT_ENDPOINT" else "comparison-model"), patch.object(
            evaluation, "model_client"
        ) as factory, redirect_stdout(io.StringIO()) as output:
            factory.return_value.__enter__.return_value = client
            evaluation.main()
        return output.getvalue()

    def completed_client(self, samples=45):
        client = MagicMock()
        raw = client.evals.runs.with_raw_response.retrieve.return_value
        raw.parse.return_value.status = "completed"
        raw.parse.return_value.model_dump.side_effect = AssertionError(
            "Azure preview run reports must preserve the original JSON, not serialize the SDK model."
        )
        raw.http_response.json.return_value = {
            "status": "completed",
            "data_source": {"type": "azure_ai_synthetic_data_gen_preview", "azure_extra": True},
        }
        client.evals.runs.output_items.list.return_value = [self.item() for _ in range(samples)]
        return client

    def test_completed_resume_reuses_run_and_validates_all_rows(self):
        client = self.completed_client()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = self.resume(root, client)
            state = json.loads((root / "results/evaluation-state.json").read_text())
            self.assertTrue(state["success"])
            report = json.loads((root / "results/cloud-evaluation.json").read_text())
            self.assertEqual(report["data_source"]["type"], "azure_ai_synthetic_data_gen_preview")
            self.assertTrue(report["data_source"]["azure_extra"])
        self.assertIn("Mode: --resume", output)
        self.assertIn("Using the saved run's sample count", output)
        self.assertLess(output.index("[Polling]"), output.index("[Results]"))
        self.assertLess(output.index("[Validation]"), output.index("Completed cloud evaluation"))
        client.evals.runs.create.assert_not_called()
        client.evals.create.assert_not_called()
        client.evals.runs.with_raw_response.retrieve.assert_called_once_with("run", eval_id="evaluation")

    def test_timeout_preserves_resumable_state_and_respects_poll_interval(self):
        client = self.completed_client()
        raw = client.evals.runs.with_raw_response.retrieve.return_value
        raw.parse.return_value.status = "in_progress"
        raw.http_response.json.return_value["status"] = "in_progress"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(evaluation.time, "monotonic", side_effect=[0, 0.75, 1.1]), patch.object(
                evaluation.time, "sleep"
            ) as sleep, self.assertRaises(TimeoutError):
                self.resume(root, client, "--timeout", "1")
            sleep.assert_called_once_with(0.25)
            state = json.loads((root / "results/evaluation-state.json").read_text())
            self.assertFalse(state["success"])
            self.assertEqual(state["run_id"], "run")
            self.assertEqual(state["status"], "in_progress")
            self.assertTrue((root / "results/cloud-evaluation.json").is_file())
        client.evals.runs.create.assert_not_called()

    def test_reset_archives_previous_reports_and_submits_one_fresh_run(self):
        client = self.completed_client(samples=1)
        client.evals.create.return_value = SimpleNamespace(id="fresh-evaluation")
        client.evals.runs.create.return_value = SimpleNamespace(id="fresh-run", status="completed")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "results").mkdir()
            (root / "results/cloud-evaluation.json").write_text('{"old": true}')
            (root / "results/notes.txt").write_text("keep unrelated file")
            with patch.object(evaluation, "compare_models", return_value=[]) as compare:
                output = self.resume(root, client, "--reset", "--samples", "1", explicit=False)
            compare.assert_called_once()
            state = json.loads((root / "results/evaluation-state.json").read_text())
            self.assertEqual(state["run_id"], "fresh-run")
            self.assertEqual(state["samples"], 1)
            self.assertTrue(state["success"])
            archive, = (root / "results/archive").iterdir()
            self.assertEqual(json.loads((archive / "evaluation-state.json").read_text())["run_id"], "run")
            self.assertEqual((archive / "cloud-evaluation.json").read_text(), '{"old": true}')
            self.assertEqual((root / "results/notes.txt").read_text(), "keep unrelated file")
            self.assertIn("billable", output)
            self.assertIn("Mode: --reset", output)
            self.assertIn("[Archive]", output)
            self.assertIn("not deleted or canceled", output)
            self.assertLess(output.index("[Archive]"), output.index("Submitting a new billable cloud run"))
        client.evals.create.assert_called_once()
        client.evals.runs.create.assert_called_once()
        self.assertEqual(client.evals.runs.create.call_args.kwargs["data_source"]
                         ["item_generation_params"]["samples_count"], 1)
        client.evals.runs.with_raw_response.retrieve.assert_called_once_with(
            "fresh-run", eval_id="fresh-evaluation"
        )
        client.evals.delete.assert_not_called()
        client.evals.runs.cancel.assert_not_called()

    def test_compare_only_leaves_saved_cloud_run_untouched(self):
        client = MagicMock()
        with tempfile.TemporaryDirectory() as folder, patch.object(
            evaluation, "compare_models", return_value=[]
        ) as compare:
            root = Path(folder)
            output = self.resume(root, client, "--compare-only", explicit=False)
            state = json.loads((root / "results/evaluation-state.json").read_text())
            self.assertEqual(state["run_id"], "run")
            self.assertFalse((root / "results/archive").exists())
        self.assertIn("Mode: --compare-only", output)
        self.assertIn("Comparison-only completed successfully.", output)
        self.assertNotIn("[Cloud evaluation]", output)
        compare.assert_called_once()
        client.evals.create.assert_not_called()
        client.evals.runs.with_raw_response.retrieve.assert_not_called()

    def test_failed_run_preserves_raw_error_and_does_not_report_success(self):
        client = self.completed_client()
        raw = client.evals.runs.with_raw_response.retrieve.return_value
        raw.parse.return_value.status = "failed"
        raw.http_response.json.return_value.update({
            "status": "failed", "error": {"message": "service-reported failure"},
        })
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(RuntimeError, "service-reported failure"):
                self.resume(root, client)
            state = json.loads((root / "results/evaluation-state.json").read_text())
            self.assertFalse(state["success"])
            self.assertEqual(state["status"], "failed")
            report = json.loads((root / "results/cloud-evaluation.json").read_text())
            self.assertEqual(report["error"]["message"], "service-reported failure")
        client.evals.runs.output_items.list.assert_not_called()

    def test_archive_preserves_all_known_reports_and_rejects_directories(self):
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            root = Path(folder)
            (root / "results").mkdir()
            names = ("model-comparison.json", "cloud-evaluation.json", "evaluation-items.json",
                     "evaluation-progress.json", "evaluation-state.json")
            for name in names:
                (root / "results" / name).write_text(name)
            archive = evaluation.archive_reports(root)
            for name in names:
                self.assertEqual((archive / name).read_text(), name)
                self.assertFalse((root / "results" / name).exists())
            self.assertIsNone(evaluation.archive_reports(root))
            (root / "results/evaluation-state.json").mkdir()
            with self.assertRaises(ValueError):
                evaluation.archive_reports(root)

    def test_reset_validates_configuration_before_archiving(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("sys.argv", ["eval.py", "--reset"]), patch.object(
                evaluation, "load_config", return_value=(root, "endpoint", "model")
            ), patch.object(evaluation, "required", return_value="http://example/api/projects/project"), patch.object(
                evaluation, "archive_reports"
            ) as archive, self.assertRaises(ValueError):
                evaluation.main()
            archive.assert_not_called()

    def test_explicit_resume_requires_saved_state(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "sys.argv", ["eval.py", "--resume"]
        ), patch.object(evaluation, "load_config", return_value=(Path(folder), "endpoint", "model")), patch.object(
            evaluation, "model_client"
        ) as client, self.assertRaises(ValueError):
            evaluation.main()
        client.assert_not_called()


class ProvenanceTests(unittest.TestCase):
    def test_plan_and_prepare_screenshots_are_available_locally(self):
        guide = ROOT / "01-plan-and-prepare" / "upstream-guide.md"
        images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", guide.read_text(encoding="utf-8"))
        self.assertTrue(images, "The guide must reference its screenshots")
        for image in images:
            with self.subTest(image=image):
                path = guide.parent / image
                self.assertTrue(path.is_file(), f"Missing screenshot: {path}")
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_all_downloaded_source_hashes(self):
        manifest = json.loads((ROOT / "SOURCE-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 18)
        for item in manifest["files"]:
            with self.subTest(path=item["local"]):
                self.assertEqual(hashlib.sha256((ROOT / item["local"]).read_bytes()).hexdigest(),
                                 item["sha256"])


if __name__ == "__main__":
    unittest.main()
