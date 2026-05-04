"""Build compact performance context for research-aware ideation."""

import json

from src import sheets

METRIC_FIELDS = [
    "views_24h",
    "avg_view_duration",
    "retention_percent",
    "likes",
    "comments",
    "shares",
    "saves",
    "profile_visits",
    "link_clicks",
    "email_signups",
    "sales",
]


def _clean(value: str) -> str:
    """Normalize a Google Sheets cell for prompt context."""

    return str(value or "").strip()


def _metric_payload(row: dict[str, str]) -> dict[str, str]:
    """Extract non-empty analytics metrics from one row."""

    return {field: _clean(row.get(field, "")) for field in METRIC_FIELDS if _clean(row.get(field, ""))}


def row_to_record(row: dict[str, str]) -> dict[str, object]:
    """Convert one sheet row into compact research context."""

    return {
        "title": _clean(row.get("title", "")),
        "content_pillar": _clean(row.get("content_pillar", "")),
        "target_viewer": _clean(row.get("target_viewer", "")),
        "hook": _clean(row.get("hook", "")),
        "tools_needed": _clean(row.get("tools_needed", "")),
        "status": _clean(row.get("status", "")),
        "date_added": _clean(row.get("date_added", "")),
        "metrics": _metric_payload(row),
    }


def build_performance_context(rows: list[dict[str, str]]) -> str:
    """Render historical idea metrics as compact JSON for the prompt."""

    records = [row_to_record(row) for row in rows]
    return json.dumps(records, ensure_ascii=True, indent=2)


def load_performance_context(limit: int) -> str:
    """Load recent performance rows from Sheets as prompt context."""

    return build_performance_context(sheets.get_performance_rows(limit))
