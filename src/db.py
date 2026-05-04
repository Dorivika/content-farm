"""SQLite persistence for ideas, scripts, renders, and analytics."""

import json
import sqlite3
from pathlib import Path

from src.models import AnalyticsEvent, Idea, Script

DB_PATH = Path("data") / "content.db"

IDEA_FIELDS = [
    "idea_id",
    "date_added",
    "source",
    "source_url",
    "content_pillar",
    "target_viewer",
    "viewer_pain",
    "title",
    "hook",
    "script_outline",
    "suggested_visuals",
    "tools_needed",
    "monetization_angle",
    "CTA",
    "platform_primary",
    "platform_secondary",
    "ideal_length_seconds",
    "difficulty_score",
    "novelty_score",
    "monetization_score",
    "production_speed_score",
    "risk_score",
    "total_score",
    "status",
    "assigned_to",
    "due_date",
    "script_status",
    "voiceover_status",
    "video_status",
    "notes",
]
STATUS_FIELDS = {"status", "script_status", "voiceover_status", "video_status"}


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection using row dictionaries."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create local database tables when they do not exist."""

    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                idea_id TEXT PRIMARY KEY,
                date_added TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT NOT NULL,
                content_pillar TEXT NOT NULL,
                target_viewer TEXT NOT NULL,
                viewer_pain TEXT NOT NULL,
                title TEXT NOT NULL,
                hook TEXT NOT NULL,
                script_outline TEXT NOT NULL,
                suggested_visuals TEXT NOT NULL,
                tools_needed TEXT NOT NULL,
                monetization_angle TEXT NOT NULL,
                CTA TEXT NOT NULL,
                platform_primary TEXT NOT NULL,
                platform_secondary TEXT NOT NULL,
                ideal_length_seconds INTEGER NOT NULL,
                difficulty_score INTEGER NOT NULL,
                novelty_score INTEGER NOT NULL,
                monetization_score INTEGER NOT NULL,
                production_speed_score INTEGER NOT NULL,
                risk_score INTEGER NOT NULL,
                total_score REAL NOT NULL,
                status TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                due_date TEXT NOT NULL,
                script_status TEXT NOT NULL,
                voiceover_status TEXT NOT NULL,
                video_status TEXT NOT NULL,
                notes TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scripts (
                idea_id TEXT PRIMARY KEY,
                script_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES ideas (idea_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS renders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id TEXT NOT NULL,
                output_path TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES ideas (idea_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )


def upsert_idea(idea: Idea) -> None:
    """Insert or update an idea by idea_id."""

    payload = idea.model_dump(mode="json")
    values = [payload[field] for field in IDEA_FIELDS]
    placeholders = ", ".join(["?"] * len(IDEA_FIELDS))
    columns = ", ".join(IDEA_FIELDS)
    updates = ", ".join([field + " = excluded." + field for field in IDEA_FIELDS[1:]])
    sql = (
        "INSERT INTO ideas (" + columns + ") VALUES (" + placeholders + ") "
        "ON CONFLICT(idea_id) DO UPDATE SET " + updates
    )
    with _connect() as connection:
        connection.execute(sql, values)


def get_idea(idea_id: str) -> Idea | None:
    """Return one idea by ID, or None when missing."""

    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM ideas WHERE idea_id = ?",
            (idea_id,),
        ).fetchone()
    return Idea(**dict(row)) if row else None


def list_ideas_by_status(status: str) -> list[Idea]:
    """Return all ideas with a matching primary status."""

    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM ideas WHERE status = ? ORDER BY date_added, idea_id",
            (status,),
        ).fetchall()
    return [Idea(**dict(row)) for row in rows]


def save_script(idea_id: str, script: Script) -> None:
    """Store a script JSON payload for one idea."""

    script_json = json.dumps(script.model_dump(mode="json"), ensure_ascii=True)
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO scripts (idea_id, script_json)
            VALUES (?, ?)
            ON CONFLICT(idea_id) DO UPDATE SET
                script_json = excluded.script_json,
                created_at = CURRENT_TIMESTAMP
            """,
            (idea_id, script_json),
        )


def get_script(idea_id: str) -> Script | None:
    """Return a stored script by idea ID, or None when missing."""

    with _connect() as connection:
        row = connection.execute(
            "SELECT script_json FROM scripts WHERE idea_id = ?",
            (idea_id,),
        ).fetchone()
    return Script(**json.loads(row["script_json"])) if row else None


def mark_status(idea_id: str, field: str, value: str) -> None:
    """Update one allowed status field on an idea."""

    if field not in STATUS_FIELDS:
        raise ValueError(f"field must be one of {sorted(STATUS_FIELDS)}")
    sql = "UPDATE ideas SET " + field + " = ? WHERE idea_id = ?"
    with _connect() as connection:
        connection.execute(sql, (value, idea_id))


def insert_analytics_event(event: AnalyticsEvent) -> None:
    """Insert one local analytics event."""

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO analytics_events
                (idea_id, event_type, timestamp, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                event.idea_id,
                event.event_type,
                event.timestamp.isoformat(),
                json.dumps(event.payload, ensure_ascii=True),
            ),
        )
