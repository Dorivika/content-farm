"""Typer command-line interface for Phase 1 operations."""

import typer
from rich.console import Console

from src import db, sheets
from src.logger import get_logger

app = typer.Typer(help="Faceless content farm automation CLI.")
console = Console()
logger = get_logger(__name__)


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
