"""Rule-based script generation helpers for approved ideas."""

from src.models import Idea, Script


def build_script_from_idea(idea: Idea) -> Script:
    """Create a structured script draft from an idea without external calls."""

    return Script(
        idea_id=idea.idea_id,
        hook=idea.hook,
        problem=f"{idea.target_viewer} often lose time because {idea.viewer_pain}",
        old_way="The old way is copying data between tools, rewriting the same notes, and checking everything manually.",
        steps=[
            f"Step one: define the exact trigger for {idea.title.lower()}.",
            f"Step two: use {idea.tools_needed} to draft, transform, or route the work.",
            "Step three: keep a human approval checkpoint before anything goes live.",
        ],
        caveat="Do not automate decisions that need judgment, compliance review, or customer trust.",
        cta=idea.CTA,
    )
