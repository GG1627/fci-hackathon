import argparse
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "pi"))

import api  # noqa: E402
import main as pi_main  # noqa: E402
from alert_monitor import AlertTracker, recovery_result  # noqa: E402
from rules.health import HealthResult, evaluate_health  # noqa: E402
from services.discord_webhook import send_discord_alert  # noqa: E402


NOW = datetime(2026, 9, 20, 20, 0, tzinfo=timezone.utc)


def reading(
    temperature_f: float = 38.0,
    door_open: bool = False,
    timestamp: datetime = NOW,
) -> dict:
    return {
        "timestamp": timestamp.isoformat(),
        "temperature_f": temperature_f,
        "door_open": int(door_open),
    }


class HealthRuleTests(unittest.TestCase):
    def test_combines_high_temperature_and_open_door(self):
        result = evaluate_health(
            reading(45.0, True),
            now=NOW,
            safe_temp_max_f=40.0,
            stale_after_seconds=15,
            door_open_since=(NOW - timedelta(minutes=6)).isoformat(),
            door_open_alert_seconds=300,
        )

        self.assertEqual(result.level, "critical")
        self.assertEqual(result.conditions, ("TEMP_HIGH", "DOOR_OPEN_TOO_LONG"))

    def test_marks_old_reading_unknown(self):
        result = evaluate_health(
            reading(timestamp=NOW - timedelta(seconds=20)),
            now=NOW,
            safe_temp_max_f=40.0,
            stale_after_seconds=15,
            door_open_since=None,
            door_open_alert_seconds=300,
        )

        self.assertEqual(result.level, "unknown")
        self.assertEqual(result.conditions, ("DEVICE_OFFLINE",))

    def test_healthy_reading_has_no_conditions(self):
        result = evaluate_health(
            reading(),
            now=NOW,
            safe_temp_max_f=40.0,
            stale_after_seconds=15,
            door_open_since=None,
            door_open_alert_seconds=300,
        )

        self.assertEqual(result.level, "good")
        self.assertEqual(result.conditions, ())


class AlertTrackerTests(unittest.TestCase):
    def test_alert_cooldown_and_recovery(self):
        problem = HealthResult("critical", ("TEMP_HIGH",), "High", "Too warm")
        healthy = HealthResult("good", (), "Healthy", "Recovered")
        tracker = AlertTracker(cooldown_seconds=60)

        self.assertEqual(tracker.action_for(problem, 100), "alert")
        tracker.mark_sent(problem, 100)
        self.assertIsNone(tracker.action_for(problem, 120))
        self.assertEqual(tracker.action_for(problem, 161), "alert")
        self.assertEqual(tracker.action_for(healthy, 120), "recovery")
        self.assertEqual(recovery_result(healthy).title, "Community Chill recovered")

    def test_problem_must_persist_before_first_alert(self):
        problem = HealthResult("critical", ("TEMP_HIGH",), "High", "Too warm")
        healthy = HealthResult("good", (), "Healthy", "Recovered")
        tracker = AlertTracker(cooldown_seconds=60, trigger_after_seconds=3)

        self.assertIsNone(tracker.action_for(problem, 100))
        self.assertIsNone(tracker.action_for(problem, 102.9))
        self.assertEqual(tracker.action_for(problem, 103), "alert")

        tracker.mark_sent(problem, 103)
        self.assertIsNone(tracker.action_for(problem, 104))
        self.assertEqual(tracker.action_for(healthy, 104), "recovery")

    def test_brief_problem_clears_without_alert_or_recovery(self):
        problem = HealthResult("critical", ("TEMP_HIGH",), "High", "Too warm")
        healthy = HealthResult("good", (), "Healthy", "Recovered")
        tracker = AlertTracker(cooldown_seconds=60, trigger_after_seconds=3)

        self.assertIsNone(tracker.action_for(problem, 100))
        self.assertIsNone(tracker.action_for(healthy, 101))
        self.assertIsNone(tracker.action_for(problem, 102))
        self.assertIsNone(tracker.action_for(problem, 104))
        self.assertEqual(tracker.action_for(problem, 105), "alert")


class DiscordWebhookTests(unittest.TestCase):
    def test_sends_embed_without_mentions_and_normalizes_legacy_host(self):
        calls = []

        class Response:
            def raise_for_status(self):
                return None

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            return Response()

        result = HealthResult("warning", ("DOOR_OPEN_TOO_LONG",), "Door", "Open")
        send_discord_alert(
            "https://discordapp.com/api/webhooks/123/token",
            result,
            image_url="https://example.test/fridge.jpg",
            post=fake_post,
        )

        url, kwargs = calls[0]
        self.assertTrue(url.startswith("https://discord.com/api/webhooks/"))
        self.assertEqual(kwargs["json"]["allowed_mentions"], {"parse": []})
        self.assertEqual(
            kwargs["json"]["embeds"][0]["image"]["url"],
            "https://example.test/fridge.jpg",
        )


class ImageApiTests(unittest.TestCase):
    def test_images_returns_latest_and_history(self):
        class Storage:
            def list_image_names(self):
                return [
                    "fridge-20260920T190000Z.jpg",
                    "fridge-20260920T191000Z.jpg",
                ]

            def get_public_url(self, name):
                return f"https://example.test/{name}"

        with patch.object(api, "get_image_storage", return_value=Storage()):
            response = api.recent_images()

        self.assertEqual(response.latest.name, "fridge-20260920T191000Z.jpg")
        self.assertEqual(len(response.history), 1)
        self.assertEqual(response.history[0].timestamp, "2026-09-20T19:00:00Z")

    def test_status_exposes_health_rules(self):
        current = datetime.now(timezone.utc).isoformat()
        row = {
            "id": 1,
            "device_id": "fridge-sensor-01",
            "timestamp": current,
            "temperature_f": 45.0,
            "door_open": 0,
            "synced": 0,
        }
        with patch.object(api, "SAFE_TEMP_MAX_F", 40.0), patch.object(
            api, "get_latest_readings", return_value=[row]
        ), patch.object(api, "get_door_open_since", return_value=None):
            response = api.current_status()

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.health_level, "critical")
        self.assertEqual(response.conditions, ["TEMP_HIGH"])
        self.assertIsNone(response.door_open_since)
        self.assertEqual(response.safe_temp_max_f, 40.0)


class LauncherTests(unittest.TestCase):
    def test_launcher_includes_all_services_when_configured(self):
        args = argparse.Namespace(
            camera_interval=30.0,
            no_camera=False,
            no_alerts=False,
        )
        with patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "configured"}):
            commands = pi_main.service_commands(args)

        names = [name for name, _ in commands]
        self.assertEqual(
            names,
            ["serial logger", "local API", "camera pipeline", "Discord alerts"],
        )
        camera_command = dict(commands)["camera pipeline"]
        self.assertEqual(camera_command[-2:], ["--interval", "30.0"])


if __name__ == "__main__":
    unittest.main()
