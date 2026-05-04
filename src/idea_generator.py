"""Offline-safe seed idea generation for the Phase 1 foundation."""

from itertools import cycle, islice

from src.models import Idea
from src.prompts import load_account_config, load_niche_config


def generate_seed_ideas(count: int = 5) -> list[Idea]:
    """Generate deterministic original backlog ideas from configured pillars."""

    account = load_account_config()
    niche = load_niche_config()
    pillars = niche.get("content_pillars", [])
    audiences = niche.get("audience", {}).get("primary", ["small business operators"])
    cta = account.get("defaults", {}).get("cta", "Follow for one AI workflow a day.")
    ideas: list[Idea] = []
    for index, pillar in enumerate(islice(cycle(pillars), count), start=1):
        audience = audiences[(index - 1) % len(audiences)]
        label = pillar.get("label", "Manual task -> AI workflow")
        title = f"{label} for {audience}"
        ideas.append(
            Idea(
                source="generated",
                content_pillar=pillar.get("id", "manual_to_ai"),
                target_viewer=audience,
                viewer_pain="A recurring business task takes too much manual time.",
                title=title,
                hook=f"Replace one repetitive task with this {audience} AI workflow.",
                script_outline="Show the manual task, the lightweight workflow, and one caveat.",
                suggested_visuals="Screen capture of the task list, workflow diagram, and result.",
                tools_needed="AI assistant, spreadsheet, automation tool",
                monetization_angle="Consulting, templates, or workflow implementation services",
                CTA=cta,
                novelty_score=3,
                monetization_score=4,
                production_speed_score=4,
                difficulty_score=2,
                risk_score=2,
            )
        )
    return ideas
