import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dotenv import dotenv_values

from setup_search import SearchSetup


class SearchSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        with patch.dict(os.environ, {}, clear=True), patch("setup_search.load_dotenv"):
            self.setup = SearchSetup()
        self.setup.project_dir = Path(self.temporary.name)
        self.setup.env_file = self.setup.project_dir / ".env"
        self.setup.docs_dir = self.setup.project_dir / "sample_documents"
        self.setup.docs_dir.mkdir()
        self.setup.search_endpoint = "https://example.search.windows.net"
        self.setup.search_service_name = "example"
        self.setup.project_endpoint = "https://foundry.services.ai.azure.com/api/projects/lab"
        self.setup.resource_group = "search-rg"
        self.setup.location = "westus3"
        self.setup.subscription_id = "subscription"
        self.setup.connection_id = None
        self.setup.search_credential = MagicMock(return_value=MagicMock())

    def write_document(self, name="remote_work_policy.txt", content="Remote Work\n25 Mbps"):
        (self.setup.docs_dir / name).write_text(content, encoding="utf-8")

    def test_dotenv_project_uses_existing_search_connection_without_azd(self):
        connection = SimpleNamespace(
            type="CognitiveSearch", name="search-connection",
            target=self.setup.search_endpoint + "/",
            id="/subscriptions/subscription/resourceGroups/foundry-rg/providers/"
               "Microsoft.CognitiveServices/accounts/foundry/projects/lab/connections/search",
        )
        with patch("setup_search.AIProjectClient") as project, patch("setup_search.DefaultAzureCredential"), \
                patch("setup_search.subprocess.run") as command:
            project.return_value.__enter__.return_value.connections.list.return_value = [connection]
            self.assertTrue(self.setup.get_deployment_info())
        command.assert_not_called()
        self.assertEqual(self.setup.connection_id, connection.id)
        self.assertEqual(self.setup.search_endpoint, connection.target.rstrip("/"))

    def test_multiple_connections_require_explicit_selection(self):
        self.setup.search_endpoint = ""
        connection = SimpleNamespace(type="CognitiveSearch")
        with patch("setup_search.AIProjectClient") as project, patch("setup_search.DefaultAzureCredential"):
            project.return_value.__enter__.return_value.connections.list.return_value = [connection, connection]
            with self.assertRaisesRegex(ValueError, "Exactly one"):
                self.setup.get_deployment_info()

    def test_existing_service_is_only_read_not_reprovisioned(self):
        self.setup.run_az = MagicMock(return_value={"location": "westus3", "sku": {"name": "serverless"}})
        self.assertTrue(self.setup.create_search_service())
        self.assertEqual(self.setup.run_az.call_args.args[:3], ("search", "service", "show"))

    def test_partial_upload_is_not_reported_as_success(self):
        self.write_document()
        with patch("setup_search.SearchClient") as client:
            client.return_value.__enter__.return_value.upload_documents.return_value = [
                SimpleNamespace(succeeded=False, key="doc", error_message="Upload rejected"),
            ]
            with self.assertRaisesRegex(RuntimeError, "Upload rejected"):
                self.setup.upload_documents()

    def test_upload_preserves_complete_document_content(self):
        content = "Remote Work\n" + "Policy " * 8000
        self.write_document(content=content)
        with patch("setup_search.SearchClient") as client:
            upload = client.return_value.__enter__.return_value.upload_documents
            upload.return_value = [SimpleNamespace(succeeded=True)]
            self.assertTrue(self.setup.upload_documents())
        self.assertEqual(upload.call_args.kwargs["documents"][0]["content"], content)
        self.assertEqual(len(self.setup.document_ids), 1)

    def test_empty_document_fails_instead_of_silently_skipping(self):
        self.write_document(content="")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.setup.upload_documents()

    def test_empty_search_results_fail_setup(self):
        self.setup.document_ids = {"doc"}
        with patch("setup_search.SearchClient") as client, patch("setup_search.time.sleep"):
            client.return_value.__enter__.return_value.search.return_value = []
            with self.assertRaisesRegex(RuntimeError, "did not become searchable"):
                self.setup.test_search()

    def test_query_validation_requires_expected_source_and_fact(self):
        self.setup.document_ids = {"doc"}
        with patch("setup_search.SearchClient") as client:
            client.return_value.__enter__.return_value.search.side_effect = [
                [{"id": "doc"}],
                [{"source_file": "remote_work_policy.txt", "content": "Incorrect policy"}],
            ]
            with self.assertRaisesRegex(RuntimeError, "Search validation failed"):
                self.setup.test_search()

    def test_search_checks_all_three_policy_sources(self):
        self.setup.document_ids = {"doc"}
        with patch("setup_search.SearchClient") as client:
            client.return_value.__enter__.return_value.search.side_effect = [
                [{"id": "doc"}],
                [{"source_file": "remote_work_policy.txt", "content": "25 Mbps"}],
                [{"source_file": "expense_report_guide.md", "content": "concur.contoso.com"}],
                [{"source_file": "it_security_policy.txt", "content": "BitLocker"}],
            ]
            self.assertTrue(self.setup.test_search())

    def test_save_updates_stale_configuration_and_preserves_other_values(self):
        self.setup.env_file.write_text(
            "MODEL_DEPLOYMENT_NAME=test-model\nSEARCH_ENDPOINT=https://old.search.windows.net\n",
            encoding="utf-8",
        )
        self.setup.connection_id = "connection"
        self.assertTrue(self.setup.save_configuration())
        values = dotenv_values(self.setup.env_file)
        self.assertEqual(values["MODEL_DEPLOYMENT_NAME"], "test-model")
        self.assertEqual(values["SEARCH_ENDPOINT"], self.setup.search_endpoint)
        self.assertEqual(values["SEARCH_PROJECT_CONNECTION_ID"], "connection")
        self.assertNotIn("SEARCH_KEY", values)

    def test_failed_search_stops_before_configuration_and_success_message(self):
        names = (
            "get_deployment_info", "create_search_service",
            "create_search_index", "upload_documents", "test_search",
            "save_configuration", "show_next_steps",
        )
        for name in names:
            setattr(self.setup, name, MagicMock(return_value=True))
        self.setup.test_search.return_value = False
        with redirect_stdout(io.StringIO()):
            self.assertFalse(self.setup.run())
        self.setup.save_configuration.assert_not_called()
        self.setup.show_next_steps.assert_not_called()


if __name__ == "__main__":
    unittest.main()
