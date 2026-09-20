from collections.abc import Callable
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from rules.health import HealthResult


COLORS = {
    "good": 0x2ECC71,
    "warning": 0xF1C40F,
    "critical": 0xE74C3C,
    "unknown": 0x95A5A6,
}


class DiscordWebhookError(RuntimeError):
    pass


def normalize_webhook_url(webhook_url: str) -> str:
    webhook_url = webhook_url.strip()
    parsed = urlparse(webhook_url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "discord.com",
        "discordapp.com",
    }:
        raise DiscordWebhookError("DISCORD_WEBHOOK_URL is not a Discord HTTPS URL.")
    if not parsed.path.startswith("/api/webhooks/"):
        raise DiscordWebhookError("DISCORD_WEBHOOK_URL has an invalid webhook path.")
    return webhook_url.replace("https://discordapp.com/", "https://discord.com/", 1)


def send_discord_alert(
    webhook_url: str,
    result: HealthResult,
    *,
    image_url: str | None = None,
    post: Callable = requests.post,
) -> None:
    embed = {
        "title": result.title,
        "description": result.message,
        "color": COLORS[result.level],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Community Chill"},
    }
    if image_url:
        embed["image"] = {"url": image_url}

    try:
        response = post(
            normalize_webhook_url(webhook_url),
            params={"wait": "true"},
            json={
                "username": "Community Chill",
                "allowed_mentions": {"parse": []},
                "embeds": [embed],
            },
            timeout=10,
        )
        response.raise_for_status()
    except (requests.RequestException, DiscordWebhookError) as error:
        raise DiscordWebhookError(f"Discord webhook failed: {error}") from error
