import json
from collections.abc import Iterator


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


def read_serial(port: str = PORT, baud_rate: int = BAUD_RATE) -> Iterator[tuple[str, float, bool]]:
    import serial

    with serial.Serial(port, baud_rate, timeout=1) as esp32:
        print(f"Reading ESP32 data from {port} at {baud_rate} baud...")

        while True:
            line = esp32.readline().decode("utf-8", errors="replace").strip()
            if not line:
                continue

            try:
                yield parse_reading(line)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                print(f"Skipping malformed line: {line}")
