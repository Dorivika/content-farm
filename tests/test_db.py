"""Tests for SQLite persistence."""

import sqlite3
from pathlib import Path

from src import db
from src.models import Idea


def test_init_db_creates_tables(tmp_db: Path) -> None:
    """Database initialization creates expected tables."""

    with sqlite3.connect(tmp_db) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    table_names = {row[0] for row in rows}
    assert {"ideas", "scripts", "renders", "analytics_events"}.issubset(table_names)


def test_upsert_idea_and_get_idea_round_trip(tmp_db: Path, sample_idea: Idea) -> None:
    """An upserted idea can be loaded back as a model."""

    db.upsert_idea(sample_idea)
    loaded = db.get_idea(sample_idea.idea_id)
    assert loaded is not None
    assert loaded.idea_id == sample_idea.idea_id
    assert loaded.title == sample_idea.title
    assert loaded.total_score == sample_idea.total_score


def test_list_ideas_by_status(tmp_db: Path, sample_idea: Idea) -> None:
    """Ideas can be listed by primary status."""

    db.upsert_idea(sample_idea)
    results = db.list_ideas_by_status("Backlog")
    assert [idea.idea_id for idea in results] == [sample_idea.idea_id]


def test_mark_status(tmp_db: Path, sample_idea: Idea) -> None:
    """Allowed status fields can be updated."""

    db.upsert_idea(sample_idea)
    db.mark_status(sample_idea.idea_id, "status", "Approved")
    loaded = db.get_idea(sample_idea.idea_id)
    assert loaded is not None
    assert loaded.status == "Approved"
