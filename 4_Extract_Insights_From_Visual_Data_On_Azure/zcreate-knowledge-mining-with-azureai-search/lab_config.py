import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

LAB_DIR = Path(__file__).resolve().parent


def required_setting(name):
    value = os.getenv(name, "").strip()
    if not value or value.lower().startswith("your_"):
        raise ValueError(f"Set {name} in {LAB_DIR / '.env'}.")
    return value


def load_search_config():
    load_dotenv(LAB_DIR / ".env")
    endpoint = required_setting("SEARCH_ENDPOINT").rstrip("/")
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("SEARCH_ENDPOINT must be an HTTPS Search service root URL.")
    return endpoint, required_setting("INDEX_NAME")
