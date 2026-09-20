from urllib.parse import urlparse

import requests
from services.supabase_api import api_headers, load_supabase_config


def main() -> None:
    try:
        supabase_url, secret_key = load_supabase_config()
        response = requests.get(
            f"{supabase_url.rstrip('/')}/rest/v1/",
            headers={**api_headers(secret_key), "Accept": "application/openapi+json"},
            timeout=15,
        )
        response.raise_for_status()
        schema = response.json()
    except (RuntimeError, requests.RequestException, ValueError) as error:
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
