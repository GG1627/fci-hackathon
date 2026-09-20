from pathlib import Path

import requests

from services.local_db import (
    DEFAULT_DB_PATH,
    get_unsynced_readings,
    mark_readings_synced,
)
from services.supabase_api import api_headers


class SupabaseSyncError(RuntimeError):
    pass


def sync_unsynced_readings(
    supabase_url: str,
    secret_key: str,
    db_path: Path = DEFAULT_DB_PATH,
    batch_size: int = 100,
) -> int:
    readings = get_unsynced_readings(limit=batch_size, db_path=db_path)
    if not readings:
        return 0

    payload = [
        {
            "device_id": reading["device_id"],
            "timestamp": reading["timestamp"],
            "temperature_f": reading["temperature_f"],
            "door_open": bool(reading["door_open"]),
        }
        for reading in readings
    ]

    try:
        response = requests.post(
            f"{supabase_url}/rest/v1/readings",
            headers=api_headers(secret_key, prefer="return=minimal"),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise SupabaseSyncError(f"Supabase sync failed: {error}") from error

    mark_readings_synced([reading["id"] for reading in readings], db_path)
    return len(readings)
