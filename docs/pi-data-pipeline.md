# Raspberry Pi data pipeline

Run these commands from the repository root on the Raspberry Pi.

## Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill in the server-only Supabase values.
Never commit `.env` or share `SUPABASE_SECRET_KEY`.

## Run local logging and Supabase sync

```bash
python3 pi/main.py
```

Each valid ESP32 reading is saved to SQLite first and then sent to Supabase.
If sync fails, the reading remains marked `Synced: NO` locally. Stop the process
with `Ctrl+C`.

## Useful checks

Test the Supabase connection and list exposed tables:

```bash
python3 pi/test_supabase_connection.py
```

Print the latest 10 local readings:

```bash
python3 pi/print_readings.py
```

Upload all currently unsynced SQLite readings without opening the serial port:

```bash
python3 pi/sync_readings.py
```

Run the local-only serial and SQLite test without Supabase sync:

```bash
python3 pi/serial_test.py
```

## Clear Supabase test data

The readings table is intended to hold sensor history, so it should not be
cleared during normal operation. To deliberately delete every remote reading:

```bash
python3 pi/clear_supabase_readings.py
```

The script requires typing `DELETE ALL READINGS` before it sends the delete.
This does not clear SQLite or reset local `synced` flags, so previously synced
local rows will not be uploaded again.
