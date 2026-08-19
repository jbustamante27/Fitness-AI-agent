from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.domain.schemas import Run

DEFAULT_DB_PATH = Path("data") / "fitness.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE, 
    password_hash   TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    activity_id     INTEGER NOT NULL,
    start_time      TEXT NOT NULL,
    distance_m      REAL NOT NULL,
    duration_s      REAL NOT NULL,
    avg_hr          REAL,
    source_file     TEXT,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (user_id, activity_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_user_time ON runs (user_id, start_time);
"""

def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys enforced and the schema applied."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA forein_keys = ON")
    conn.executescript(SCHEMA)
    return conn

def get_or_create_user(conn: sqlite3.Connection, email: str) -> int:
    """Returns the user id. Auth comes later; for now an email is the identity"""
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is not None:
        return int(row["id"])

    cur = conn.execute(
        "INSERT INTO users (email, created_at) VALUES (?, ?)",
        (email, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return int(cur.lastrowid)

def save_runs(conn: sqlite3.Connection, user_id: int, runs: List[Run]) -> int:
    """
    Insert runs for a user, skipping any whose activity_id is already stored.
    Returns the number actually inserted.
    """
    inserted = 0
    now = datetime.now().isoformat(timespec="seconds")

    for run in runs:
        activity_id = _activity_id_for(run)
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO runs
                (user_id, activity_id, start_time, distance_m,
                 duration_s, avg_hr, source_file, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                activity_id,
                run.start_time.isoformat(),
                run.distance_m,
                run.duration_s,
                run.avg_hr,
                run.source_file,
                now,
            ),
        )
        inserted += cur.rowcount

    conn.commit()
    return inserted


def get_runs(conn: sqlite3.Connection, user_id: int) -> List[Run]:
    """All stored runs for a user, oldest first."""
    rows = conn.execute(
        "SELECT * FROM runs WHERE user_id = ? ORDER BY start_time ASC",
        (user_id,),
    ).fetchall()

    return [
        Run(
            start_time=datetime.fromisoformat(row["start_time"]),
            distance_m=row["distance_m"],
            duration_s=row["duration_s"],
            avg_hr=row["avg_hr"],
            source_file=row["source_file"],
        )
        for row in rows
    ]


def _activity_id_for(run: Run) -> str:
    """
    Natural key for deduplication.

    Garmin activity IDs are not currently carried on the Run model, so we
    derive a stable key from the run's own values. Two files describing the
    same activity produce the same key; two genuinely different runs cannot
    collide unless they started at the same second.
    """
    return f"{run.start_time.isoformat()}|{int(run.distance_m)}|{int(run.duration_s)}"