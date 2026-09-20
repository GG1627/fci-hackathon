from services.local_db import initialize_database, save_reading
from serial_reader import read_serial


def main() -> None:
    initialize_database()

    try:
        for device_id, temperature, door_open in read_serial():
            save_reading(device_id, temperature, door_open)
            door = "OPEN" if door_open else "CLOSED"
            print(f"Temp: {temperature:.1f} F | Door: {door}")
    except KeyboardInterrupt:
        print("\nSerial test stopped.")


if __name__ == "__main__":
    main()
