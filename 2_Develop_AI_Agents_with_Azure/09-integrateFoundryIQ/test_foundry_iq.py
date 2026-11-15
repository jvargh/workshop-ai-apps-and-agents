from contextlib import redirect_stdout
import io
import os
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import agent_client


def response(output=(), text="Product answer", status="completed"):
    return SimpleNamespace(output=list(output), output_text=text, status=status, error="Service error")


def approval(identifier):
    return SimpleNamespace(
        type="mcp_approval_request", id=identifier, name="knowledge_base_retrieve",
        server_label="kb-sample", arguments='{"query":"Contoso products"}',
    )


class FoundryIQTests(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.history = []

    def send(self, reply):
        self.api.responses.create.return_value = reply
        return agent_client.send_message_to_agent("Product question", self.api, "product-agent", "conversation", self.history)

    def test_approval_rounds_return_matching_decisions_and_keep_full_history(self):
        tool = SimpleNamespace(type="mcp_call", name="knowledge_base_retrieve", server_label="kb-sample",
                               error=None, status="completed")
        self.api.responses.create.side_effect = [
            response([approval("first")]), response([approval("second")]), response([tool]),
        ]
        with patch("builtins.input", side_effect=["yes", "y"]), redirect_stdout(io.StringIO()) as output:
            agent_client.send_message_to_agent("Product question", self.api, "product-agent", "conversation", self.history)
        items = self.api.conversations.items.create.call_args_list
        self.assertEqual([call.kwargs["items"][0]["approval_request_id"] for call in items[1:]], ["first", "second"])
        self.assertTrue(all(call.kwargs["items"][0]["approve"] for call in items[1:]))
        self.assertTrue(all(call.kwargs["conversation_id"] == "conversation" for call in items))
        self.assertEqual([turn["role"] for turn in self.history], ["user", "assistant"])
        self.assertIn("[Knowledge] Completed MCP call", output.getvalue())

    def test_invalid_approval_input_is_reprompted_and_no_denies(self):
        self.api.responses.create.side_effect = [response([approval("decision")]), response(text="Lookup denied")]
        with patch("builtins.input", side_effect=["maybe", "no"]), redirect_stdout(io.StringIO()) as output:
            agent_client.send_message_to_agent("Question", self.api, "agent", "conversation", self.history)
        self.assertFalse(self.api.conversations.items.create.call_args.kwargs["items"][0]["approve"])
        self.assertIn("No approval decision has been sent", output.getvalue())

    def test_no_approval_response_does_not_ask_for_a_decision(self):
        with patch("builtins.input") as prompt, redirect_stdout(io.StringIO()):
            self.assertEqual(self.send(response()), "Product answer")
        prompt.assert_not_called()
        self.assertEqual(self.api.responses.create.call_count, 1)

    def test_failed_incomplete_and_empty_answers_do_not_enter_assistant_history(self):
        for reply in (response(status="failed"), response(status="incomplete"), response(text=" ")):
            with self.subTest(status=reply.status), redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                self.send(reply)
        self.assertTrue(all(turn["role"] == "user" for turn in self.history))

    def test_failed_knowledge_call_is_not_reported_as_success(self):
        tool = SimpleNamespace(type="mcp_call", name="retrieve", error="Access denied", status="failed")
        with redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, "Access denied"):
                self.send(response([tool]))
        self.assertNotIn("Agent:\nProduct answer", output.getvalue())

    def test_invalid_arguments_and_approval_eof_are_explicit_failures(self):
        request = approval("invalid")
        request.arguments = "{invalid"
        with patch("builtins.input") as prompt, redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            self.send(response([request]))
        prompt.assert_not_called()
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(io.StringIO()), self.assertRaisesRegex(
            RuntimeError, "before an approval decision"
        ):
            self.send(response([approval("eof")]))

    def test_sources_and_history_display_actual_response_data(self):
        content = SimpleNamespace(type="output_text", annotations=[
            SimpleNamespace(type="url_citation", title="Catalog", url="https://example.com/catalog"),
            SimpleNamespace(type="file_citation", filename="tents.pdf", file_id="file"),
        ])
        with redirect_stdout(io.StringIO()) as output:
            self.send(response([SimpleNamespace(type="message", content=[content])]))
            agent_client.display_conversation_history(self.history)
        text = output.getvalue()
        self.assertIn("[Source] Catalog: https://example.com/catalog", text)
        self.assertIn("[Source] tents.pdf", text)
        self.assertIn("USER: Product question", text)
        self.assertIn("ASSISTANT: Product answer", text)

    def test_sources_are_unique_across_messages_without_hiding_different_files(self):
        repeated_url = SimpleNamespace(type="url_citation", title="https://example.com/catalog", url="https://example.com/catalog")
        repeated_file = SimpleNamespace(type="file_citation", filename="tents.pdf", file_id="first-file")
        first = SimpleNamespace(type="output_text", annotations=[repeated_url, repeated_file, repeated_url])
        second = SimpleNamespace(type="output_text", annotations=[
            repeated_url, repeated_file,
            SimpleNamespace(type="url_citation", title="Other catalog", url="https://example.com/other"),
            SimpleNamespace(type="file_citation", filename="tents.pdf", file_id="second-file"),
        ])
        with redirect_stdout(io.StringIO()) as output:
            agent_client.show_sources(response([
                SimpleNamespace(type="message", content=[first]),
                SimpleNamespace(type="message", content=[second]),
            ]))
        text = output.getvalue()
        self.assertEqual(text.count("[Source]"), 4)
        self.assertEqual(text.count("https://example.com/catalog"), 1)
        self.assertEqual(text.count("file ID: first-file"), 1)
        self.assertEqual(text.count("file ID: second-file"), 1)
        self.assertIn("Other catalog: https://example.com/other", text)

    def test_source_deduplication_resets_each_turn_and_keeps_inline_references(self):
        annotation = SimpleNamespace(type="url_citation", title="Catalog", url="https://example.com/catalog")
        content = SimpleNamespace(type="output_text", annotations=[annotation, annotation])
        reply = response([SimpleNamespace(type="message", content=[content])], text="Claim A [1]. Claim B [1].")
        with redirect_stdout(io.StringIO()) as output:
            self.send(reply)
            self.send(reply)
        self.assertEqual(output.getvalue().count("[Source] Catalog:"), 2)
        self.assertEqual(output.getvalue().count("Claim A [1]. Claim B [1]."), 2)
        self.assertEqual(reply.output_text, "Claim A [1]. Claim B [1].")

    def test_history_and_quit_do_not_call_model_or_delete_existing_agent(self):
        project = MagicMock()
        project.__enter__.return_value = project
        api = project.get_openai_client.return_value
        api.__enter__.return_value = api
        project.agents.get.return_value = SimpleNamespace(
            name="product-agent", as_dict=lambda: {"versions": {"latest": {"definition": {"tools": [
                {"type": "mcp", "server_label": "kb-sample", "require_approval": "never"},
            ]}}}}
        )
        with patch.dict(os.environ, {"PROJECT_ENDPOINT": "endpoint", "AGENT_NAME": "product-agent"}), patch.object(
            agent_client, "load_dotenv"
        ), patch.object(agent_client, "DefaultAzureCredential"), patch.object(
            agent_client, "AIProjectClient", return_value=project
        ), patch("builtins.input", side_effect=["", "history", "quit"]), redirect_stdout(io.StringIO()) as output:
            agent_client.main()
        api.responses.create.assert_not_called()
        project.agents.delete.assert_not_called()
        self.assertIn("No model request was sent", output.getvalue())
        self.assertIn("No questions have been submitted", output.getvalue())
        self.assertIn("runs without manual approval prompts", output.getvalue())
        self.assertIn("[Complete]", output.getvalue())


if __name__ == "__main__":
    unittest.main()
