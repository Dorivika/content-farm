"""Google Sheets service-account integration for the ideas backlog."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from src.models import Idea
from src.settings import settings

CORE_FIELDS = [
    "idea_id",
    "date_added",
    "source",
    "source_url",
    "content_pillar",
    "target_viewer",
    "viewer_pain",
    "title",
    "hook",
    "script_outline",
    "suggested_visuals",
    "tools_needed",
    "monetization_angle",
    "CTA",
    "platform_primary",
    "platform_secondary",
    "ideal_length_seconds",
    "difficulty_score",
    "novelty_score",
    "monetization_score",
    "production_speed_score",
    "risk_score",
    "total_score",
    "status",
    "assigned_to",
    "due_date",
    "script_status",
    "voiceover_status",
    "video_status",
    "notes",
]
ANALYTICS_FIELDS = [
    "published_url_youtube",
    "published_url_tiktok",
    "published_url_instagram",
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
ALL_FIELDS = CORE_FIELDS + ANALYTICS_FIELDS
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _sheet_id() -> str:
    """Return the configured Google Sheet ID or raise a clear error."""

    if not settings.google_sheet_id:
        raise RuntimeError("Set GOOGLE_SHEET_ID in .env")
    return settings.google_sheet_id


def _credentials_path() -> Path:
    """Return the configured service-account path or raise a clear error."""

    path = settings.google_credentials_path
    if not path.exists():
        raise FileNotFoundError(f"Service account JSON not found at {path}. See README.")
    return path


def _range(a1_range: str) -> str:
    """Return an escaped A1 range for the configured sheet tab."""

    tab = settings.google_sheet_tab.replace("'", "''")
    return f"'{tab}'!{a1_range}"


@lru_cache(maxsize=1)
def get_service() -> Any:
    """Build and cache the Google Sheets API service."""

    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials.from_service_account_file(
        _credentials_path(),
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=credentials)


def read_rows() -> list[dict[str, str]]:
    """Read all rows from the configured sheet tab as dictionaries."""

    service = get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=_sheet_id(), range=_range("A:ZZ"))
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    headers = [str(header).strip() for header in values[0]]
    rows = []
    for raw_row in values[1:]:
        padded = list(raw_row) + [""] * (len(headers) - len(raw_row))
        rows.append(dict(zip(headers, padded, strict=False)))
    return rows


def append_ideas(ideas: list[Idea]) -> None:
    """Append idea rows to the Google Sheet using only core fields."""

    if not ideas:
        return
    rows = []
    for idea in ideas:
        payload = idea.model_dump(mode="json")
        rows.append([payload.get(field, "") for field in CORE_FIELDS])
    get_service().spreadsheets().values().append(
        spreadsheetId=_sheet_id(),
        range=_range("A1"),
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


def count_status(status: str) -> int:
    """Count sheet rows with the requested primary status."""

    return len(get_rows_by_status(status))


def get_rows_by_status(status: str) -> list[dict[str, str]]:
    """Return sheet rows matching a primary status value."""

    return [row for row in read_rows() if row.get("status") == status]


def get_performance_rows(limit: int = 50) -> list[dict[str, str]]:
    """Return recent rows that include any manual analytics metrics."""

    rows = []
    for row in read_rows():
        if any(str(row.get(field, "")).strip() for field in ANALYTICS_FIELDS):
            rows.append(row)
    return rows[-limit:]
