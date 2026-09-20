import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_supabase_config() -> tuple[str, str]:
    load_dotenv(ROOT_DIR / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    secret_key = os.getenv("SUPABASE_SECRET_KEY")
    if not supabase_url or not secret_key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_SECRET_KEY in the root .env file."
        )

    return supabase_url.rstrip("/"), secret_key


def api_headers(secret_key: str, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": secret_key,
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers
