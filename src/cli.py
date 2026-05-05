"""Typer command-line interface for content farm operations."""

from collections import Counter

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import db, orchestrator, pipeline, script_generator, sheets
from src.logger import get_logger
from src.models import Idea

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


@app.command("init-db")
def init_db_command() -> None:
    """Initialize the local SQLite database."""

    db.init_db()
    console.print("[green]SQLite database initialized at data/content.db[/green]")


@app.command("check-backlog")
def check_backlog_command() -> None:
    """Count Backlog rows in the configured Google Sheet."""

    console.print(f"[cyan]Backlog ideas:[/cyan] {sheets.count_status('Backlog')}")


@app.command("generate-ideas")
def generate_ideas_command(
    count: int | None = typer.Option(None, "--count", "-c", help="Number of ideas to request."),
    force: bool = typer.Option(False, "--force", help="Generate even when backlog is healthy."),
) -> None:
    """Generate ideas, append them to Sheets when available, and save locally."""

    db.init_db()
    try:
        ideas = pipeline.generate_and_store_ideas(count, force)
    except Exception as exc:
        logger.exception("Idea generation failed: %s", exc)
        console.print("[red]No ideas generated.[/red]")
        raise typer.Exit(code=1) from exc
    if not ideas:
        console.print("[red]No ideas generated.[/red]")
        raise typer.Exit(code=1)
    _print_pillar_summary(ideas)
    console.print(f"[green]{len(ideas)} saved[/green], [red]0 failed[/red]")


@app.command("pull-approved")
def pull_approved_command() -> None:
    """Pull Approved ideas from Google Sheets into SQLite."""

    db.init_db()
    try:
        count = pipeline.pull_approved_rows()
    except Exception as exc:
        logger.exception("Failed to read approved rows: %s", exc)
        console.print(f"[red]Could not read Google Sheets:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]{count} approved ideas pulled[/green], [red]0 failed[/red]")


@app.command("generate-script")
def generate_script_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Generate and save a script for one local idea."""

    db.init_db()
    idea = db.get_idea(idea_id)
    if idea is None:
        console.print(f"[red]Idea not found:[/red] {idea_id}")
        raise typer.Exit(code=1)
    try:
        script = script_generator.generate_script(idea)
        pipeline.save_generated_script(idea_id, script)
        console.print(Panel(script.full_text, title=f"Script: {idea.title}"))
        console.print("[green]1 succeeded[/green], [red]0 failed[/red]")
    except Exception as exc:
        logger.exception("Failed to generate script for %s: %s", idea_id, exc)
        db.mark_status(idea_id, "script_status", "failed")
        console.print("[green]0 succeeded[/green], [red]1 failed[/red]")
        raise typer.Exit(code=1) from exc


@app.command("voiceover")
def voiceover_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Generate voiceover audio and SRT subtitles for one script."""

    db.init_db()
    try:
        audio_path, srt_path = pipeline.generate_voiceover_assets(idea_id)
        console.print(f"[green]Audio:[/green] {audio_path}")
        console.print(f"[green]Subtitles:[/green] {srt_path}")
        console.print("[green]1 succeeded[/green], [red]0 failed[/red]")
    except Exception as exc:
        logger.exception("Voiceover failed for %s: %s", idea_id, exc)
        db.mark_status(idea_id, "voiceover_status", "failed")
        console.print("[green]0 succeeded[/green], [red]1 failed[/red]")
        raise typer.Exit(code=1) from exc


@app.command("render")
def render_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Render a vertical MP4 for one idea."""

    db.init_db()
    try:
        video_path = pipeline.render_video_asset(idea_id)
        console.print(f"[green]Video:[/green] {video_path}")
        console.print("[green]1 succeeded[/green], [red]0 failed[/red]")
    except Exception as exc:
        logger.exception("Render failed for %s: %s", idea_id, exc)
        db.mark_status(idea_id, "video_status", "failed")
        console.print("[green]0 succeeded[/green], [red]1 failed[/red]")
        raise typer.Exit(code=1) from exc


@app.command("package")
def package_command(idea_id: str = typer.Option(..., "--idea-id")) -> None:
    """Export manual upload packages for one rendered idea."""

    db.init_db()
    try:
        packages = pipeline.package_video_assets(idea_id)
    except Exception as exc:
        logger.exception("Package export failed for %s: %s", idea_id, exc)
        raise typer.Exit(code=1) from exc
    for package in packages:
        console.print(f"[green]{package.platform}:[/green] {package.upload_notes}")


@app.command("run-daily")
def run_daily_command() -> None:
    """Run the daily content pipeline."""

    orchestrator.run_daily()


@app.command("retry-failed")
def retry_failed_command() -> None:
    """Retry ideas with failed script, voiceover, or render sub-status."""

    orchestrator.retry_failed()
