"""Parse Gemini idea responses into validated Idea models."""

import json
import re
from datetime import date
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from src.logger import get_logger
from src.models import Idea

logger = get_logger(__name__)


def _extract_json(text: str) -> str:
    """Extract a JSON payload from a model response."""

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    return fence.group(1).strip() if fence else cleaned


def _clean_key(value: str) -> str:
    """Normalize a Markdown table field name."""

    return re.sub(r"[^A-Za-z0-9_]+", "", value).strip()


def _clean_value(value: str) -> str:
    """Normalize a Markdown table field value."""

    value = value.strip().strip("|").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _coerce_payload(item: dict[str, Any]) -> dict[str, Any]:
    """Prepare a raw idea payload for Pydantic validation."""

    payload = dict(item)
    payload["idea_id"] = str(uuid4())
    payload["date_added"] = date.today().isoformat()
    payload.setdefault("source", "gemini_generated")
    payload.setdefault("source_url", "")
    payload.setdefault("notes", "")
    return payload


def _validate_payloads(payloads: list[dict[str, Any]]) -> list[Idea]:
    """Validate idea payload dictionaries and drop invalid rows."""

    ideas: list[Idea] = []
    for item in payloads:
        try:
            ideas.append(Idea(**_coerce_payload(item)))
        except ValidationError as exc:
            logger.warning("Dropping invalid idea payload: %s", exc)
    return ideas


def _parse_json_ideas(raw_text: str) -> list[Idea]:
    """Parse a JSON idea response."""

    payload = json.loads(_extract_json(raw_text))
    if not isinstance(payload, list):
        raise ValueError("Gemini idea response was not a JSON array")
    return _validate_payloads([item for item in payload if isinstance(item, dict)])


def _parse_markdown_concepts(raw_text: str) -> list[Idea]:
    """Parse Deep Research Markdown concept tables into ideas."""

    blocks = re.split(r"(?im)^###\s+Concept\s+\d+[:.\-\s]*(.*?)\s*$", raw_text)
    payloads: list[dict[str, Any]] = []
    for index in range(2, len(blocks), 2):
        block = blocks[index]
        payload: dict[str, Any] = {}
        for line in block.splitlines():
            match = re.match(r"^\|\s*\*\*(?P<key>[^*]+)\*\*\s*\|\s*(?P<value>.*?)\s*\|?\s*$", line)
            if not match:
                continue
            key = _clean_key(match.group("key"))
            value = _clean_value(match.group("value"))
            if key in {"Parameter", ""}:
                continue
            payload[key] = value
        if payload:
            payloads.append(payload)
    return _validate_payloads(payloads)


def parse_ideas(raw_text: str) -> list[Idea]:
    """Parse Gemini output as JSON first, then Markdown concept tables."""

    try:
        return _parse_json_ideas(raw_text)
    except Exception as exc:
        logger.warning("Failed to parse Gemini idea JSON, trying Markdown tables: %s", exc)
    ideas = _parse_markdown_concepts(raw_text)
    if not ideas:
        logger.error("Failed to parse Gemini ideas from response: %s", raw_text)
    return ideas
