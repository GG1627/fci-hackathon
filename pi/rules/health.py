from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


HealthLevel = Literal["good", "warning", "critical", "unknown"]


@dataclass(frozen=True)
class HealthResult:
    level: HealthLevel
    conditions: tuple[str, ...]
    title: str
    message: str


def parse_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def evaluate_health(
    reading,
    *,
    now: datetime,
    safe_temp_max_f: float,
    stale_after_seconds: float,
    door_open_since: str | None,
    door_open_alert_seconds: float,
) -> HealthResult:
    if reading is None:
        return HealthResult(
            level="unknown",
            conditions=("NO_DATA",),
            title="Community Chill has no sensor data",
            message="No ESP32 readings are available. Check the sensor connection.",
        )

    reading_time = parse_timestamp(reading["timestamp"])
    age_seconds = max(0.0, (now - reading_time).total_seconds())
    if age_seconds > stale_after_seconds:
        return HealthResult(
            level="unknown",
            conditions=("DEVICE_OFFLINE",),
            title="Community Chill sensor data is stale",
            message=(
                f"The latest ESP32 reading is {age_seconds:.0f} seconds old. "
                "Current fridge status is unknown."
            ),
        )

    temperature_f = float(reading["temperature_f"])
    door_open = bool(reading["door_open"])
    temperature_high = temperature_f > safe_temp_max_f
    door_open_seconds = 0.0
    if door_open and door_open_since:
        door_open_seconds = max(
            0.0,
            (now - parse_timestamp(door_open_since)).total_seconds(),
        )
    door_open_too_long = door_open and door_open_seconds >= door_open_alert_seconds

    if temperature_high and door_open_too_long:
        return HealthResult(
            level="critical",
            conditions=("TEMP_HIGH", "DOOR_OPEN_TOO_LONG"),
            title="High temperature and door left open",
            message=(
                f"Temperature is {temperature_f:.1f} F and the door has been open "
                f"for {door_open_seconds:.0f} seconds. Check that the fridge is closed."
            ),
        )
    if temperature_high:
        return HealthResult(
            level="critical",
            conditions=("TEMP_HIGH",),
            title="Fridge temperature is high",
            message=(
                f"Temperature is {temperature_f:.1f} F, above the configured "
                f"{safe_temp_max_f:.1f} F limit. The door is "
                f"{'open' if door_open else 'closed'}."
            ),
        )
    if door_open_too_long:
        return HealthResult(
            level="warning",
            conditions=("DOOR_OPEN_TOO_LONG",),
            title="Fridge door has been left open",
            message=f"The door has been open for {door_open_seconds:.0f} seconds.",
        )

    return HealthResult(
        level="good",
        conditions=(),
        title="Community Chill is healthy",
        message=(
            f"Temperature is {temperature_f:.1f} F and the door is "
            f"{'open' if door_open else 'closed'}."
        ),
    )
