"""Tests for script generation helpers."""

from src.models import Idea
from src.script_generator import build_script_from_idea


def test_build_script_from_idea(sample_idea: Idea) -> None:
    """Rule-based script generation preserves idea identity and structure."""

    script = build_script_from_idea(sample_idea)
    assert script.idea_id == sample_idea.idea_id
    assert len(script.steps) == 3
    assert script.word_count > 0
