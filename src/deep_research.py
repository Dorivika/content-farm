"""Gemini Deep Research client using the Interactions API."""

import time
from typing import Any

from src.settings import settings


def _interaction_text(interaction: Any) -> str:
    """Extract final text from a completed interaction."""

    outputs = getattr(interaction, "outputs", []) or []
    if not outputs:
        return ""
    text = getattr(outputs[-1], "text", "")
    return text if isinstance(text, str) else str(text)


def run_deep_research(prompt: str) -> str:
    """Run Deep Research in the background and return the final response text."""

    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    kwargs = {
        "input": prompt,
        "agent": settings.gemini_deep_research_agent,
        "agent_config": {
            "type": "deep-research",
            "thinking_summaries": "none",
            "visualization": "off",
            "collaborative_planning": False,
        },
        "background": True,
    }
    try:
        interaction = client.interactions.create(**kwargs, store=True)
    except TypeError:
        interaction = client.interactions.create(**kwargs)

    deadline = time.monotonic() + settings.deep_research_timeout_seconds
    while time.monotonic() < deadline:
        interaction = client.interactions.get(interaction.id)
        if interaction.status == "completed":
            return _interaction_text(interaction)
        if interaction.status == "failed":
            raise RuntimeError(f"Deep Research failed: {interaction.error}")
        time.sleep(settings.deep_research_poll_seconds)
    raise TimeoutError("Deep Research timed out before completion.")
