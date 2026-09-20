from services.supabase_api import load_supabase_config
from services.supabase_sync import SupabaseSyncError, sync_unsynced_readings


def main() -> None:
    try:
        supabase_url, secret_key = load_supabase_config()
    except RuntimeError as error:
        raise SystemExit(error) from error
    total_synced = 0

    try:
        while True:
            synced_count = sync_unsynced_readings(supabase_url, secret_key)
            total_synced += synced_count
            if synced_count < 100:
                break
    except SupabaseSyncError as error:
        raise SystemExit(error) from error

    print(f"Synced {total_synced} reading(s) to Supabase.")


if __name__ == "__main__":
    main()
