"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from src.models import Idea


def test_score_validation_rejects_zero(sample_idea: Idea) -> None:
    """Scores below 1 are rejected."""

    payload = sample_idea.model_dump()
    payload["novelty_score"] = 0
    with pytest.raises(ValidationError):
        Idea(**payload)


def test_score_validation_rejects_six(sample_idea: Idea) -> None:
    """Scores above 5 are rejected."""

    payload = sample_idea.model_dump()
    payload["risk_score"] = 6
    with pytest.raises(ValidationError):
        Idea(**payload)


def test_score_validation_accepts_one_to_five(sample_idea: Idea) -> None:
    """Scores from 1 through 5 are accepted."""

    for score in range(1, 6):
        payload = sample_idea.model_dump()
        payload["difficulty_score"] = score
        assert Idea(**payload).difficulty_score == score


def test_total_score_computation(sample_idea: Idea) -> None:
    """The weighted total score follows the Phase 1 formula."""

    assert sample_idea.total_score == 4.25


def test_idea_default_values(sample_idea: Idea) -> None:
    """Idea defaults match the backlog workflow."""

    assert sample_idea.status == "Backlog"
    assert sample_idea.script_status == "pending"
    assert sample_idea.voiceover_status == "pending"
    assert sample_idea.video_status == "pending"
    assert sample_idea.source == "generated"
