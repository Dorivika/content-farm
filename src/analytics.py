"""Analytics helpers for local event capture."""

from typing import Any

from src.db import insert_analytics_event
from src.models import AnalyticsEvent


def record_event(idea_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Record an analytics event in the local SQLite database."""

    insert_analytics_event(
        AnalyticsEvent(idea_id=idea_id, event_type=event_type, payload=payload)
    )
