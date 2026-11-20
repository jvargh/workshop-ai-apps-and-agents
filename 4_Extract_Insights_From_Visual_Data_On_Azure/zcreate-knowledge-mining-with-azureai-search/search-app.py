import sys

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from lab_config import load_search_config


def main():
    try:
        # Get config settings and authenticate with the signed-in Azure identity.
        search_endpoint, index = load_search_config()
        with DefaultAzureCredential() as credential, SearchClient(
            search_endpoint, index, credential
        ) as search_client:
            while True:
                try:
                    query_text = input(
                        "Enter a query (or type 'quit' to exit): "
                    ).strip()
                except EOFError:
                    break
                if query_text.lower() == "quit":
                    break
                if not query_text:
                    print("Please enter a query.")
                    continue

                found_documents = search_client.search(
                    search_text=query_text,
                    select=["title", "locations", "persons", "keyPhrases"],
                    order_by=["title"],
                    include_total_count=True,
                )

                print(f"\nSearch returned {found_documents.get_count()} documents:")
                for document in found_documents:
                    print(f"\nDocument: {document['title']}")
                    for field, label in (
                        ("locations", "Locations"),
                        ("persons", "People"),
                        ("keyPhrases", "Key phrases"),
                    ):
                        print(f" - {label}:")
                        for value in document[field]:
                            print(f"   - {value}")
        return 0
    except (AzureError, ValueError, OSError) as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
