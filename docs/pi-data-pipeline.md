# Raspberry Pi services

Sensor readings stay local in SQLite. Supabase is used only for camera images.

## Install and configure

From the repository root on the Pi:

```bash
python3 -m pip install -r requirements.txt
```

Create a root `.env` from `.env.example`. Fill in the Supabase credentials and
the Discord webhook URL. Never commit or share the populated `.env` file.

## Run everything

Production settings from `.env`:

```bash
python3 pi/main.py
```

For a demo with an image every 30 seconds:

```bash
python3 pi/main.py --camera-interval 30
```

This starts the SQLite serial logger, local API, camera scheduler, and Discord
alert monitor. Press `Ctrl+C` once to stop every service cleanly. Discord is
skipped when `DISCORD_WEBHOOK_URL` is empty.

Optional modes:

```bash
python3 pi/main.py --no-camera
python3 pi/main.py --no-alerts
```

## Useful checks

```bash
python3 pi/print_readings.py
python3 pi/camera_pipeline.py --once
python3 pi/manage_images.py list
python3 pi/alert_monitor.py --test
```

Legacy Supabase sensor-reading scripts remain in the repository for reference,
but they are not started by `pi/main.py` and are not part of the current
architecture.
