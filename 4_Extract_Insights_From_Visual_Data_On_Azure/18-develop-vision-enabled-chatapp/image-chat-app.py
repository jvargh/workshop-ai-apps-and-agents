import argparse
import base64
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

# Add references
from openai import OpenAI, OpenAIError
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def main():
    parser = argparse.ArgumentParser(description="Ask questions about fruit images.")
    parser.add_argument(
        "--image-source",
        choices=("local", "url"),
        default="local",
        help="Use the local mystery fruit (default) or the guide's public orange URL."
    )
    args = parser.parse_args()
    os.system("cls" if os.name == "nt" else "clear")

    try:
        # Get configuration settings
        lab_dir = Path(__file__).resolve().parent
        load_dotenv(lab_dir / ".env")
        openai_endpoint = os.getenv("ENDPOINT")
        model_deployment = os.getenv("MODEL_DEPLOYMENT")
        endpoint_parts = urlsplit(openai_endpoint or "")
        if (
            endpoint_parts.scheme != "https"
            or not endpoint_parts.hostname
            or endpoint_parts.path.rstrip("/") != "/openai/v1"
            or endpoint_parts.query
            or endpoint_parts.fragment
        ):
            raise ValueError("Set ENDPOINT to https://<resource>.openai.azure.com/openai/v1/ in this lab's .env.")
        if not model_deployment:
            raise ValueError("Set MODEL_DEPLOYMENT to your vision-capable deployment name.")

        # Create an OpenAI client
        with DefaultAzureCredential() as credential:
            token_provider = get_bearer_token_provider(
                credential, "https://ai.azure.com/.default"
            )
            with OpenAI(
                base_url=openai_endpoint,
                api_key=token_provider,
                timeout=120
            ) as client:
                # Initialize prompts
                system_message = (
                    "You are an AI assistant in a grocery store that sells fruit. "
                    "You provide detailed answers to questions about produce."
                )
                print(f"Image source: {args.image_source}")
                while True:
                    prompt = input(
                        "\nAsk a question about the image\n(or type 'quit' to exit)\n"
                    ).strip()
                    if prompt.lower() == "quit":
                        break
                    if not prompt:
                        print("Please enter a question.\n")
                        continue
                    print("Getting a response ...\n")

                    # Get a response to image input
                    if args.image_source == "url":
                        image_url = (
                            "https://microsoftlearning.github.io/mslearn-ai-vision/"
                            "Labfiles/gen-ai-vision/orange.jpeg"
                        )
                    else:
                        image_path = lab_dir / "mystery-fruit.jpeg"
                        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
                        image_url = f"data:image/jpeg;base64,{image_data}"

                    response = client.responses.create(
                        model=model_deployment,
                        input=[
                            {"role": "developer", "content": system_message},
                            {"role": "user", "content": [
                                {"type": "input_text", "text": prompt},
                                {"type": "input_image", "image_url": image_url}
                            ]}
                        ]
                    )
                    if response.status != "completed" or not response.output_text.strip():
                        raise ValueError(
                            f"The model returned no completed text response (status: {response.status})."
                        )
                    print(response.output_text)
    except (AzureError, OpenAIError, OSError, ValueError) as error:
        print(f"Image chat failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
