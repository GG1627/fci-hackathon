from datetime import datetime, timezone
from typing import Literal

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.local_db import DEFAULT_DB_PATH, get_latest_readings


STALE_AFTER_SECONDS = 10
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


app = FastAPI(title="FridgeGuard Local API", version="1.0.0")
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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def current_status() -> StatusResponse:
    rows = get_latest_readings(limit=1, db_path=DB_PATH)
    if not rows:
        return StatusResponse(status="no_data", age_seconds=None, reading=None)

    reading = serialize_reading(rows[0])
    timestamp = datetime.fromisoformat(reading.timestamp.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age_seconds = max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    status = "stale" if age_seconds > STALE_AFTER_SECONDS else "ok"

    return StatusResponse(
        status=status,
        age_seconds=round(age_seconds, 1),
        reading=reading,
    )


@app.get("/api/readings", response_model=list[Reading])
def recent_readings(limit: int = Query(default=50, ge=1, le=500)) -> list[Reading]:
    rows = get_latest_readings(limit=limit, db_path=DB_PATH)
    return [serialize_reading(row) for row in rows]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
