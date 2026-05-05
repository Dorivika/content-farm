"""Gemini-backed script generation with deterministic offline fallback."""

import json
import re
from typing import Any

from pydantic import ValidationError

from src.logger import get_logger
from src.models import Idea, Script
from src.prompts import render_template
from src.settings import settings

logger = get_logger(__name__)
GEMINI_MODEL = "gemini-2.0-flash"


def _extract_json(text: str) -> str:
    """Extract a JSON payload from a model response."""

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    return fence.group(1).strip() if fence else cleaned


def _response_text(response: Any) -> str:
    """Return text from a Gemini response object."""

    text = getattr(response, "text", "")
    return text if isinstance(text, str) else str(text)


def _call_gemini(prompt: str) -> str:
    """Call Gemini and return the raw response text."""

    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return _response_text(response)


def _fallback_steps(idea: Idea) -> list[str]:
    """Build three workflow steps from an idea outline."""

    outline = idea.script_outline.rstrip(".")
    return [
        f"First, turn the task into a checklist: {outline}.",
        f"Second, use {idea.tools_needed} to draft the boring parts, not final decisions.",
        "Third, review the output, fix edge cases, and only then move it into your real workflow.",
    ]


def build_script_from_idea(idea: Idea) -> Script:
    """Create a structured script draft from an idea without external calls."""

    return Script(
        idea_id=idea.idea_id,
        hook=idea.hook,
        problem=f"Most {idea.target_viewer}s waste time on {idea.viewer_pain}.",
        old_way="The old way? Manual work, spreadsheets, or expensive software.",
        steps=_fallback_steps(idea),
        caveat="This won't replace expert judgment, but it handles the boring parts.",
        cta=idea.CTA or "Follow for more workflows like this.",
    )


def _parse_script(idea: Idea, raw_text: str) -> Script | None:
    """Parse Gemini JSON into a validated Script model."""

    try:
        payload = json.loads(_extract_json(raw_text))
    except json.JSONDecodeError:
        logger.error("Failed to parse Gemini script JSON: %s", raw_text)
        return None
    if not isinstance(payload, dict):
        logger.error("Gemini script response was not a JSON object: %s", raw_text)
        return None
    try:
        script = Script(
            idea_id=idea.idea_id,
            hook=str(payload.get("hook", idea.hook)),
            problem=str(payload.get("problem", "")),
            old_way=str(payload.get("old_way", "")),
            steps=[
                str(payload.get("step_1", "")),
                str(payload.get("step_2", "")),
                str(payload.get("step_3", "")),
            ],
            caveat=str(payload.get("caveat", "")),
            cta=str(payload.get("cta", idea.CTA)),
        )
    except ValidationError as exc:
        logger.error("Invalid Gemini script payload: %s", exc)
        return None
    if script.word_count < 90 or script.word_count > 140:
        logger.warning("Generated script word count is outside 90-140: %s", script.word_count)
    return script


def generate_script(idea: Idea) -> Script:
    """Generate a structured script with Gemini or an offline fallback."""

    if settings.offline_mode or not settings.gemini_api_key:
        return build_script_from_idea(idea)
    prompt = render_template(
        "script_generator.md",
        {
            "title": idea.title,
            "hook": idea.hook,
            "viewer_pain": idea.viewer_pain,
            "script_outline": idea.script_outline,
            "tools_needed": idea.tools_needed,
        },
    )
    try:
        script = _parse_script(idea, _call_gemini(prompt))
    except Exception as exc:
        logger.exception("Gemini script generation failed: %s", exc)
        return build_script_from_idea(idea)
    return script or build_script_from_idea(idea)
