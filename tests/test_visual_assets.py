"""Tests for optional visual asset fallbacks."""

from pathlib import Path

from src import broll, captions, visual_generator
from src.models import Idea, Script
from src.settings import settings


def test_broll_fallback_without_api_key(monkeypatch) -> None:
    """Pexels b-roll fetch returns empty when no API key is configured."""

    monkeypatch.setattr(settings, "offline_mode", False)
    monkeypatch.setattr(settings, "pexels_api_key", "")
    assert broll.fetch_broll(["automation"], 2) == []


def test_visual_generator_offline_fallback(monkeypatch, sample_idea: Idea) -> None:
    """Gemini step image generation returns empty in offline mode."""

    monkeypatch.setattr(settings, "offline_mode", True)
    script = Script(
        idea_id=sample_idea.idea_id,
        hook=sample_idea.hook,
        problem="Problem",
        old_way="Old way",
        steps=["Step one", "Step two", "Step three"],
        caveat="Caveat",
        cta="CTA",
    )
    assert visual_generator.generate_step_images(sample_idea, script) == []


def test_caption_overlay_offline_fallback(monkeypatch, tmp_path: Path) -> None:
    """pycaps overlay generation is skipped in offline mode."""

    monkeypatch.setattr(settings, "offline_mode", True)
    assert captions.generate_caption_overlay(tmp_path / "a.mp3", tmp_path / "out.mov") is None
