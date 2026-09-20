# FridgeGuard — Gainesville Community Fridge Hackathon Plan

## Project Summary

**Project Name:** FridgeGuard  
**Track:** Gainesville Community Fridge Hardware  
**Event:** CityCamp Gainesville Hack Day  
**Date:** Sunday, September 20, 2026  
**Build Window:** 10:00 AM–5:00 PM submission deadline  
**Location:** Reitz Union, Room G330, University of Florida

### One-Sentence Pitch

> FridgeGuard is a low-cost, offline-friendly monitoring system that watches the Gainesville Community Fridge when volunteers are not on site and alerts them when the fridge needs attention.

### Core Problem

The Gainesville Community Fridge will run outdoors, off-grid, and mostly unattended. Volunteers may only visit about once per week.

Between visits, the team needs to know:

- Is the fridge staying cold enough to keep food safe?
- Was the door accidentally left open?
- Is the fridge running low on food?
- Is the monitoring system still online and reporting?
- Does a Fridge Warrior need to visit the site?

FridgeGuard should answer one simple operational question:

> **Does someone need to check the fridge right now?**

---

# 1. Locked Prototype Architecture

For the hackathon prototype, use:

- **ESP32** for low-power continuous sensor reads
- **Raspberry Pi 5** for edge processing, camera, local storage, cloud sync, and alerts
- **USB serial** between ESP32 and Pi
- **Supabase Postgres** for remote sensor/event data
- **Supabase Storage** for the latest fridge image
- **Next.js/React dashboard** for remote monitoring
- **Discord webhook** for one-way volunteer alerts

```text
                     FRIDGEGUARD

                         ESP32
                    ┌─────┴─────┐
                    │           │
             Temperature     Door Sensor
                Sensor       Reed Switch
                    │           │
                    └─────┬─────┘
                          │
                      USB Serial
                          │
                          ▼
                   Raspberry Pi 5
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
        SQLite        Pi Camera      Rule Engine
           │              │              │
           │          OpenCV             │
           │              │              │
           │         Stock Level         │
           │              │              │
           └──────────────┼──────────────┘
                          │
                          ▼
                       Supabase
                 ┌────────┴────────┐
                 │                 │
              Postgres          Storage
                 │                 │
          Sensor History      latest.jpg
                 │                 │
                 └────────┬────────┘
                          │
                   ┌──────┴──────┐
                   ▼             ▼
              Web Dashboard   Discord
                               Webhook
```

---

# 2. Why Use Both ESP32 and Raspberry Pi 5

## ESP32 Role

The ESP32 acts as the simple low-power sensor node.

Responsibilities:

- read temperature
- read door state
- send readings to Pi over USB serial

Example serial payload:

```json
{
  "temperature_f": 38.4,
  "door_open": false
}
```

The ESP32 should stay intentionally simple.

It should NOT need to:

- host the dashboard
- run SQLite
- upload images
- run computer vision
- manage Discord
- handle complicated cloud logic

## Raspberry Pi 5 Role

The Pi acts as the edge computer / gateway.

Responsibilities:

- receive ESP32 readings
- save readings locally
- evaluate alert rules
- capture images
- estimate stock level
- sync data to Supabase
- upload latest image
- trigger Discord webhooks
- queue data when internet is unavailable

---

# 3. Final Deployment vs Hackathon Prototype

The Raspberry Pi 5 is useful for the hackathon because it is already available and supports the Camera Module 3 easily.

It is not necessarily the ideal permanent off-grid hardware.

## Hackathon Prototype

```text
ESP32
├── temperature
└── door
      │
      ▼
Raspberry Pi 5
├── SQLite
├── Camera Module 3
├── OpenCV
├── cloud sync
└── Discord alerts
```

## Future Deployment Concept

A lower-power deployed version could use:

```text
ESP32-class camera board
├── temperature
├── door
├── periodic image capture
├── simple stock estimation
├── local buffering
└── Wi-Fi sync
```

The camera would NOT stream continuously.

Possible behavior:

- wake every few minutes
- capture one image
- estimate Full / Medium / Low
- upload result
- sleep again

Or capture only after:

- a door-open event
- a door-close event
- a scheduled interval

### Judge Explanation

> Our prototype uses a Raspberry Pi 5 because we already had a compatible camera and it let us rapidly demonstrate sensing, computer vision, local storage, and remote monitoring. A deployed version could move the always-on sensing and periodic image capture to a lower-power ESP32-class camera device.

