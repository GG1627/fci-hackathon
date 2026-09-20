# FridgeGuard local API

The API reads the Raspberry Pi's local SQLite database. It does not require an
internet connection or Supabase.

## Start the API

From the repository root on the Pi:

```bash
python3 -m pip install -r requirements.txt
python3 pi/api.py
```

The server listens on port `8000`. Stop it with `Ctrl+C`.

## Endpoints

Health check:

```text
GET http://localhost:8000/api/health
```

Latest reading and `ok`, `stale`, or `no_data` status:

```text
GET http://localhost:8000/api/status
```

Recent readings, newest first (default 50, maximum 500):

```text
GET http://localhost:8000/api/readings?limit=50
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

From another computer on the same network, replace `localhost` with the Pi's
hostname or IP address, for example:

```text
http://gaels-pi-5.local:8000/api/status
```

The API allows browser requests from other local development origins so a
future React app can poll `/api/status` every one or two seconds.
