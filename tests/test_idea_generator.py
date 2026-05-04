"""Tests for deterministic seed idea generation."""

from src.idea_generator import generate_seed_ideas


def test_generate_seed_ideas_returns_requested_count() -> None:
    """Seed generation returns the requested number of valid ideas."""

    ideas = generate_seed_ideas(3)
    assert len(ideas) == 3
    assert all(idea.status == "Backlog" for idea in ideas)
