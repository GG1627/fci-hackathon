# Community Chill local API

The API reads sensor data from the Raspberry Pi's local SQLite database. It
also returns public URLs for camera images stored in Supabase. Supabase secrets
remain on the Pi and are never returned to the browser.

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

Latest reading, door-open start time, configured temperature threshold,
freshness, health level, active rule conditions, and message:

```text
GET http://localhost:8000/api/status
```

Freshness is `ok`, `stale`, or `no_data`. Health is independently reported as
`good`, `warning`, `critical`, or `unknown`, with conditions such as
`TEMP_HIGH`, `DOOR_OPEN_TOO_LONG`, and `DEVICE_OFFLINE`.

Recent readings, newest first (default 50, maximum 500):

```text
GET http://localhost:8000/api/readings?limit=50
```

Latest camera image plus up to ten previous images, newest first:

```text
GET http://localhost:8000/api/images
```

Example response:

```json
{
  "latest": {
    "name": "fridge-20260920T194553Z.jpg",
    "timestamp": "2026-09-20T19:45:53Z",
    "url": "https://PROJECT.supabase.co/storage/v1/object/public/fridge-images/fridge-20260920T194553Z.jpg"
  },
  "history": []
}
```

If Supabase is temporarily unavailable, only `/api/images` returns HTTP 503;
the local sensor endpoints continue working.

Interactive API documentation:

```text
http://localhost:8000/docs
```

From another computer on the same network, replace `localhost` with the Pi's
hostname or IP address, for example:

```text
http://gaels-pi-5.local:8000/api/status
```

The API allows browser requests from other local development origins. The
Community Chill dashboard polls `/api/status` and `/api/readings` every five
seconds and `/api/images` every 30 seconds.