---

# 4. Existing Hardware

Already available:

- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- ESP32
- temperature sensor
- miscellaneous electronics

Bring:

- Pi 5
- Pi power supply
- Camera Module 3
- correct camera ribbon cable
- microSD card
- ESP32
- temperature sensor
- USB cable for ESP32 → Pi serial
- breadboard
- jumper wires
- resistors
- laptop
- Ethernet cable if available
- USB power bank if available
- LEDs/buttons/switches
- tape
- cardboard / small box
- magnet if available
- screwdriver/basic tools

---

# 5. Parts to Grab at the Hackathon

## Highest Priority

### Magnetic Reed Switch + Magnet

Purpose:

- detect door open / closed
- measure open duration
- detect door-left-open incidents
- help explain rising temperature

This is the preferred door sensor.

### Breadboard / Jumper Wires / Resistors

Needed for integration.

### DS18B20 Waterproof Temperature Probe

Grab one if available even if another temperature sensor is already owned.

Why:

- designed for this kind of environment
- easy fridge probe placement
- widely supported

## Useful If Available

### INA219 / INA226

Optional power telemetry:

- voltage
- current
- rough power measurement

Do not make the build depend on this.

### Small OLED / LCD / E-Ink

Optional local status display.

### BME280

Optional humidity/ambient sensor.

---

# 6. Door Monitoring

Preferred hardware:

> **Magnetic reed switch**

Advantages:

- extremely low power
- cheap
- reliable
- easy to wire
- works well on a refrigerator door
- ideal for both prototype and deployment

Track:

- current state
- open timestamp
- close timestamp
- open duration
- number of openings
- longest opening

Example:

```text
Door: OPEN
Open for: 2m 14s
```

Potential alert:

> Door has remained open longer than expected.

---

# 7. Temperature Monitoring

Food-safe target:

> Refrigerator temperature should remain at or below **40°F / 4°C**.

Example normal state:

```text
Temperature
37.6°F
SAFE
```

Example problem:

```text
Temperature
44.2°F
WARNING
```

### Demo Mode

The bench prototype will not be inside a real refrigerator.

Use configurable thresholds.

Production:

```text
SAFE_TEMP_MAX_F = 40
```

Demo:

```text
DEMO_TEMP_MAX_F = room_temperature + small_delta
```

Warm the sensor using a finger/hand.

Explain to judges:

> The deployed safety threshold is 40°F. For the room-temperature demo, we temporarily changed the trigger threshold so you can see the alert logic operate live.

---

# 8. Camera / Computer Vision

Use:

- Raspberry Pi Camera Module 3
- Picamera2
- OpenCV

Do NOT depend on MediaPipe.

Do NOT require a trained neural network for the MVP.

## Stock Goal

Estimate:

```text
FULL
MEDIUM
LOW
EMPTY
```

Do not try to identify every food item.

## MVP Vision Pipeline

```text
Capture Still Image
      ↓
Crop Known Shelf Region
      ↓
Compare With Empty-Shelf Reference
      ↓
Estimate Occupied Area / Image Difference
      ↓
Classify Stock Level
```

Possible simple techniques:

- background subtraction
- pixel difference
- contour area
- edge density
- shelf visibility
- thresholding

Because the camera position is fixed, simple computer vision may be enough.

## ML / YOLO

Only consider YOLO or another model if:

- core system is already reliable
- OpenCV approach is insufficient
- install/runtime is already verified

Do not make PyTorch/YOLO a Sunday dependency unless tested beforehand.

---

# 9. Image Storage Strategy

The Pi should not continuously archive every image.

Preferred:

```text
fridge/latest.jpg
```

Overwrite the same cloud object after each relevant capture.

Optional:

```text
fridge/latest.jpg
fridge/previous-1.jpg
fridge/previous-2.jpg
```

Use Supabase Storage rather than creating a separate AWS/S3 setup.

Website can display:

```text
Latest Fridge View

[ latest image ]

Captured: 2:42 PM
Stock: LOW
```

This keeps storage use tiny.

---

# 10. Image Capture Frequency

## Hackathon Demo

Capture frequently enough that changes are visible quickly.

Example:

- every 5–10 seconds in demo mode
- manual refresh button
- capture after door state change

## Real Deployment

Do not continuously stream video.

