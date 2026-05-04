"""Tests for script generation fallbacks."""

from src.models import Idea, Script
from src.script_generator import generate_script
from src.settings import settings


def test_offline_fallback_generates_valid_script(monkeypatch, sample_idea: Idea) -> None:
    """Offline fallback generates a valid Script from a sample Idea."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    script = generate_script(sample_idea)
    assert isinstance(script, Script)
    assert script.idea_id == sample_idea.idea_id
    assert len(script.steps) == 3


def test_full_text_is_non_empty(monkeypatch, sample_idea: Idea) -> None:
    """Script full_text computed property returns content."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert generate_script(sample_idea).full_text


def test_word_count_is_reasonable(monkeypatch, sample_idea: Idea) -> None:
    """Offline fallback script has a useful amount of text."""

    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert generate_script(sample_idea).word_count > 20
