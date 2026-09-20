# FridgeGuard Agent Guide

## Project

FridgeGuard monitors the Gainesville Community Fridge. Read
`FRIDGEGUARD_PLAN_UPDATED.md` before making architectural decisions.

## Confirmed Working State

- The ESP32 reads the TMP117 temperature sensor.
- The ESP32 reads the reed-switch door sensor.
- The ESP32 sends one newline-delimited JSON object per second at 115200 baud.
- The Raspberry Pi detects the ESP32 at `/dev/ttyUSB0`.
- Raspberry Pi serial parsing is working reliably.
- Every valid reading is stored in the local SQLite database.
- The latest stored readings can be read back successfully on the Raspberry Pi.
- The Raspberry Pi Camera Module 3 is connected and working.
- `rpicam-still` successfully captures JPEG images on the Raspberry Pi.

Completed pipeline:

```text
TMP117 + reed switch -> ESP32 -> USB serial JSON -> Raspberry Pi parser -> SQLite
```

```text
Camera Module 3 -> Raspberry Pi -> periodic JPEG -> Supabase Storage -> dashboard
```

Sensor readings remain local in SQLite and are not synced to Supabase.
Supabase is used only for cloud image storage in the `fridge-images` bucket.

## Current Task

Implement and verify the independent camera pipeline: periodically capture a
still image, upload it to Supabase Storage with a timestamped name, and retain
the latest image plus ten previous images (11 total). Use size-conscious JPEG
settings and keep a safe manual image-list/cleanup command. Do not add computer
vision yet.

## Serial Contract

One JSON object per line:

```json
{
  "device_id": "fridge-sensor-01",
  "temperature_f": 75.7,
  "door_open": false
}
```

Do not change this contract without updating both the ESP32 firmware and the
Raspberry Pi parser.

## Build Order

ESP32 sensing, Raspberry Pi serial parsing, and SQLite logging are complete.
Continue in this order:

1. Camera capture and Supabase image upload (current)
2. Web dashboard
3. Discord webhook alerts
4. Stock estimation
5. Polish and documentation

Do not move to stretch features until the core sensor-to-local-storage pipeline
is stable.

## Constraints

- Keep the architecture simple and hackathon-friendly.
- Prefer verified working hardware and data flow over additional features.
- Use USB serial between the ESP32 and Raspberry Pi, not Bluetooth.
- Keep serial parsing separate from storage, cloud, alert, and camera logic.
- Keep the camera pipeline separate from the ESP32 and SQLite sensor pipeline.
- Do not sync sensor readings to Supabase.
- Use timestamped image names and retain only the newest 11 cloud images.
- Do not add login/auth unless absolutely necessary.
- Use Discord webhooks rather than a full Discord bot.
- Do not add complex ML while simple OpenCV remains sufficient.
- Never commit secrets, credentials, webhook URLs, or populated `.env` files.
- Keep `.env` files out of Git; commit only safe placeholders when needed.
