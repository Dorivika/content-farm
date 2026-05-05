"""Export manual upload packages for each target platform."""

from pathlib import Path

from src import db
from src.models import PlatformPackage
from src.prompts import load_account_config, load_niche_config


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text with ellipsis when needed."""

    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."


def _hashtags(idea) -> list[str]:
    """Build a short hashtag set from brand defaults and topic terms."""

    account = load_account_config()
    niche = load_niche_config()
    pool = niche.get("hashtag_pool") or account.get("defaults", {}).get("hashtag_pool", [])
    tags = list(pool[:4])
    topic = "".join(part.title() for part in idea.content_pillar.split("_"))
    topic_tag = f"#{topic}"
    if topic_tag not in tags:
        tags.append(topic_tag)
    return tags[:5]


def _value_summary(idea) -> str:
    """Return a compact value summary for captions."""

    outline = idea.script_outline.strip()
    return _truncate(outline, 220) if outline else _truncate(idea.viewer_pain, 160)


def _write_package(path: Path, text: str) -> None:
    """Write a platform package text file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _youtube_package(idea, tags: list[str]) -> PlatformPackage:
    """Create and write the YouTube Shorts package."""

    title = _truncate(idea.title, 100)
    caption = (
        f"TITLE: {title}\n\n"
        "DESCRIPTION:\n"
        f"{idea.hook}\n\n"
        f"{_value_summary(idea)}\n\n"
        f"{idea.CTA}\n\n"
        f"{' '.join(tags)}\n\n"
        "UPLOAD NOTES:\n"
        "- Category: Science & Technology\n"
        "- Visibility: Public\n"
        "- Shorts: Yes (vertical 9:16)\n"
        "- End screen: Subscribe prompt\n"
    )
    path = Path("outputs") / "packages" / "youtube" / f"{idea.idea_id}.txt"
    _write_package(path, caption)
    return PlatformPackage(
        idea_id=idea.idea_id,
        platform="youtube",
        title=title,
        caption=caption,
        hashtags=tags,
        cta=idea.CTA,
        upload_notes=str(path),
    )


def _tiktok_package(idea, tags: list[str]) -> PlatformPackage:
    """Create and write the TikTok package."""

    punchy = _truncate(idea.hook.rstrip(".") + ".", 80)
    caption = (
        "CAPTION:\n"
        f"{punchy} {idea.CTA} {' '.join(tags)}\n\n"
        "UPLOAD NOTES:\n"
        "- Sound: Original\n"
        "- Allow duets: Yes\n"
        "- Allow stitches: Yes\n"
    )
    path = Path("outputs") / "packages" / "tiktok" / f"{idea.idea_id}.txt"
    _write_package(path, caption)
    return PlatformPackage(
        idea_id=idea.idea_id,
        platform="tiktok",
        title=idea.title,
        caption=caption,
        hashtags=tags,
        cta=idea.CTA,
        upload_notes=str(path),
    )


def _instagram_package(idea, tags: list[str]) -> PlatformPackage:
    """Create and write the Instagram Reels package."""

    caption = (
        "CAPTION:\n"
        f"{idea.hook}\n\n"
        f"{_value_summary(idea)}\n\n"
        f"{idea.CTA}\n\n"
        f"{' '.join(tags)}\n\n"
        "UPLOAD NOTES:\n"
        "- Cover: Auto-select or custom thumbnail\n"
        "- Share to Feed: Yes\n"
        "- Share to Stories: Optional\n"
    )
    path = Path("outputs") / "packages" / "instagram" / f"{idea.idea_id}.txt"
    _write_package(path, caption)
    return PlatformPackage(
        idea_id=idea.idea_id,
        platform="instagram",
        title=idea.title,
        caption=caption,
        hashtags=tags,
        cta=idea.CTA,
        upload_notes=str(path),
    )


def export_packages(idea_id: str) -> list[PlatformPackage]:
    """Export manual upload packages for all supported platforms."""

    idea = db.get_idea(idea_id)
    if idea is None:
        raise ValueError(f"Idea not found: {idea_id}")
    tags = _hashtags(idea)
    return [
        _youtube_package(idea, tags),
        _tiktok_package(idea, tags),
        _instagram_package(idea, tags),
    ]


def save_package(package: PlatformPackage, output_dir: Path) -> Path:
    """Write a platform package text file for manual upload."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{package.idea_id}_{package.platform}.txt"
    output_path.write_text(package.caption, encoding="utf-8")
    return output_path
