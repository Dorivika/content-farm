"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from src import db
from src.models import Idea


@pytest.fixture
def tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary SQLite database for tests."""

    db_path = tmp_path / "content.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    return db_path


@pytest.fixture
def sample_idea() -> Idea:
    """Return a valid idea model for tests."""

    return Idea(
        content_pillar="manual_to_ai",
        target_viewer="solo founders",
        viewer_pain="manual follow-up notes take too long",
        title="Turn meeting notes into follow-up emails",
        hook="Stop rewriting follow-up emails after every sales call.",
        script_outline="Show notes, prompt, draft, and approval.",
        suggested_visuals="Calendar, notes app, email draft.",
        tools_needed="AI assistant, Gmail draft, spreadsheet",
        monetization_angle="Sell a workflow setup template.",
        difficulty_score=2,
        novelty_score=4,
        monetization_score=4,
        production_speed_score=5,
        risk_score=2,
    )
