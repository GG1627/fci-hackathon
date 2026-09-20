import requests

from services.supabase_api import api_headers, load_supabase_config


CONFIRMATION = "DELETE ALL READINGS"


def main() -> None:
    print("WARNING: This permanently deletes every row in Supabase readings.")
    confirmation = input(f"Type {CONFIRMATION!r} to continue: ")
    if confirmation != CONFIRMATION:
        print("Cancelled. Nothing was deleted.")
        return

    try:
        supabase_url, secret_key = load_supabase_config()
        response = requests.delete(
            f"{supabase_url}/rest/v1/readings",
            headers=api_headers(secret_key, prefer="return=minimal"),
            params={"id": "not.is.null"},
            timeout=15,
        )
        response.raise_for_status()
    except (RuntimeError, requests.RequestException) as error:
        raise SystemExit(f"Could not clear Supabase readings: {error}") from error

    print("Supabase readings table cleared.")
    print("Local SQLite readings and their synced flags were not changed.")


if __name__ == "__main__":
    main()
