from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
import requests

ARM_VERSION = "2025-06-01"


def required(name):
    value = os.getenv(name, "").strip()
    if not value or "<" in value or value.lower().startswith("your-"):
        raise ValueError(f"Configure {name} in this lab's local .env.")
    return value


def load_config(script):
    folder = Path(script).resolve().parent
    load_dotenv(folder / ".env")
    endpoint = required("AZURE_OPENAI_ENDPOINT").rstrip("/") + "/"
    parts = urlsplit(endpoint)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.path != "/openai/v1/"
        or parts.query
        or parts.fragment
        or parts.username
        or parts.password
    ):
        raise ValueError("AZURE_OPENAI_ENDPOINT must be an HTTPS resource /openai/v1/ URL.")
    return folder, endpoint, required("MODEL_DEPLOYMENT")


@contextmanager
def model_client(endpoint):
    with DefaultAzureCredential() as credential, OpenAI(
        base_url=endpoint,
        api_key=get_bearer_token_provider(credential, "https://ai.azure.com/.default"),
        timeout=120,
        max_retries=2,
    ) as client:
        yield client


def completed_text(response):
    if response.status != "completed":
        raise RuntimeError(f"Response not completed: {response.status}; {response.error}")
    text = response.output_text.strip()
    if not text:
        raise RuntimeError("The completed response contained no output text.")
    return text


def save_report(folder, name, report):
    target = folder / "results" / name
    target.parent.mkdir(exist_ok=True)
    content = {"recorded_at": datetime.now(timezone.utc).isoformat(), **report}
    target.write_text(json.dumps(content, indent=2, default=str), encoding="utf-8")
    print(f"Saved local report: {target}")
    return target


def account_path():
    return (
        f"/subscriptions/{required('AZURE_SUBSCRIPTION_ID')}"
        f"/resourceGroups/{required('AZURE_RESOURCE_GROUP')}"
        "/providers/Microsoft.CognitiveServices/accounts/"
        f"{required('AZURE_AI_ACCOUNT_NAME')}"
    )


def arm_get(credential, path):
    response = requests.get(
        f"https://management.azure.com{path}",
        params={"api-version": ARM_VERSION},
        headers={
            "Authorization": "Bearer "
            + credential.get_token("https://management.azure.com/.default").token
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def run(main):
    try:
        result = main()
        return result if isinstance(result, int) else 0
    except (AzureError, OpenAIError, requests.RequestException,
            ValueError, OSError, RuntimeError) as exc:
        print(f"Lab failed: {exc}", file=sys.stderr)
        return 1
