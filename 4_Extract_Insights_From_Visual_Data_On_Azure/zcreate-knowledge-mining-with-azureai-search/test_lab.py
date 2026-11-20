import contextlib
import importlib.util
import io
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from azure.core.exceptions import HttpResponseError

import lab_config


def load_script(name):
    path = Path(__file__).with_name(f"{name.replace('_', '-')}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


app = load_script("search_app")
setup = load_script("setup_search")


class ConfigurationTests(unittest.TestCase):
    def test_config_uses_script_relative_env(self):
        with patch.object(lab_config, "load_dotenv") as load, patch.dict(
            os.environ,
            {"SEARCH_ENDPOINT": "https://example.search.windows.net/",
             "INDEX_NAME": "margies-index"},
            clear=True,
        ):
            self.assertEqual(
                lab_config.load_search_config(),
                ("https://example.search.windows.net", "margies-index"),
            )
            load.assert_called_once_with(lab_config.LAB_DIR / ".env")

    def test_missing_and_placeholder_values_are_errors(self):
        for value in ("", "your_search_endpoint", "   "):
            with self.subTest(value=value), patch.dict(
                os.environ, {"SEARCH_ENDPOINT": value}, clear=True
            ), self.assertRaises(ValueError):
                lab_config.required_setting("SEARCH_ENDPOINT")

    def test_invalid_endpoint_is_rejected(self):
        for endpoint in (
            "http://example.search.windows.net",
            "https://example.search.windows.net/indexes/a",
            "https://example.search.windows.net?api-key=secret",
            "https://user:password@example.search.windows.net",
        ):
            with self.subTest(endpoint=endpoint), patch.object(
                lab_config, "load_dotenv"
            ), patch.dict(os.environ, {
                "SEARCH_ENDPOINT": endpoint, "INDEX_NAME": "margies-index"
            }), self.assertRaises(ValueError):
                lab_config.load_search_config()


class ClientTests(unittest.TestCase):
    def run_app(self, inputs, client=None):
        if client is None:
            client = MagicMock()
        credential = MagicMock()
        output, error = io.StringIO(), io.StringIO()
        with patch.object(app, "load_search_config", return_value=(
            "https://example.search.windows.net", "margies-index"
        )), patch.object(
            app, "DefaultAzureCredential"
        ) as credentials, patch.object(
            app, "SearchClient"
        ) as clients, patch(
            "builtins.input", side_effect=inputs
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            credentials.return_value.__enter__.return_value = credential
            clients.return_value.__enter__.return_value = client
            result = app.main()
            clients.assert_called_once_with(
                "https://example.search.windows.net", "margies-index", credential
            )
            credentials.return_value.__exit__.assert_called_once()
            clients.return_value.__exit__.assert_called_once()
        return result, output.getvalue(), error.getvalue(), client

    def test_guide_query_fields_order_and_output(self):
        client = MagicMock()
        hits = MagicMock()
        hits.get_count.return_value = 1
        hits.__iter__.return_value = iter([{
            "title": "London Brochure.pdf", "locations": ["London"],
            "persons": ["Example Person"], "keyPhrases": ["flights"],
        }])
        client.search.return_value = hits
        code, output, error, _ = self.run_app([" London ", " QuIt "], client)
        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        for value in ("Search returned 1 documents:", "London Brochure.pdf",
                      "London", "Example Person", "flights"):
            self.assertIn(value, output)
        client.search.assert_called_once_with(
            search_text="London",
            select=["title", "locations", "persons", "keyPhrases"],
            order_by=["title"], include_total_count=True,
        )

    def test_blank_input_does_not_query(self):
        code, output, _, client = self.run_app(["  ", "quit"])
        self.assertEqual(code, 0)
        self.assertIn("Please enter a query.", output)
        client.search.assert_not_called()

    def test_eof_exits_cleanly(self):
        code, _, _, client = self.run_app([EOFError()])
        self.assertEqual(code, 0)
        client.search.assert_not_called()

    def test_azure_failure_has_nonzero_exit(self):
        client = MagicMock()
        client.search.side_effect = HttpResponseError(message="Forbidden")
        code, _, error, _ = self.run_app(["London"], client)
        self.assertEqual(code, 1)
        self.assertIn("Search failed:", error)
        self.assertIn("Forbidden", error)

    def test_config_failure_has_nonzero_exit(self):
        error = io.StringIO()
        with patch.object(
            app, "load_search_config", side_effect=ValueError("Missing config")
        ), contextlib.redirect_stderr(error):
            self.assertEqual(app.main(), 1)
        self.assertIn("Missing config", error.getvalue())


class PipelineTests(unittest.TestCase):
    def test_archive_contains_exactly_six_original_pdfs(self):
        with ZipFile(setup.LAB_DIR / "documents.zip") as archive:
            members = [item for item in archive.infolist()
                       if item.filename.lower().endswith(".pdf")]
            self.assertEqual(len(members), 6)
            self.assertEqual(
                {Path(item.filename).name: item.file_size for item in members},
                setup.EXPECTED_DOCUMENTS,
            )
            for item in members:
                self.assertTrue(archive.read(item).startswith(b"%PDF-"))

    def test_field_attributes_match_guide(self):
        index = setup.index_definition("margies-index")
        fields = {item["name"]: item for item in index["fields"]}
        for name in ("metadata_storage_size", "metadata_storage_last_modified",
                     "title", "locations", "persons", "keyPhrases"):
            with self.subTest(field=name):
                self.assertTrue(fields[name]["retrievable"])
                self.assertTrue(fields[name]["filterable"])
                self.assertEqual(fields[name]["sortable"], name in (
                    "metadata_storage_size", "metadata_storage_last_modified", "title"
                ))
                self.assertEqual(fields[name]["searchable"], name not in (
                    "metadata_storage_size", "metadata_storage_last_modified"
                ))
        self.assertEqual(
            index["semantic"]["defaultConfiguration"], "margies-semantic"
        )

    def test_free_enrichment_and_required_skills(self):
        definition = setup.skillset_definition("margies-index")
        self.assertNotIn("cognitiveServices", definition)
        skills = {item["name"]: item for item in definition["skills"]}
        self.assertEqual(set(skills), {"ocr", "merge", "phrases", "entities", "images"})
        self.assertEqual(skills["entities"]["categories"], ["Person", "Location"])
        self.assertEqual(skills["images"]["visualFeatures"], ["tags", "categories"])
        self.assertEqual(
            skills["merge"]["outputs"],
            [{"name": "mergedText", "targetName": "merged_content"}],
        )
        for name in ("entities", "phrases"):
            self.assertEqual(
                skills[name]["inputs"],
                [{"name": "text", "source": "/document/merged_content"}],
            )

    def test_indexer_once_with_complete_enrichment_mappings(self):
        definition = setup.indexer_definition("margies-index")
        self.assertNotIn("schedule", definition)
        self.assertEqual(definition["parameters"]["maxFailedItems"], 0)
        self.assertEqual(
            definition["parameters"]["configuration"]["imageAction"],
            "generateNormalizedImages",
        )
        self.assertEqual(
            {item["targetFieldName"] for item in definition["outputFieldMappings"]},
            {"merged_content", "locations", "persons", "keyPhrases",
             "imageTags", "imageCategories"},
        )

    def test_datasource_uses_identity_not_storage_key(self):
        body = setup.datasource_definition("margies-index", "/storage/resource", "documents")
        self.assertEqual(body["credentials"]["connectionString"],
                         "ResourceId=/storage/resource;")
        self.assertEqual(body["container"]["name"], "documents")

    def test_storage_id_validation(self):
        with patch.dict(os.environ, {
            "STORAGE_RESOURCE_ID": "https://invalid.blob.core.windows.net",
            "BLOB_CONTAINER": "documents",
        }), self.assertRaises(ValueError):
            setup.storage_settings()

    def test_wait_does_not_accept_old_success(self):
        rest = MagicMock()
        rest.call.side_effect = [
            {"lastResult": {"status": "success", "startTime": "old"}},
            {"lastResult": {"status": "inProgress", "startTime": "new"}},
            {"lastResult": {"status": "success", "startTime": "new"}},
        ]
        with patch.object(setup.time, "sleep"):
            status = setup.wait_for_indexer(rest, "margies-index", 60, "old")
        self.assertEqual(status["lastResult"]["startTime"], "new")
        self.assertEqual(rest.call.call_count, 3)

    def test_wait_timeout_is_failure(self):
        with patch.object(setup.time, "monotonic", side_effect=[0, 61]):
            with self.assertRaises(TimeoutError):
                setup.wait_for_indexer(MagicMock(), "margies-index", 60)

    def test_http_errors_surface_without_returning_success(self):
        session = MagicMock()
        response = session.request.return_value
        response.ok = False
        response.status_code = 403
        response.text = "Forbidden"
        rest = setup.SearchRest("https://example.search.windows.net", MagicMock(), session)
        with self.assertRaisesRegex(RuntimeError, "HTTP 403: Forbidden"):
            rest.call("PUT", "indexes/margies-index", {})
        self.assertEqual(session.request.call_args.kwargs["timeout"], 90)

    def test_zero_documents_cannot_pass_validation(self):
        client = MagicMock()
        client.search.return_value.__iter__.return_value = iter([])
        client.search.return_value.get_count.return_value = 0
        with patch.object(setup, "SearchClient") as clients:
            clients.return_value.__enter__.return_value = client
            with self.assertRaisesRegex(ValueError, "Expected six indexed PDFs"):
                setup.validate_search("https://example.search.windows.net",
                                      "margies-index", MagicMock())

    def test_six_document_validation_queries_filter_and_reranker(self):
        documents = [{
            "title": title, "metadata_storage_size": size,
            "metadata_storage_last_modified": "2026-10-30T00:00:00Z",
            "merged_content": "Travel information",
            "locations": ["London"], "persons": ["Example Person"],
            "keyPhrases": ["flights"], "imageTags": ["building"],
            "imageCategories": ["outdoor"],
        } for title, size in setup.EXPECTED_DOCUMENTS.items()]

        def result(hits):
            page = MagicMock()
            page.__iter__.return_value = iter(hits)
            page.get_count.return_value = len(hits)
            return page

        info = next(d for d in documents if d["title"] == "Margies Travel Company Info.pdf")
        new_york = next(d for d in documents if d["title"] == "New York Brochure.pdf")
        london = next(d for d in documents if d["title"] == "London Brochure.pdf")
        client = MagicMock()
        client.search.side_effect = [
            result(documents), result(documents), result([new_york, info]),
            result([info]), result([london]), result([info]),
            [{"title": "London Brochure.pdf", "@search.reranker_score": 2.7}],
        ]
        with patch.object(setup, "SearchClient") as clients, \
                contextlib.redirect_stdout(io.StringIO()):
            clients.return_value.__enter__.return_value = client
            report = setup.validate_search("https://example.search.windows.net",
                                           "margies-index", MagicMock())
        self.assertEqual(report["document_count"], 6)
        self.assertEqual(
            report["guide_queries"]["new_york_under_380000"]["count"], 1
        )
        self.assertEqual(
            client.search.call_args_list[3].kwargs["filter"],
            "metadata_storage_size lt 380000",
        )
        self.assertEqual(client.search.call_args.kwargs["query_type"], "semantic")
        self.assertEqual(
            set(report["guide_queries"]),
            {"all_titles_locations", "new_york", "new_york_under_380000",
             "london", "flights"},
        )

    def test_existing_indexer_explicitly_run_without_reset(self):
        rest = MagicMock()
        rest.call.side_effect = [
            {"value": [{"name": "margies-index-indexer"}]},
            {"lastResult": {"status": "success", "startTime": "old"}},
            None, None, None, None, None,
        ]
        with patch.object(setup, "wait_for_indexer") as wait, \
                contextlib.redirect_stdout(io.StringIO()):
            setup.configure_pipeline(rest, "margies-index", "/storage", "documents", 60)
        wait.assert_called_once_with(rest, "margies-index", 60, "old")
        rest.call.assert_any_call("POST", "indexers/margies-index-indexer/run")
        self.assertFalse(any("reset" in str(call) for call in rest.call.call_args_list))


if __name__ == "__main__":
    unittest.main()
