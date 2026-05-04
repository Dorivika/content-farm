"""Typer command-line interface for content farm operations."""

from collections import Counter
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import (
    captions,
    db,
    idea_generator,
    performance_context,
    renderer,
    script_generator,
    sheets,
    voiceover,
)
from src.logger import get_logger
from src.models import Idea
from src.settings import settings

app = typer.Typer(help="Faceless content farm automation CLI.")
console = Console()
logger = get_logger(__name__)


def _print_pillar_summary(ideas: list[Idea]) -> None:
    """Print a Rich summary table for generated ideas."""

    table = Table(title="Generated Ideas")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Total", str(len(ideas)))
    for pillar, count in sorted(Counter(idea.content_pillar for idea in ideas).items()):
        table.add_row(pillar, str(count))
    console.print(table)


def _row_to_idea(row: dict[str, str]) -> Idea:
    """Convert a Google Sheet row dictionary into an Idea model."""

    payload = {field: row.get(field, "") for field in sheets.CORE_FIELDS if field != "total_score"}
    for field in ["idea_id", "date_added"]:
        if not payload.get(field):
            payload.pop(field, None)
    return Idea(**payload)


@app.command("init-db")
def init_db_command() -> None:
    """Initialize the local SQLite database."""

    db.init_db()
    logger.info("Initialized database")
    console.print("[green]SQLite database initialized at data/content.db[/green]")


@app.command("check-backlog")
def check_backlog_command() -> None:
    """Count Backlog rows in the configured Google Sheet."""

    count = sheets.count_status("Backlog")
    console.print(f"[cyan]Backlog ideas:[/cyan] {count}")


@app.command("generate-ideas")
def generate_ideas_command(
    count: int | None = typer.Option(None, "--count", "-c", help="Number of ideas to request."),
    force: bool = typer.Option(False, "--force", help="Generate even when backlog is healthy."),
) -> None:
    """Generate ideas, append them to Sheets when available, and save locally."""

    db.init_db()
    history = "[]"
    if settings.gemini_api_key:
        try:
            backlog_count = sheets.count_status("Backlog")
            if backlog_count >= settings.backlog_minimum and not force:
                console.print(
                    f"[green]Backlog is healthy:[/green] {backlog_count} ideas "
                    f"(minimum {settings.backlog_minimum}). Use --force to override."
                )
                return
            history = performance_context.load_performance_context(
                settings.performance_history_limit
            )
        except Exception as exc:
            logger.warning("Could not load Sheets backlog/performance context: %s", exc)
            console.print(f"[yellow]Performance context skipped:[/yellow] {exc}")

    ideas = idea_generator.generate_ideas(count, performance_history=history)
    if not ideas:
        console.print("[red]No ideas generated.[/red]")
        raise typer.Exit(code=1)

    try:
        sheets.append_ideas(ideas)
    except Exception as exc:
        logger.warning("Could not append ideas to Google Sheets: %s", exc)
        console.print(f"[yellow]Sheets append skipped:[/yellow] {exc}")

    succeeded = 0
    failed = 0
    for idea in ideas:
        try:
            db.upsert_idea(idea)
            succeeded += 1
        except Exception as exc:
            failed += 1
            logger.exception("Failed to save idea %s: %s", idea.idea_id, exc)
    _print_pillar_summary(ideas)
    console.print(f"[green]{succeeded} saved[/green], [red]{failed} failed[/red]")


@app.command("pull-approved")
def pull_approved_command() -> None:
    """Pull Approved ideas from Google Sheets into SQLite."""

    db.init_db()
    succeeded = 0
    failed = 0
    try:
        rows = sheets.get_rows_by_status("Approved")
    except Exception as exc:
        logger.exception("Failed to read approved rows: %s", exc)
        console.print(f"[red]Could not read Google Sheets:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    for row in rows:
        try:
            db.upsert_idea(_row_to_idea(row))
            succeeded += 1
        except Exception as exc:
            failed += 1
            logger.exception("Failed to import approved row: %s", exc)
    console.print(f"[green]{succeeded} approved ideas pulled[/green], [red]{failed} failed[/red]")


@app.command("generate-script")
def generate_script_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Generate and save a script for one local idea."""

    db.init_db()
    idea = db.get_idea(idea_id)
    if idea is None:
        console.print(f"[red]Idea not found:[/red] {idea_id}")
        raise typer.Exit(code=1)

    succeeded = 0
    failed = 0
    try:
        script = script_generator.generate_script(idea)
        db.save_script(idea_id, script)
        output_path = Path("outputs") / "packages" / f"{idea_id}_script.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script.full_text, encoding="utf-8")
        db.mark_status(idea_id, "script_status", "done")
        db.mark_status(idea_id, "status", "Scripted")
        succeeded = 1
        console.print(Panel(script.full_text, title=f"Script: {idea.title}"))
    except Exception as exc:
        failed = 1
        logger.exception("Failed to generate script for %s: %s", idea_id, exc)
        try:
            db.mark_status(idea_id, "script_status", "failed")
        except Exception as status_exc:
            logger.exception("Failed to mark script failure for %s: %s", idea_id, status_exc)
    console.print(f"[green]{succeeded} succeeded[/green], [red]{failed} failed[/red]")
    if failed:
        raise typer.Exit(code=1)


@app.command("voiceover")
def voiceover_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Generate voiceover audio and SRT subtitles for one script."""

    db.init_db()
    script = db.get_script(idea_id)
    if script is None:
        console.print(f"[red]Script not found:[/red] {idea_id}")
        raise typer.Exit(code=1)

    audio_path = Path("outputs") / "audio" / f"{idea_id}.mp3"
    srt_path = Path("outputs") / "subtitles" / f"{idea_id}.srt"
    try:
        voiceover.generate_voiceover(script.full_text, audio_path)
        duration = voiceover.estimate_duration_seconds(script.full_text)
        captions.generate_srt(script, duration, srt_path)
        db.mark_status(idea_id, "voiceover_status", "done")
        db.mark_status(idea_id, "status", "Voiceover Done")
        console.print(f"[green]Audio:[/green] {audio_path}")
        console.print(f"[green]Subtitles:[/green] {srt_path}")
        console.print("[green]1 succeeded[/green], [red]0 failed[/red]")
    except Exception as exc:
        logger.exception("Voiceover failed for %s: %s", idea_id, exc)
        try:
            db.mark_status(idea_id, "voiceover_status", "failed")
        except Exception as status_exc:
            logger.exception("Failed to mark voiceover failure for %s: %s", idea_id, status_exc)
        console.print("[green]0 succeeded[/green], [red]1 failed[/red]")
        raise typer.Exit(code=1) from exc


@app.command("render")
def render_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Render a vertical MP4 for one idea."""

    db.init_db()
    try:
        video_path = renderer.render_video(idea_id)
        db.mark_status(idea_id, "video_status", "done")
        db.mark_status(idea_id, "status", "Rendered")
        console.print(f"[green]Video:[/green] {video_path}")
        console.print("[green]1 succeeded[/green], [red]0 failed[/red]")
    except Exception as exc:
        logger.exception("Render failed for %s: %s", idea_id, exc)
        try:
            db.mark_status(idea_id, "video_status", "failed")
        except Exception as status_exc:
            logger.exception("Failed to mark render failure for %s: %s", idea_id, status_exc)
        console.print("[green]0 succeeded[/green], [red]1 failed[/red]")
        raise typer.Exit(code=1) from exc
