import sys, os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv

# Add references
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput, AnalysisResult
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential


def main():
    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    # Get configuration settings 
    lab_dir = Path(__file__).parent
    load_dotenv(lab_dir / ".env")
    endpoint = os.getenv("ENDPOINT")
    analyzer_id = os.getenv("ANALYZER")
    api_version = "2025-11-01"

    # Set up Content Understanding client
    try:
        endpoint_parts = urlsplit(endpoint or "")
        if (
            endpoint_parts.scheme != "https"
            or not endpoint_parts.netloc
            or endpoint_parts.path not in ("", "/")
            or endpoint_parts.query
            or endpoint_parts.fragment
        ):
            raise ValueError("Set ENDPOINT to the Foundry resource root, https://<resource>.services.ai.azure.com/.")
        if not analyzer_id or analyzer_id == "your_analyzer_id":
            raise ValueError("Set ANALYZER to your published Content Understanding analyzer ID.")

        with DefaultAzureCredential() as credential, ContentUnderstandingClient(
            endpoint=endpoint,
            credential=credential,
            api_version=api_version
        ) as client:
            while True:
                file_no = input('\nChoose a file (1, 2, or 3), or anything else to exit: ').strip()
                if file_no not in ["1", "2", "3"]:
                    break

                file_path = lab_dir / "images" / f"image{file_no}.jpg"
                file_bytes = file_path.read_bytes()

                print(f"Analyzing with {analyzer_id} analyzer...")
                print(f"  File: {file_path}\n")

                # Analyze the file
                poller = client.begin_analyze(
                    analyzer_id=analyzer_id,
                    inputs=[AnalysisInput(data=file_bytes)]
                )
                result: AnalysisResult = poller.result()
                if not result.contents:
                    raise ValueError("The analyzer returned no image content.")
                fields = result.contents[0].fields
                if not fields or "Description" not in fields or "Tags" not in fields:
                    raise ValueError("The analyzer must return both Description and Tags fields.")
                description = fields["Description"].value_string
                tags = fields["Tags"].value_array
                if not description or not description.strip() or not tags:
                    raise ValueError("The analyzer returned an empty Description or Tags field.")
                if any(not tag.value_string or not tag.value_string.strip() for tag in tags):
                    raise ValueError("The analyzer returned a tag without a string value.")

                print(f"Description:\n{description}\n")
                print("Tags:")
                for tag in tags:
                    print("  -", tag.value_string)
    except AzureError as err:
        print(f"[Azure Error]: {err}", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError) as err:
        print(f"[Configuration or Analysis Error]: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()