# Health rules and Discord alerts

Discord alerts run as a separate process that reads the latest SQLite data. It
does not open the ESP32 serial port and cannot interrupt local logging.

Configure these root `.env` values:

```text
DISCORD_WEBHOOK_URL=
SAFE_TEMP_MAX_F=40
DOOR_OPEN_ALERT_SECONDS=300
READING_STALE_AFTER_SECONDS=15
ALERT_COOLDOWN_SECONDS=1800
ALERT_TRIGGER_AFTER_SECONDS=3
ALERT_POLL_INTERVAL_SECONDS=2
ALERT_STARTUP_GRACE_SECONDS=15
```

Rules cover:

- temperature above the configured limit
- door open longer than the configured duration
- stale or missing ESP32 readings
- cause-aware high-temperature plus open-door alerts
- a recovery message when all active problems clear
- a configurable confirmation window so brief sensor spikes do not alert

New or changed alert conditions must remain active for
`ALERT_TRIGGER_AFTER_SECONDS` before they are sent. The same active condition
is then sent at most once per cooldown. Recovery messages send immediately.

## Send a safe test message

After putting a valid webhook URL in `.env`:

```bash
python3 pi/alert_monitor.py --test
```

## Demo settings

For a room-temperature demo, choose a threshold slightly above the current
room reading to avoid an immediate temperature alert. To demonstrate quickly,
temporarily use a short door duration and cooldown, for example:

```text
SAFE_TEMP_MAX_F=76
DOOR_OPEN_ALERT_SECONDS=10
ALERT_COOLDOWN_SECONDS=60
ALERT_TRIGGER_AFTER_SECONDS=3
ALERT_POLL_INTERVAL_SECONDS=1
```

Restore the production-safe values before using FridgeGuard in a refrigerator.
