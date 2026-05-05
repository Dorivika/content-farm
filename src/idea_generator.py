"""Deep Research-backed idea generation with deterministic offline fallback."""

from typing import Any

from src.deep_research import run_deep_research
from src.idea_parser import parse_ideas
from src.logger import get_logger
from src.models import Idea
from src.prompts import load_account_config, load_niche_config, render_template
from src.settings import settings

logger = get_logger(__name__)


def _sample_idea_payloads() -> list[dict[str, Any]]:
    """Return deterministic original sample ideas for offline testing."""

    return [
        {
            "content_pillar": "manual_to_ai",
            "target_viewer": "freelance designer",
            "viewer_pain": "rewriting client feedback into task lists after every call",
            "title": "Turn client feedback into tasks with Gemini and Trello",
            "hook": "Your feedback calls leak time",
            "script_outline": "Show a messy call transcript becoming grouped action items. Then show a human approval step before cards are created.",
            "suggested_visuals": "Transcript, Gemini prompt, Trello board, checked approval column.",
            "tools_needed": "Gemini, Trello, Google Docs",
            "monetization_angle": "Sell a client delivery workflow template.",
            "CTA": "Comment TASKS for the prompt structure.",
            "platform_primary": "youtube_shorts",
            "platform_secondary": "instagram_reels",
            "ideal_length_seconds": 45,
            "difficulty_score": 2,
            "novelty_score": 4,
            "monetization_score": 4,
            "production_speed_score": 5,
            "risk_score": 1,
        },
        {
            "content_pillar": "smb_automation",
            "target_viewer": "local service business owner",
            "viewer_pain": "missing follow-ups after quote requests",
            "title": "Auto-draft quote follow-ups without auto-sending them",
            "hook": "Stop losing warm quotes",
            "script_outline": "Explain a workflow where form submissions create a draft follow-up. The owner reviews the draft before sending.",
            "suggested_visuals": "Google Form, Sheet row, Gmail draft, approval checkbox.",
            "tools_needed": "Google Forms, Google Sheets, Gmail, Zapier",
            "monetization_angle": "Lead into done-for-you automation setup.",
            "CTA": "Save this before your next quote request.",
            "platform_primary": "instagram_reels",
            "platform_secondary": "youtube_shorts",
            "ideal_length_seconds": 40,
            "difficulty_score": 2,
            "novelty_score": 3,
            "monetization_score": 5,
            "production_speed_score": 4,
            "risk_score": 1,
        },
        {
            "content_pillar": "saas_alternative",
            "target_viewer": "solo founder",
            "viewer_pain": "paying for a CRM before sales volume justifies it",
            "title": "Build a tiny CRM in Sheets with AI summaries",
            "hook": "Your CRM can wait",
            "script_outline": "Show a lean spreadsheet CRM with AI-generated next steps. Emphasize that it is for early-stage sales, not complex teams.",
            "suggested_visuals": "Sheet pipeline, notes column, AI summary, next action filter.",
            "tools_needed": "Google Sheets, Gemini, Apps Script",
            "monetization_angle": "Promote a founder operations template.",
            "CTA": "Follow for one workflow a day.",
            "platform_primary": "tiktok",
            "platform_secondary": "instagram_reels",
            "ideal_length_seconds": 50,
            "difficulty_score": 3,
            "novelty_score": 4,
            "monetization_score": 4,
            "production_speed_score": 4,
            "risk_score": 1,
        },
        {
            "content_pillar": "prompt_system",
            "target_viewer": "agency operator",
            "viewer_pain": "turning vague client requests into usable briefs",
            "title": "A prompt system for cleaner client briefs",
            "hook": "Vague briefs cost money",
            "script_outline": "Break down a three-question prompt that extracts goals, constraints, and deliverables. Show the before and after brief.",
            "suggested_visuals": "Bad brief, prompt checklist, improved brief, approval marker.",
            "tools_needed": "ChatGPT or Gemini, Notion",
            "monetization_angle": "Offer a client onboarding prompt pack.",
            "CTA": "Steal the three-question structure.",
            "platform_primary": "youtube_shorts",
            "platform_secondary": "tiktok",
            "ideal_length_seconds": 35,
            "difficulty_score": 1,
            "novelty_score": 3,
            "monetization_score": 4,
            "production_speed_score": 5,
            "risk_score": 1,
        },
        {
            "content_pillar": "india_tech",
            "target_viewer": "Indian tech job seeker",
            "viewer_pain": "customizing resumes for each job description manually",
            "title": "Match your resume to a JD without lying",
            "hook": "Do not fake resume keywords",
            "script_outline": "Show how to compare a resume with a job description and identify truthful gaps. Keep the human review step explicit.",
            "suggested_visuals": "Resume, job description, gap table, honest rewrite checklist.",
            "tools_needed": "Gemini, Google Docs, Google Sheets",
            "monetization_angle": "Lead into career workflow templates.",
            "CTA": "Share this with a job seeker.",
            "platform_primary": "instagram_reels",
            "platform_secondary": "youtube_shorts",
            "ideal_length_seconds": 45,
            "difficulty_score": 2,
            "novelty_score": 4,
            "monetization_score": 3,
            "production_speed_score": 4,
            "risk_score": 2,
        },
    ]


def _build_prompt(count: int, performance_history: str) -> str:
    """Render the idea research prompt from YAML configuration."""

    account = load_account_config()
    niche = load_niche_config()
    audience_config = niche.get("audience", {})
    audience = audience_config.get("primary", []) + audience_config.get("secondary", [])
    return render_template(
        "idea_research.md",
        {
            "niche": niche.get("niche", ""),
            "tagline": account.get("brand", {}).get("tagline", ""),
            "content_pillars": niche.get("content_pillars", []),
            "audience": audience,
            "performance_history": performance_history,
            "count": count,
        },
    )


def generate_sample_ideas() -> list[Idea]:
    """Generate five deterministic valid ideas for offline testing."""

    return [Idea(source="offline_sample", source_url="", **item) for item in _sample_idea_payloads()]


def generate_seed_ideas(count: int = 5) -> list[Idea]:
    """Generate deterministic original backlog ideas from configured pillars."""

    return generate_sample_ideas()[:count]


def generate_ideas(count: int | None = None, performance_history: str = "[]") -> list[Idea]:
    """Generate original content ideas with Deep Research or an offline fallback."""

    if settings.offline_mode or not settings.gemini_api_key:
        logger.warning("No Gemini API key. Using sample ideas for testing.")
        return generate_sample_ideas()
    idea_count = count or settings.ideas_to_generate
    try:
        return parse_ideas(run_deep_research(_build_prompt(idea_count, performance_history)))
    except Exception as exc:
        logger.exception("Deep Research idea generation failed: %s", exc)
        return []
