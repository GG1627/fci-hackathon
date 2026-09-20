import argparse
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from rules.health import HealthResult, evaluate_health
from services.discord_webhook import DiscordWebhookError, send_discord_alert
from services.image_storage import ImageStorageService
from services.local_db import get_door_open_since, get_latest_readings
from services.supabase_api import load_supabase_config


ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AlertSettings:
    webhook_url: str
    safe_temp_max_f: float
    door_open_alert_seconds: float
    reading_stale_after_seconds: float
    cooldown_seconds: float
    poll_interval_seconds: float
    startup_grace_seconds: float


class AlertTracker:
    def __init__(self, cooldown_seconds: float) -> None:
        self.cooldown_seconds = cooldown_seconds
        self.active_conditions: tuple[str, ...] = ()
        self.last_sent_at: float | None = None

    def action_for(self, result: HealthResult, now: float) -> str | None:
        if result.conditions:
            changed = result.conditions != self.active_conditions
            cooldown_elapsed = (
                self.last_sent_at is None
                or now - self.last_sent_at >= self.cooldown_seconds
            )
            return "alert" if changed or cooldown_elapsed else None
        return "recovery" if self.active_conditions else None

    def mark_sent(self, result: HealthResult, now: float) -> None:
        self.active_conditions = result.conditions
        self.last_sent_at = now


def env_float(name: str, default: float, minimum: float = 0.0) -> float:
    value = os.getenv(name, str(default))
    try:
        parsed = float(value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a number.") from error
    if parsed < minimum:
        raise RuntimeError(f"{name} must be at least {minimum}.")
    return parsed


def load_alert_settings() -> AlertSettings:
    load_dotenv(ROOT_DIR / ".env")
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL in the root .env file.")
    return AlertSettings(
        webhook_url=webhook_url,
        safe_temp_max_f=env_float("SAFE_TEMP_MAX_F", 40.0),
        door_open_alert_seconds=env_float("DOOR_OPEN_ALERT_SECONDS", 300.0),
        reading_stale_after_seconds=env_float(
            "READING_STALE_AFTER_SECONDS", 15.0
        ),
        cooldown_seconds=env_float("ALERT_COOLDOWN_SECONDS", 1800.0),
        poll_interval_seconds=env_float("ALERT_POLL_INTERVAL_SECONDS", 2.0, 0.1),
        startup_grace_seconds=env_float("ALERT_STARTUP_GRACE_SECONDS", 15.0),
    )


def optional_image_storage() -> ImageStorageService | None:
    try:
        supabase_url, secret_key = load_supabase_config()
        return ImageStorageService(supabase_url, secret_key)
    except Exception as error:
        print(f"Latest image unavailable for Discord alerts: {error}", flush=True)
        return None


def latest_image_url(storage: ImageStorageService | None) -> str | None:
    if storage is None:
        return None
    try:
        names = storage.list_image_names()
        return storage.get_public_url(names[-1]) if names else None
    except Exception as error:
        print(f"Latest image unavailable for Discord alerts: {error}", flush=True)
        return None


def recovery_result(current: HealthResult) -> HealthResult:
    return HealthResult(
        level="good",
        conditions=(),
        title="Community Chill recovered",
        message=current.message,
    )


def monitor(settings: AlertSettings) -> None:
    tracker = AlertTracker(settings.cooldown_seconds)
    storage = optional_image_storage()

    if settings.startup_grace_seconds:
        print(
            f"Alert monitor waiting {settings.startup_grace_seconds:g} seconds "
            "for sensor data...",
            flush=True,
        )
        time.sleep(settings.startup_grace_seconds)

    print("Discord alert monitor running. Press Ctrl+C to stop.", flush=True)
    while True:
        rows = get_latest_readings(limit=1)
        reading = rows[0] if rows else None
        result = evaluate_health(
            reading,
            now=datetime.now(timezone.utc),
            safe_temp_max_f=settings.safe_temp_max_f,
            stale_after_seconds=settings.reading_stale_after_seconds,
            door_open_since=get_door_open_since(),
            door_open_alert_seconds=settings.door_open_alert_seconds,
        )
        action = tracker.action_for(result, time.monotonic())
        if action:
            notification = recovery_result(result) if action == "recovery" else result
            try:
                send_discord_alert(
                    settings.webhook_url,
                    notification,
                    image_url=latest_image_url(storage),
                )
                tracker.mark_sent(result, time.monotonic())
                print(f"Discord {action} sent: {notification.title}", flush=True)
            except DiscordWebhookError as error:
                print(error, flush=True)

        time.sleep(settings.poll_interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor Community Chill health alerts.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send one test webhook message immediately and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        settings = load_alert_settings()
    except RuntimeError as error:
        raise SystemExit(error) from error

    if args.test:
        test_result = HealthResult(
            level="good",
            conditions=(),
            title="Community Chill test alert",
            message="Discord webhook connectivity is working.",
        )
        try:
            send_discord_alert(
                settings.webhook_url,
                test_result,
                image_url=latest_image_url(optional_image_storage()),
            )
        except DiscordWebhookError as error:
            raise SystemExit(error) from error
        print("Discord test alert sent.")
        return

    try:
        monitor(settings)
    except KeyboardInterrupt:
        print("\nDiscord alert monitor stopped.")


if __name__ == "__main__":
    main()
