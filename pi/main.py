from serial_reader import read_serial
from services.local_db import initialize_database, save_reading
from services.supabase_api import load_supabase_config
from services.supabase_sync import SupabaseSyncError, sync_unsynced_readings


def main() -> None:
    initialize_database()
    try:
        supabase_url, secret_key = load_supabase_config()
    except RuntimeError as error:
        raise SystemExit(error) from error
    sync_offline = False

    try:
        for device_id, temperature, door_open in read_serial():
            save_reading(device_id, temperature, door_open)
            door = "OPEN" if door_open else "CLOSED"
            print(f"Temp: {temperature:.1f} F | Door: {door}")

            try:
                synced_count = sync_unsynced_readings(supabase_url, secret_key)
                if sync_offline:
                    print("Supabase connection restored.")
                if synced_count > 1:
                    print(f"Synced {synced_count} queued readings.")
                sync_offline = False
            except SupabaseSyncError as error:
                if not sync_offline:
                    print(f"{error} Readings will remain queued in SQLite.")
                sync_offline = True
    except KeyboardInterrupt:
        print("\nFridgeGuard stopped.")


if __name__ == "__main__":
    main()
