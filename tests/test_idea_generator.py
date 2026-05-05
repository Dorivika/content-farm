"""Tests for Gemini idea generation fallbacks."""

from src.idea_generator import generate_ideas
from src.idea_parser import parse_ideas
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


def test_deep_research_markdown_tables_parse() -> None:
    """Deep Research concept-table output is parsed as ideas."""

    raw = """
### Concept 1: The WhatsApp Order Engine

| Parameter | Strategic Detail |
| :--- | :--- |
| **title** | Automate WhatsApp Orders For Indian Businesses |
| **content_pillar** | india_tech |
| **target_viewer** | Indian small business operator |
| **viewer_pain** | Losing hours manually typing WhatsApp orders into Excel |
| **hook** | WhatsApp orders are killing your productivity. |
| **script_outline** | Show WhatsApp orders becoming Google Sheet rows through Make. Keep human review for exceptions. |
| **suggested_visuals** | Split screen of WhatsApp and Google Sheets. |
| **tools_needed** | WhatsApp Business API, Make.com, Google Sheets |
| **monetization_angle** | Make affiliate link or consulting services. |
| **CTA** | Save this workflow for later. |
| **platform_primary** | instagram_reels |
| **platform_secondary** | youtube_shorts |
| **ideal_length_seconds** | 45 |
| **difficulty_score** | 3 |
| **novelty_score** | 3 |
| **monetization_score** | 5 |
| **production_speed_score** | 3 |
| **risk_score** | 1 |
| **source** | gemini_generated |
| **source_url** | |
| **notes** | Localized to Indian WhatsApp commerce. |
"""
    ideas = parse_ideas(raw)
    assert len(ideas) == 1
    assert ideas[0].title == "Automate WhatsApp Orders For Indian Businesses"
    assert ideas[0].content_pillar == "india_tech"
