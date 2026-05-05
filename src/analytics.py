"""CSV and SQLite analytics event logging."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src import db
from src.models import AnalyticsEvent

ANALYTICS_PATH = Path("data") / "analytics.csv"
HEADERS = ["timestamp", "idea_id", "event_type", "detail"]


def init_analytics() -> None:
    """Create the analytics CSV file if it does not exist."""

    ANALYTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ANALYTICS_PATH.exists():
        with ANALYTICS_PATH.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=HEADERS).writeheader()


def append_event(idea_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Append an analytics event to CSV and SQLite."""

    init_analytics()
    timestamp = datetime.utcnow()
    detail = json.dumps(payload, ensure_ascii=True)
    with ANALYTICS_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writerow(
            {
                "timestamp": timestamp.isoformat(),
                "idea_id": idea_id,
                "event_type": event_type,
                "detail": detail,
            }
        )
    db.insert_analytics_event(
        AnalyticsEvent(
            idea_id=idea_id,
            event_type=event_type,
            timestamp=timestamp,
            payload=payload,
        )
    )


def record_event(idea_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Record an analytics event in local analytics stores."""

    append_event(idea_id, event_type, payload)
