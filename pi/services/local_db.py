import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "fridgeguard.db"


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature_f REAL NOT NULL,
                door_open INTEGER NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def save_reading(
    device_id: str,
    temperature_f: float,
    door_open: bool,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    initialize_database(db_path)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO readings
                (device_id, timestamp, temperature_f, door_open, synced)
            VALUES (?, ?, ?, ?, 0)
            """,
            (device_id, timestamp, temperature_f, int(door_open)),
        )


def get_latest_readings(
    limit: int = 10, db_path: Path = DEFAULT_DB_PATH
) -> list[sqlite3.Row]:
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT id, device_id, timestamp, temperature_f, door_open, synced
            FROM readings
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_unsynced_readings(
    limit: int = 100, db_path: Path = DEFAULT_DB_PATH
) -> list[sqlite3.Row]:
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT id, device_id, timestamp, temperature_f, door_open
            FROM readings
            WHERE synced = 0
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def mark_readings_synced(
    reading_ids: list[int], db_path: Path = DEFAULT_DB_PATH
) -> None:
    if not reading_ids:
        return

    placeholders = ", ".join("?" for _ in reading_ids)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"UPDATE readings SET synced = 1 WHERE id IN ({placeholders})",
            reading_ids,
        )
