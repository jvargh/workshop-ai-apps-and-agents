import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


foundry_stub = ModuleType("agent_framework.foundry")
foundry_stub.FoundryChatClient = MagicMock()
spec = importlib.util.spec_from_file_location(
    "expense_agent", Path(__file__).with_name("agent-framework.py")
)
expense_agent = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"agent_framework.foundry": foundry_stub}), \
        patch("dotenv.load_dotenv"):
    spec.loader.exec_module(expense_agent)


class ClaimPrivacyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "EXPENSE_CLAIM_EMAIL": "recipient@example.com",
            "PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/lab",
            "MODEL_DEPLOYMENT_NAME": "test-model",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def mock_client(self):
        client = MagicMock()
        client.client.close = AsyncMock()
        client.project_client.close = AsyncMock()
        return client

    async def test_recipient_comes_from_local_configuration(self):
        manager = MagicMock()
        agent = AsyncMock()
        manager.__aenter__.return_value = agent
        agent.run.return_value = "Draft ready"
        client = self.mock_client()
        with patch.object(
            expense_agent, "Agent", return_value=manager
        ) as constructor, patch.object(
            expense_agent, "FoundryChatClient", return_value=client
        ), patch.object(
            expense_agent, "AzureCliCredential"
        ) as credential, contextlib.redirect_stdout(io.StringIO()):
            await expense_agent.process_expenses_data("Draft a claim", "Example expense")
        instructions = constructor.call_args.kwargs["instructions"]
        self.assertIn("recipient@example.com", instructions)
        self.assertIn("never sends email", instructions)
        self.assertIn("Do not claim that anything was sent", instructions)
        agent.run.assert_awaited_once()
        self.assertEqual(agent.run.call_args.kwargs["options"], {"store": False})
        client.client.close.assert_awaited_once()
        client.project_client.close.assert_awaited_once()
        credential.return_value.close.assert_called_once()

    async def test_missing_recipient_fails_before_client_creation(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            expense_agent, "FoundryChatClient"
        ) as client:
            with self.assertRaisesRegex(ValueError, "EXPENSE_CLAIM_EMAIL"):
                await expense_agent.process_expenses_data("Draft a claim", "Example expense")
        client.assert_not_called()

    async def test_missing_project_or_model_fails_before_client_creation(self):
        for key in ("PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME"):
            with self.subTest(key=key), patch.dict(os.environ, {key: ""}), patch.object(
                expense_agent, "FoundryChatClient"
            ) as client, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, key):
                    await expense_agent.process_expenses_data("Draft a claim", "Example expense")
                client.assert_not_called()

    async def test_model_failure_is_propagated_and_clients_close(self):
        manager = MagicMock()
        agent = AsyncMock()
        manager.__aenter__.return_value = agent
        agent.run.side_effect = RuntimeError("Synthetic model failure")
        client = self.mock_client()
        output = io.StringIO()
        with patch.object(expense_agent, "Agent", return_value=manager), patch.object(
            expense_agent, "FoundryChatClient", return_value=client
        ), patch.object(expense_agent, "AzureCliCredential") as credential, \
                contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "Synthetic model failure"):
                await expense_agent.process_expenses_data("Draft a claim", "Example expense")
        client.client.close.assert_awaited_once()
        client.project_client.close.assert_awaited_once()
        credential.return_value.close.assert_called_once()
        self.assertNotIn("Finished.", output.getvalue())

    async def test_empty_response_is_failure(self):
        manager = MagicMock()
        agent = AsyncMock()
        manager.__aenter__.return_value = agent
        agent.run.return_value = ""
        with patch.object(expense_agent, "Agent", return_value=manager), patch.object(
            expense_agent, "FoundryChatClient", return_value=self.mock_client()
        ), patch.object(expense_agent, "AzureCliCredential"), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "no final text"):
                await expense_agent.process_expenses_data("Draft a claim", "Example expense")

    async def test_client_creation_failure_closes_credential(self):
        with patch.object(
            expense_agent, "FoundryChatClient", side_effect=RuntimeError("Client setup failed")
        ), patch.object(expense_agent, "AzureCliCredential") as credential, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "Client setup failed"):
                await expense_agent.process_expenses_data("Draft a claim", "Example expense")
        credential.return_value.close.assert_called_once()

    async def test_blank_exit_and_eof_stop_before_inference(self):
        for value in ("", "exit", "EXIT", EOFError()):
            with self.subTest(value=value), patch(
                "builtins.input", side_effect=value if isinstance(value, Exception) else None,
                return_value=value if isinstance(value, str) else None,
            ), patch.object(expense_agent, "process_expenses_data", new_callable=AsyncMock) as process, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                await expense_agent.main()
                process.assert_not_awaited()
                self.assertIn("Stopped before model inference", output.getvalue())

    async def test_tool_returns_the_same_printed_draft_without_writing_files(self):
        arguments = {
            "to": "recipient@example.com",
            "subject": "Expense Claim",
            "body": "Synthetic taxi 24.00; dinner 65.50; hotel 125.90; total 215.40.",
        }
        with contextlib.redirect_stdout(io.StringIO()) as output, patch(
            "builtins.open", side_effect=AssertionError("No file writes are allowed")
        ), patch.object(Path, "open", side_effect=AssertionError("No file writes are allowed")):
            result = await expense_agent.submit_claim.invoke(arguments=arguments)
        self.assertEqual(len(result), 1)
        self.assertEqual(json.loads(result[0].text), {"status": "draft_only", **arguments})
        for value in arguments.values():
            self.assertIn(value, output.getvalue())
        self.assertIn("PRINTED DRAFT ONLY", output.getvalue())

    async def test_tool_rejects_a_recipient_not_in_configuration(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(ValueError, "must match EXPENSE_CLAIM_EMAIL"):
                await expense_agent.submit_claim.invoke(arguments={
                    "to": "different@example.com", "subject": "Expense Claim", "body": "Synthetic",
                })
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