Possible:

- capture every 5–15 minutes
- capture after the door closes
- capture only during selected hours
- use a lower-power camera board

---

# 11. Local Storage / Offline Behavior

The Pi should use SQLite.

The ESP32 does not need SQLite.

Flow:

```text
ESP32 reading
      ↓
USB serial
      ↓
Pi
      ↓
SQLite first
      ↓
Try cloud sync
      ↓
Internet?
 ┌───────┴───────┐
YES              NO
 ↓                ↓
Upload         Keep queued
                   ↓
             Retry later
```

Local logging is important because the site may have weak connectivity.

---

# 12. Cloud Database

Use **Supabase Postgres**.

The remote web dashboard should read cloud data.

Suggested tables:

## readings

```text
id
device_id
timestamp
temperature_f
door_open
door_open_seconds
stock_level
health
sync_source
```

## events

```text
id
device_id
timestamp
type
severity
message
resolved
```

Possible event types:

```text
TEMP_HIGH
DOOR_OPEN_TOO_LONG
STOCK_LOW
DEVICE_OFFLINE
DEVICE_RESTORED
TEMP_RECOVERED
DOOR_CLOSED
```

---

# 13. Supabase Storage

Use Supabase Storage for the latest image.

Suggested path:

```text
fridge/latest.jpg
```

Overwrite instead of accumulating thousands of photos.

Possible metadata in database:

```text
latest_image_url
latest_image_timestamp
stock_level
```

---

# 14. Remote Web Dashboard

Recommended:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Vercel deployment

Dashboard should be understandable by a non-engineer immediately.

## Main View

```text
Gainesville Community Fridge

STATUS
🟢 ALL GOOD

Temperature
37.6°F
Safe

Door
Closed

Stock
Medium

Last Update
2 minutes ago

Latest Fridge View
[ photo ]
```

Problem state:

```text
🔴 NEEDS ATTENTION

Temperature
44.2°F

Door
Open for 6 min

Stock
Low

Fridge Warrior alerted
```

---

# 15. Stale Data / Offline Fail-Safe

Never show stale information as healthy.

Bad:

```text
🟢 ALL GOOD
37°F
```

if the reading is nine hours old.

Better:

```text
⚪ STATUS UNKNOWN

Last reading:
9 hours ago

FridgeGuard may be offline.
```

Suggested statuses:

```text
GREEN   All good
YELLOW  Attention soon
RED     Action recommended
GRAY    Current status unknown
```

---

# 16. Discord Alerts

Use a **Discord webhook**, not a full Discord bot.

Advantages:

- free
- extremely simple
- no bot token
- no OAuth
- no WebSocket connection
- no long-running Discord client

## Testing Setup

Create a personal test server:

```text
FridgeGuard Testing
└── #fridge-alerts
```

Create a webhook in that channel.

Store URL in:

```text
.env
```

Example:

```text
DISCORD_WEBHOOK_URL=...
```

Never commit the real webhook URL.

Commit only:

```text
DISCORD_WEBHOOK_URL=
```

in `.env.example`.

## Who Sends the Message?

The webhook appears as the sender.

Configure display name:

```text
FridgeGuard
```

Optional avatar.

## Example Alert

```text
🧊 FridgeGuard

🚨 Temperature Alert

Temperature: 44.1°F
Door: OPEN
Open duration: 5m 12s

Possible cause:
Door may have been left open.

Recommended action:
Check the community fridge.
```

---

# 17. Discord + Latest Image

When useful, alerts can include the latest fridge image.

Preferred flow:

```text
Pi Camera
   ↓
latest.jpg
   ↓
Supabase Storage
   ├── Dashboard
   └── Discord image/embed
```

Possible alert:

```text
🚨 Stock Alert

Stock level appears LOW.

Temperature: 38.1°F
Door: Closed

[latest fridge image]
```

---

# 18. Cause-Aware Alerts

Do not simply dump sensor values.

Combine signals.

## Temperature High + Door Open

```text
Likely door issue
```

Message:

> Fridge temperature is rising and the door has remained open. Check that the fridge is fully closed.

## Temperature High + Door Closed

```text
Possible cooling / power issue
```

Message:

> Temperature is above the configured safe threshold while the door is closed. Check refrigeration and power.

## Stock Low

Message:

> Fridge stock appears low. Consider scheduling a restock visit.

## Device Stale

