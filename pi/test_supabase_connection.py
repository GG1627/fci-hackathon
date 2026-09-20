import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(ROOT_DIR / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    secret_key = os.getenv("SUPABASE_SECRET_KEY")
    if not supabase_url or not secret_key:
        raise SystemExit(
            "Missing SUPABASE_URL or SUPABASE_SECRET_KEY in the root .env file."
        )

    try:
        response = requests.get(
            f"{supabase_url.rstrip('/')}/rest/v1/",
            headers={
                "Accept": "application/openapi+json",
                "apikey": secret_key,
            },
            timeout=15,
        )
        response.raise_for_status()
        schema = response.json()
    except (requests.RequestException, ValueError) as error:
        raise SystemExit(f"Supabase connection failed: {error}") from error

    tables = sorted(
        path.removeprefix("/")
        for path in schema.get("paths", {})
        if path.startswith("/") and path.count("/") == 1 and path != "/"
    )

    project_host = urlparse(supabase_url).netloc
    print(f"Connected successfully to {project_host}.")
    if not tables:
        print("No tables are currently exposed through the Data API.")
        return

    print("Tables exposed through the Data API:")
    for table in tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
