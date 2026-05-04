"""Tests for Gemini idea generation fallbacks."""

from src.idea_generator import generate_ideas
from src.models import Idea
from src.settings import settings


def test_offline_fallback_returns_five_ideas(monkeypatch) -> None:
    """Offline fallback returns exactly five ideas when no API key exists."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert len(generate_ideas()) == 5


def test_fallback_ideas_pass_pydantic_validation(monkeypatch) -> None:
    """All fallback ideas are valid Pydantic Idea instances."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    ideas = generate_ideas()
    assert all(isinstance(idea, Idea) for idea in ideas)


def test_fallback_ideas_have_unique_ids(monkeypatch) -> None:
    """All fallback ideas receive unique idea IDs."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    ids = [idea.idea_id for idea in generate_ideas()]
    assert len(ids) == len(set(ids))


def test_fallback_content_pillars_are_varied(monkeypatch) -> None:
    """Offline fallback ideas cover multiple content pillars."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    pillars = {idea.content_pillar for idea in generate_ideas()}
    assert len(pillars) > 1
