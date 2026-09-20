from services.local_db import get_latest_readings


def main() -> None:
    readings = get_latest_readings(limit=10)

    if not readings:
        print("No readings found.")
        return

    for reading in readings:
        door = "OPEN" if reading["door_open"] else "CLOSED"
        synced = "YES" if reading["synced"] else "NO"
        print(
            f'{reading["timestamp"]} | {reading["device_id"]} | '
            f'Temp: {reading["temperature_f"]:.1f} F | Door: {door} | '
            f"Synced: {synced}"
        )


if __name__ == "__main__":
    main()
