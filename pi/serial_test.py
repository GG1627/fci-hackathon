import json

import serial


PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200


def main() -> None:
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as esp32:
            print(f"Reading ESP32 data from {PORT} at {BAUD_RATE} baud...")

            while True:
                line = esp32.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    reading = json.loads(line)
                    temperature = float(reading["temperature_f"])
                    door = "OPEN" if reading["door_open"] else "CLOSED"
                    print(f"Temp: {temperature:.1f} F | Door: {door}")
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    print(f"Skipping malformed line: {line}")
    except KeyboardInterrupt:
        print("\nSerial test stopped.")


if __name__ == "__main__":
    main()
