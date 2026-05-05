"""Daily pipeline orchestration and retry flows."""

from collections.abc import Callable

from rich.console import Console
from rich.panel import Panel

from src import db, pipeline, script_generator, sheets
from src.logger import get_logger
from src.settings import settings

logger = get_logger(__name__)
console = Console()


def script_one(idea_id: str) -> None:
    """Generate and save one script for orchestration."""

    idea = db.get_idea(idea_id)
    if idea is None:
        raise ValueError(f"Idea not found: {idea_id}")
    pipeline.save_generated_script(idea_id, script_generator.generate_script(idea))


def _run_batch(
    status: str,
    failed_field: str,
    results: dict[str, int],
    action: Callable[[str], object],
) -> None:
    """Run one daily pipeline batch with isolated failures."""

    for idea in db.list_ideas_by_status(status)[:3]:
        try:
            action(idea.idea_id)
            results["success"] += 1
        except Exception as exc:
            logger.error("%s failed for %s: %s", status, idea.idea_id, exc)
            if failed_field:
                db.mark_status(idea.idea_id, failed_field, "failed")
            results["failed"] += 1


def run_daily() -> dict[str, int]:
    """Run the daily content pipeline with isolated failures."""

    db.init_db()
    results = {"success": 0, "failed": 0}
    try:
        count = 0 if settings.offline_mode else sheets.count_status("Backlog")
        console.print(f"Backlog count: {count}")
        if settings.offline_mode or count < settings.backlog_minimum:
            console.print("Backlog low. Generating ideas...")
            pipeline.generate_and_store_ideas(force=True)
    except Exception as exc:
        logger.error("Backlog check failed: %s", exc)
    try:
        pulled = 0 if settings.offline_mode else pipeline.pull_approved_rows()
        console.print(f"Pulled approved ideas: {pulled}")
    except Exception as exc:
        logger.error("Pull approved failed: %s", exc)
    _run_batch("Approved", "script_status", results, script_one)
    _run_batch("Scripted", "voiceover_status", results, pipeline.generate_voiceover_assets)
    _run_batch("Voiceover Done", "video_status", results, pipeline.render_video_asset)
    _run_batch("Rendered", "", results, pipeline.package_video_assets)
    console.print(Panel(f"Done: {results['success']} succeeded, {results['failed']} failed", title="Daily Pipeline Complete"))
    return results


def retry_failed() -> dict[str, int]:
    """Retry ideas with failed script, voiceover, or render sub-status."""

    db.init_db()
    results = {"success": 0, "failed": 0}
    for idea in pipeline.list_failed_ideas():
        try:
            if idea.script_status == "failed":
                db.mark_status(idea.idea_id, "script_status", "pending")
                script_one(idea.idea_id)
            elif idea.voiceover_status == "failed":
                db.mark_status(idea.idea_id, "voiceover_status", "pending")
                pipeline.generate_voiceover_assets(idea.idea_id)
            elif idea.video_status == "failed":
                db.mark_status(idea.idea_id, "video_status", "pending")
                pipeline.render_video_asset(idea.idea_id)
            results["success"] += 1
        except Exception as exc:
            logger.error("Retry failed for %s: %s", idea.idea_id, exc)
            results["failed"] += 1
    console.print(Panel(f"Done: {results['success']} retried, {results['failed']} failed", title="Retry Complete"))
    return results
