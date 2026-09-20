import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rules.health import evaluate_health
from services.image_storage import ImageStorageService
from services.local_db import DEFAULT_DB_PATH, get_door_open_since, get_latest_readings
from services.supabase_api import load_supabase_config


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
STALE_AFTER_SECONDS = float(os.getenv("READING_STALE_AFTER_SECONDS", "15"))
SAFE_TEMP_MAX_F = float(os.getenv("SAFE_TEMP_MAX_F", "40"))
DOOR_OPEN_ALERT_SECONDS = float(os.getenv("DOOR_OPEN_ALERT_SECONDS", "300"))
DB_PATH = DEFAULT_DB_PATH


class Reading(BaseModel):
    id: int
    device_id: str
    timestamp: str
    temperature_f: float
    door_open: bool
    synced: bool


class StatusResponse(BaseModel):
    status: Literal["ok", "stale", "no_data"]
    age_seconds: float | None
    reading: Reading | None
    door_open_since: str | None
    safe_temp_max_f: float
    health_level: Literal["good", "warning", "critical", "unknown"]
    conditions: list[str]
    message: str


class ImageItem(BaseModel):
    name: str
    timestamp: str
    url: str


class ImagesResponse(BaseModel):
    latest: ImageItem | None
    history: list[ImageItem]


app = FastAPI(title="Community Chill Local API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def serialize_reading(row) -> Reading:
    return Reading(
        id=row["id"],
        device_id=row["device_id"],
        timestamp=row["timestamp"],
        temperature_f=row["temperature_f"],
        door_open=bool(row["door_open"]),
        synced=bool(row["synced"]),
    )


@lru_cache(maxsize=1)
def get_image_storage() -> ImageStorageService:
    supabase_url, secret_key = load_supabase_config()
    return ImageStorageService(supabase_url, secret_key)


def serialize_image(storage: ImageStorageService, name: str) -> ImageItem:
    captured_at = datetime.strptime(name, "fridge-%Y%m%dT%H%M%SZ.jpg").replace(
        tzinfo=timezone.utc
    )
    return ImageItem(
        name=name,
        timestamp=captured_at.isoformat().replace("+00:00", "Z"),
        url=storage.get_public_url(name),
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def current_status() -> StatusResponse:
    rows = get_latest_readings(limit=1, db_path=DB_PATH)
    if not rows:
        health_result = evaluate_health(
            None,
            now=datetime.now(timezone.utc),
            safe_temp_max_f=SAFE_TEMP_MAX_F,
            stale_after_seconds=STALE_AFTER_SECONDS,
            door_open_since=None,
            door_open_alert_seconds=DOOR_OPEN_ALERT_SECONDS,
        )
        return StatusResponse(
            status="no_data",
            age_seconds=None,
            reading=None,
            door_open_since=None,
            safe_temp_max_f=SAFE_TEMP_MAX_F,
            health_level=health_result.level,
            conditions=list(health_result.conditions),
            message=health_result.message,
        )

    reading = serialize_reading(rows[0])
    timestamp = datetime.fromisoformat(reading.timestamp.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age_seconds = max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    status = "stale" if age_seconds > STALE_AFTER_SECONDS else "ok"
    door_open_since = get_door_open_since(DB_PATH)
    health_result = evaluate_health(
        rows[0],
        now=datetime.now(timezone.utc),
        safe_temp_max_f=SAFE_TEMP_MAX_F,
        stale_after_seconds=STALE_AFTER_SECONDS,
        door_open_since=door_open_since,
        door_open_alert_seconds=DOOR_OPEN_ALERT_SECONDS,
    )

    return StatusResponse(
        status=status,
        age_seconds=round(age_seconds, 1),
        reading=reading,
        door_open_since=door_open_since,
        safe_temp_max_f=SAFE_TEMP_MAX_F,
        health_level=health_result.level,
        conditions=list(health_result.conditions),
        message=health_result.message,
    )


@app.get("/api/readings", response_model=list[Reading])
def recent_readings(limit: int = Query(default=50, ge=1, le=500)) -> list[Reading]:
    rows = get_latest_readings(limit=limit, db_path=DB_PATH)
    return [serialize_reading(row) for row in rows]


@app.get("/api/images", response_model=ImagesResponse)
def recent_images() -> ImagesResponse:
    try:
        storage = get_image_storage()
        images = [
            serialize_image(storage, name)
            for name in reversed(storage.list_image_names())
        ]
    except Exception as error:
        print(f"Could not load Supabase images: {error}", flush=True)
        raise HTTPException(
            status_code=503,
            detail="Image storage is temporarily unavailable.",
        ) from error

    return ImagesResponse(
        latest=images[0] if images else None,
        history=images[1:],
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
