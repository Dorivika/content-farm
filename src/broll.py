"""Pexels b-roll search and download helpers."""

import hashlib
from pathlib import Path
from urllib.parse import urlparse

from src.logger import get_logger
from src.settings import settings

logger = get_logger(__name__)
PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
BROLL_DIR = Path("assets") / "backgrounds"


def _keyword_hash(keyword: str) -> str:
    """Return a stable cache hash for a keyword."""

    return hashlib.sha1(keyword.lower().strip().encode("utf-8")).hexdigest()[:12]


def _cached_files(keyword: str) -> list[Path]:
    """Return cached b-roll files for one keyword."""

    return sorted(BROLL_DIR.glob(f"pexels_{_keyword_hash(keyword)}_*.mp4"))


def _pick_video_file(video: dict) -> str:
    """Pick the best vertical video URL from a Pexels video object."""

    files = video.get("video_files", [])
    vertical = [item for item in files if item.get("height", 0) > item.get("width", 0)]
    candidates = sorted(vertical or files, key=lambda item: item.get("height", 0), reverse=True)
    return str(candidates[0].get("link", "")) if candidates else ""


def _download(url: str, path: Path) -> Path:
    """Download one Pexels video URL to a local cache path."""

    import requests

    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=60, stream=True) as response:
        response.raise_for_status()
        with path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return path


def _search_keyword(keyword: str, count: int) -> list[Path]:
    """Search Pexels for one keyword and download missing videos."""

    import requests

    cached = _cached_files(keyword)
    if cached:
        return cached[:count]
    response = requests.get(
        PEXELS_SEARCH_URL,
        headers={"Authorization": settings.pexels_api_key},
        params={"query": keyword, "orientation": "portrait", "per_page": count},
        timeout=30,
    )
    response.raise_for_status()
    paths = []
    for video in response.json().get("videos", []):
        url = _pick_video_file(video)
        if not url:
            continue
        suffix = Path(urlparse(url).path).suffix or ".mp4"
        video_id = str(video.get("id", len(paths)))
        path = BROLL_DIR / f"pexels_{_keyword_hash(keyword)}_{video_id}{suffix}"
        paths.append(path if path.exists() else _download(url, path))
        if len(paths) >= count:
            break
    return paths


def fetch_broll(keywords: list[str], count: int = 5) -> list[Path]:
    """Fetch vertical Pexels b-roll clips for script keywords."""

    if settings.offline_mode or not settings.pexels_api_key:
        return []
    clips: list[Path] = []
    for keyword in [item.strip() for item in keywords if item.strip()]:
        try:
            clips.extend(_search_keyword(keyword, count - len(clips)))
        except Exception as exc:
            logger.warning("Pexels b-roll fetch failed for '%s': %s", keyword, exc)
        if len(clips) >= count:
            break
    return clips[:count]
