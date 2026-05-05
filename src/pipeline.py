"""Reusable pipeline actions used by CLI commands and daily orchestration."""

import sqlite3
from pathlib import Path

from src import (
    analytics,
    captions,
    db,
    idea_generator,
    package_exporter,
    performance_context,
    renderer,
    sheets,
    voiceover,
)
from src.models import Idea, PlatformPackage, Script
from src.settings import settings


def row_to_idea(row: dict[str, str]) -> Idea:
    """Convert a Google Sheet row dictionary into an Idea model."""

    payload = {field: row.get(field, "") for field in sheets.CORE_FIELDS if field != "total_score"}
    for field in ["idea_id", "date_added"]:
        if not payload.get(field):
            payload.pop(field, None)
    return Idea(**payload)


def generate_and_store_ideas(count: int | None = None, force: bool = False) -> list[Idea]:
    """Generate ideas, append them to Sheets when available, and save locally."""

    history = "[]"
    if settings.gemini_api_key and not settings.offline_mode:
        backlog_count = sheets.count_status("Backlog")
        if backlog_count >= settings.backlog_minimum and not force:
            return []
        history = performance_context.load_performance_context(settings.performance_history_limit)
    ideas = idea_generator.generate_ideas(count, performance_history=history)
    if not ideas:
        return []
    if not settings.offline_mode:
        try:
            sheets.append_ideas(ideas)
        except Exception:
            if settings.gemini_api_key:
                raise
    for idea in ideas:
        db.upsert_idea(idea)
    return ideas


def pull_approved_rows() -> int:
    """Pull Approved ideas from Google Sheets into SQLite."""

    rows = sheets.get_rows_by_status("Approved")
    for row in rows:
        db.upsert_idea(row_to_idea(row))
    return len(rows)


def generate_script_asset(idea_id: str, script: Script) -> Path:
    """Write generated script text to the package output folder."""

    output_path = Path("outputs") / "packages" / f"{idea_id}_script.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script.full_text, encoding="utf-8")
    return output_path


def save_generated_script(idea_id: str, script: Script) -> Path:
    """Save a script and update idea script status."""

    db.save_script(idea_id, script)
    path = generate_script_asset(idea_id, script)
    db.mark_status(idea_id, "script_status", "done")
    db.mark_status(idea_id, "status", "Scripted")
    analytics.append_event(idea_id, "script_generated", {"path": str(path)})
    return path


def generate_voiceover_assets(idea_id: str) -> tuple[Path, Path]:
    """Generate audio and subtitle files for one scripted idea."""

    script = db.get_script(idea_id)
    if script is None:
        raise ValueError(f"Script not found: {idea_id}")
    audio_path = Path("outputs") / "audio" / f"{idea_id}.mp3"
    srt_path = Path("outputs") / "subtitles" / f"{idea_id}.srt"
    overlay_path = Path("outputs") / "captions" / f"{idea_id}_captions.mov"
    voiceover.generate_voiceover(script.full_text, audio_path)
    duration = voiceover.estimate_duration_seconds(script.full_text)
    captions.generate_srt(script, duration, srt_path)
    captions.generate_caption_overlay(audio_path, overlay_path)
    db.mark_status(idea_id, "voiceover_status", "done")
    db.mark_status(idea_id, "status", "Voiceover Done")
    analytics.append_event(
        idea_id,
        "voiceover_generated",
        {"audio_path": str(audio_path), "srt_path": str(srt_path), "overlay_path": str(overlay_path)},
    )
    return audio_path, srt_path


def render_video_asset(idea_id: str) -> Path:
    """Render a video and update render status."""

    video_path = renderer.render_video(idea_id)
    db.mark_status(idea_id, "video_status", "done")
    db.mark_status(idea_id, "status", "Rendered")
    analytics.append_event(idea_id, "video_rendered", {"path": str(video_path)})
    return video_path


def package_video_assets(idea_id: str) -> list[PlatformPackage]:
    """Export platform packages and log the package event."""

    packages = package_exporter.export_packages(idea_id)
    analytics.append_event(
        idea_id,
        "packages_exported",
        {"paths": [package.upload_notes for package in packages]},
    )
    return packages


def list_failed_ideas() -> list[Idea]:
    """Return ideas with any failed sub-status."""

    with sqlite3.connect(db.DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT * FROM ideas
            WHERE script_status = ?
               OR voiceover_status = ?
               OR video_status = ?
            ORDER BY date_added, idea_id
            """,
            ("failed", "failed", "failed"),
        ).fetchall()
    return [Idea(**dict(row)) for row in rows]
