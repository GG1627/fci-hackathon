import json

from services.local_db import initialize_database, save_reading


PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200


def parse_reading(line: str) -> tuple[str, float, bool]:
    reading = json.loads(line)
    device_id = reading["device_id"]
    temperature = reading["temperature_f"]
    door_open = reading["door_open"]

    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id must be a non-empty string")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("temperature_f must be a number")
    if not isinstance(door_open, bool):
        raise ValueError("door_open must be a boolean")

    return device_id, float(temperature), door_open


def main() -> None:
    import serial

    initialize_database()

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as esp32:
            print(f"Reading ESP32 data from {PORT} at {BAUD_RATE} baud...")

            while True:
                line = esp32.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    device_id, temperature, door_open = parse_reading(line)
                    save_reading(device_id, temperature, door_open)
                    door = "OPEN" if door_open else "CLOSED"
                    print(f"Temp: {temperature:.1f} F | Door: {door}")
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    print(f"Skipping malformed line: {line}")
    except KeyboardInterrupt:
        print("\nSerial test stopped.")


if __name__ == "__main__":
    main()