Message:

> FridgeGuard has not reported recently. Current fridge status is unknown.

---

# 19. Alert Rate Limiting

Do not spam Discord.

Example:

```text
Alert triggered
↓
Send once
↓
Start cooldown
↓
Only resend if:
- state worsens
- long interval passes
- system recovered and fails again
```

Recovery message:

```text
✅ FridgeGuard Recovered

Temperature has returned to the configured safe range.

Door: Closed
```

---

# 20. Saturday Pre-Hackathon Setup

Do as much of this as possible before Sunday.

## Raspberry Pi OS

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

## Camera

Install/verify:

```bash
sudo apt install -y   python3-picamera2   python3-opencv   python3-venv   python3-pip   python3-serial   git
```

Verify:

```bash
rpicam-hello
```

Capture one still image.

## Python Environment

Create:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

Install lightweight dependencies:

```bash
pip install requests python-dotenv supabase pyserial
```

## Camera Test

Verify:

```python
from picamera2 import Picamera2
```

and:

```python
import cv2
```

both work.

Capture and process one image.

## ESP32 Serial Test

Before real sensors are wired, flash firmware that outputs fake data:

```json
{"temperature_f":72.5,"door_open":false}
```

every few seconds.

Connect ESP32 to Pi via USB.

Verify the Pi can read serial messages.

Goal:

```text
ESP32 fake data
      ↓
USB
      ↓
Pi Python
```

works before the event.

## SQLite Test

Create one local database and write/read one dummy record.

## Supabase

Before Sunday:

- create project
- create `readings` table
- create `events` table
- create Storage bucket
- test one insert from Pi
- test one read from website
- test one image upload

## Discord

Before Sunday:

- create test Discord server
- create `#fridge-alerts`
- create webhook
- test webhook from Pi
- verify notification arrives on phone

## Website

Before Sunday:

- deploy blank/early dashboard to Vercel
- verify Supabase reads work
- verify mobile layout loads

---

# 21. MVP Scope

## Must Work

- [ ] ESP32 sends sensor values over USB serial
- [ ] real temperature sensor works
- [ ] real reed switch works if available
- [ ] Pi reads serial data
- [ ] Pi saves readings to SQLite
- [ ] Pi syncs readings to Supabase
- [ ] dashboard displays current data
- [ ] stale data becomes UNKNOWN
- [ ] Discord webhook alerts work
- [ ] physical bench demo works

## Strong Target

- [ ] cause-aware alerts
- [ ] queued offline sync
- [ ] recovery alerts
- [ ] event history
- [ ] polished dashboard
- [ ] physical cardboard fridge/door setup

## Stretch

- [ ] Camera stock estimation
- [ ] latest fridge image on dashboard
- [ ] image in Discord alert
- [ ] INA219/INA226 telemetry
- [ ] OLED/e-ink display
- [ ] advanced stock vision

---

# 22. If No Door Sensor Is Available

Fallback:

Use camera-based door detection.

Example concept:

```text
Capture image
↓
Detect whether fridge interior / known marker is visible
↓
Infer likely OPEN / CLOSED
```

This is acceptable for the prototype.

However:

> A magnetic reed switch is still the preferred real deployment method because it is cheaper, simpler, more reliable, and lower power.

---

# 23. Power Monitoring

Do not require solar telemetry.

If an INA219/INA226 is available and easy to add:

- voltage
- current
- basic power information

can become a bonus feature.

Do not claim battery-runtime prediction unless actually modeled.

---

# 24. Suggested Repo Structure

Use one monorepo.

```text
fridgeguard/
├── AGENTS.md
├── README.md
├── FRIDGEGUARD_PLAN.md
│
├── firmware/
│   └── esp32/
│       ├── src/
│       └── platformio.ini
│
├── pi/
│   ├── main.py
│   ├── serial_reader.py
│   ├── sensors/
│   │   └── camera.py
│   ├── services/
│   │   ├── cloud_sync.py
│   │   ├── discord.py
│   │   ├── local_db.py
│   │   └── image_upload.py
│   ├── rules/
│   │   └── health.py
│   └── vision/
│       └── stock.py
│
├── web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── hardware/
│   ├── wiring.md
│   └── parts.md
│
└── docs/
    ├── architecture.md
    ├── demo.md
    └── deployment.md
```

Everything belongs in one repo because it is one product.

---

