from dotenv import load_dotenv
import os
import sys
import json
import argparse
from pathlib import Path
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import StringField
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential


def main():
    parser = argparse.ArgumentParser(description="Extract contact details from a business card.")
    parser.add_argument("image_file", nargs="?", default="biz-card-1.png")
    parser.add_argument("--output", default="results.json", help="JSON output path, relative to this lab folder unless absolute.")
    args = parser.parse_args()

    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    try:

        # Get the business card
        lab_dir = Path(__file__).resolve().parent
        image_file = lab_dir / args.image_file
        output_file = lab_dir / args.output

        # Get config settings
        load_dotenv(lab_dir / ".env")
        ai_svc_endpoint = os.getenv('ENDPOINT')
        analyzer = os.getenv('ANALYZER_NAME')

        # Analyze the business card
        analyze_card(image_file, analyzer, ai_svc_endpoint, output_file)

    except (AzureError, OSError, ValueError) as ex:
        print(f"Card analysis failed: {ex}", file=sys.stderr)
        raise SystemExit(1) from ex



def analyze_card(image_file, analyzer, endpoint, output_file):
    
    # Use Content Understanding to analyze the image
    if not endpoint or endpoint == "YOUR_ENDPOINT":
        raise ValueError("Set ENDPOINT in this lab's .env to the Foundry resource root endpoint.")
    if not analyzer:
        raise ValueError("Set ANALYZER_NAME in this lab's .env.")
    print(f"Reading business card image: {image_file}", flush=True)
    image_data = Path(image_file).read_bytes()
    with DefaultAzureCredential() as credential, ContentUnderstandingClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2025-11-01"
    ) as client:
        print(f"Submitting image to analyzer '{analyzer}'...", flush=True)
        poller = client.begin_analyze_binary(
            analyzer_id=analyzer,
            binary_input=image_data
        )
        print("Request accepted. Waiting for analysis results...", flush=True)
        result = poller.result()
        if not result.contents:
            raise ValueError("The analyzer returned no content.")
        extracted_cards = []
        for content in result.contents:
            if not content.fields:
                raise ValueError("The analyzer returned content without contact fields.")
            values = {}
            for name in ("Company", "Name", "Title", "Email", "Phone"):
                field = content.fields.get(name)
                if not isinstance(field, StringField):
                    raise ValueError(f"The analyzer returned a missing or non-string {name} field.")
                values[name] = field.value_string
            extracted_cards.append(values)

        print(f"Extracted contact fields from {len(extracted_cards)} result(s).")
        print(f"Writing full JSON response to: {output_file}", flush=True)
        with Path(output_file).open("w", encoding="utf-8") as json_file:
            json.dump(result.as_dict(), json_file, indent=4, ensure_ascii=False)
        print("Analysis complete. JSON response saved.")
        for index, values in enumerate(extracted_cards, start=1):
            print(f"\nCard {index}")
            for field_name, value in values.items():
                print(f"  {field_name}: {value if value else '(not found on card)'}")




if __name__ == "__main__":
    main()        