# 25. Example ESP32 → Pi Contract

```json
{
  "device_id": "fridge-sensor-01",
  "temperature_f": 38.2,
  "door_open": false,
  "uptime_ms": 124551
}
```

Send newline-delimited JSON over serial.

---

# 26. Example Pi → Cloud Contract

```json
{
  "device_id": "gnv-community-fridge-01",
  "timestamp": "2026-09-20T14:32:00-04:00",
  "temperature_f": 38.2,
  "door_open": false,
  "door_open_seconds": 0,
  "stock_level": "medium",
  "health": "good"
}
```

---

# 27. Recommended Build Order

1. ESP32 serial output
2. temperature + reed switch
3. Pi serial input
4. SQLite logging
5. health rules
6. Supabase sync
7. web dashboard
8. Discord webhook alerts
9. stale/offline handling
10. camera capture
11. stock estimation
12. polish + docs

---

# 28. Hackathon Timeline

Submission deadline: **5 PM**

## 10:00–10:30
- grab reed switch and useful hardware immediately
- wire sensors
- confirm serial
- confirm camera

## 10:30–11:30
- real sensor values
- Pi serial reader
- SQLite
- health logic

## 11:30–12:30
- Supabase
- dashboard live data

## 12:30–1:30
- Discord alerts
- recovery logic
- stale/offline state

## 1:30–2:30
- offline queue
- dashboard polish

## 2:30–3:30
- camera stock feature if core is solid

## 3:30–4:15
- demo setup
- reliability tests
- phone test
- screenshots/video

## 4:15–4:40
- README
- wiring
- parts list
- Devpost

## 4:40–5:00
- submit
- no new features

---

# 29. Demo Flow

1. Show normal dashboard state.
2. Open mock fridge door.
3. Show door timer.
4. Trigger Discord alert.
5. Warm temperature sensor.
6. Show high-temperature alert.
7. Explain deployed threshold is 40°F.
8. If reliable, disconnect internet and show local logging.
9. Reconnect and show sync.
10. If implemented, remove mock food and show stock estimate/image update.

---

# 30. Core Pitch

> The Gainesville Community Fridge will operate outdoors and off-grid with volunteers checking it only periodically. FridgeGuard is a low-cost monitoring system that watches temperature, door state, stock level, and device connectivity between visits. An ESP32 handles continuous sensing, while a Raspberry Pi prototype performs local storage, computer vision, cloud sync, and alerts. Readings are preserved locally if connectivity fails, synced to a remote dashboard when service is available, and Fridge Warriors receive actionable Discord alerts when something needs attention.

---

# 31. What Not to Build

Do not waste hackathon time on:

- login/accounts
- native mobile app
- full Discord bot
- object-by-object food recognition
- custom PCB
- complex ML
- SMS if Discord works
- solar forecasting without hardware
- excessive historical image storage
- advanced power optimization before MVP

---

# 32. Definition of Done

## Hardware
- [ ] ESP32 runs
- [ ] temperature sensor works
- [ ] reed switch works if obtained
- [ ] USB serial works
- [ ] camera works if included

## Edge Software
- [ ] Pi reads ESP32
- [ ] SQLite logging works
- [ ] health rules work
- [ ] cloud sync works
- [ ] offline queue works
- [ ] Discord webhook works
- [ ] rate limiting works
- [ ] recovery alerts work

## Cloud / Web
- [ ] Supabase tables work
- [ ] Storage works if camera enabled
- [ ] dashboard shows current state
- [ ] stale state becomes UNKNOWN
- [ ] latest image displays if implemented

## Documentation
- [ ] parts list
- [ ] cost estimate
- [ ] wiring notes
- [ ] setup instructions
- [ ] architecture
- [ ] limitations
- [ ] future low-power deployment plan

## Demo
- [ ] normal state
- [ ] door event
- [ ] temperature event
- [ ] Discord alert
- [ ] dashboard update
- [ ] offline/reconnect if reliable
- [ ] stock demo if implemented

---

# 33. Final Principle

FridgeGuard should not feel like a collection of sensors.

Every component supports one operational goal:

> **Help Fridge Warriors know when the Gainesville Community Fridge needs attention, even when nobody is there.**

A reliable temperature sensor, door sensor, local offline logging, remote dashboard, and actionable alerts are already a complete strong project.

Camera stock estimation and power telemetry are valuable additions only after the core system is solid.
