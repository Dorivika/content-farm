"""FFmpeg rendering helpers for vertical videos."""

import re
import subprocess
from pathlib import Path

from src import captions, db
from src.logger import get_logger
from src.settings import settings
from src.voiceover import estimate_duration_seconds

logger = get_logger(__name__)


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter on Windows."""

    text = re.sub(r"[\r\n]+", " ", text)
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    text = text.replace(",", "\\,")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace(";", "\\;")
    text = text.replace("%", "\\%")
    return text


def _to_ffmpeg_path(path: Path) -> str:
    """Convert Windows path to forward-slash format for FFmpeg filters."""

    return str(path.resolve()).replace("\\", "/")


def _to_filter_path(path: Path) -> str:
    """Convert a path for use inside FFmpeg filter arguments."""

    return _to_ffmpeg_path(path).replace(":", "\\:")


def _check_ffmpeg() -> None:
    """Ensure FFmpeg can be executed."""

    try:
        subprocess.run(
            [settings.ffmpeg_path, "-version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"FFmpeg not found at '{settings.ffmpeg_path}'. Install from "
            "https://ffmpeg.org and set FFMPEG_PATH in .env"
        ) from exc


def _font_filter_part() -> str:
    """Return an optional drawtext fontfile filter fragment."""

    font_files = list((Path("assets") / "fonts").glob("*.ttf"))
    if not font_files:
        font_files = list((Path("assets") / "fonts").glob("*.otf"))
    return f":fontfile={_to_filter_path(font_files[0])}" if font_files else ""


def _drawtext(text: str, y: str, size: int, extra: str = "") -> str:
    """Build one FFmpeg drawtext filter."""

    font = _font_filter_part()
    escaped = _escape_drawtext(text)
    return (
        "drawtext="
        f"text={escaped}"
        f"{font}:fontsize={size}:fontcolor=white:"
        "box=1:boxcolor=black@0.45:boxborderw=24:"
        f"x=(w-text_w)/2:y={y}{extra}"
    )


def _caption_drawtext_filters(script, duration: float) -> list[str]:
    """Build drawtext filters that burn timed subtitles into the video."""

    filters = []
    for segment, start, end in captions.segment_timings(script, duration):
        enable = f":enable=between(t\\,{start:.2f}\\,{end:.2f})"
        filters.append(_drawtext(segment, "h-360", 36, enable))
    return filters


def _video_input_args(background_path: Path, duration: float) -> list[str]:
    """Build FFmpeg input arguments for asset or generated background."""

    if background_path.exists():
        return ["-stream_loop", "-1", "-i", str(background_path)]
    return [
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x1a1a2e:s=1080x1920:d={duration:.2f}:r=30",
    ]


def _probe_audio_duration(audio_path: Path, fallback: float) -> float:
    """Return actual audio duration using ffprobe when available."""

    ffprobe = "ffprobe"
    if settings.ffmpeg_path.lower().endswith("ffmpeg.exe"):
        ffprobe = str(Path(settings.ffmpeg_path).with_name("ffprobe.exe"))
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return max(fallback, float(result.stdout.strip()))
    except Exception as exc:
        logger.warning("Could not probe audio duration, using estimate: %s", exc)
        return fallback


def _build_ffmpeg_cmd(idea_id: str, duration: float) -> list[str]:
    """Build the Windows-safe FFmpeg render command."""

    idea = db.get_idea(idea_id)
    script = db.get_script(idea_id)
    if idea is None:
        raise ValueError(f"Idea not found: {idea_id}")
    if script is None:
        raise ValueError(f"Script not found: {idea_id}")

    audio_path = Path("outputs") / "audio" / f"{idea_id}.mp3"
    output_path = Path("outputs") / "videos" / f"{idea_id}.mp4"
    background_path = Path("assets") / "backgrounds" / f"{idea_id}.mp4"
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filters = [
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        _drawtext(idea.title, "200", 48),
        _drawtext(script.hook, "360", 44),
        *_caption_drawtext_filters(script, duration),
    ]
    command = [
        settings.ffmpeg_path,
        "-y",
        *_video_input_args(background_path, duration),
        "-i",
        str(audio_path),
        "-t",
        f"{duration:.2f}",
        "-vf",
        ",".join(filters),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    return command


def render_video(idea_id: str) -> Path:
    """Render a vertical MP4 for an idea using FFmpeg."""

    _check_ffmpeg()
    script = db.get_script(idea_id)
    if script is None:
        raise ValueError(f"Script not found: {idea_id}")
    audio_path = Path("outputs") / "audio" / f"{idea_id}.mp3"
    duration = _probe_audio_duration(audio_path, estimate_duration_seconds(script.full_text))
    subtitle_path = Path("outputs") / "subtitles" / f"{idea_id}.srt"
    if not subtitle_path.exists():
        captions.generate_srt(script, duration, subtitle_path)
    command = _build_ffmpeg_cmd(idea_id, duration)
    logger.debug("Running FFmpeg render command: %s", command)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg render failed: %s", result.stderr)
        raise RuntimeError("FFmpeg render failed. See data/logs/pipeline.log for stderr.")
    output_path = Path("outputs") / "videos" / f"{idea_id}.mp4"
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg did not produce a playable file at {output_path}")
    return output_path


def render_color_video(audio_path: Path, output_path: Path, seconds: int | None = None) -> Path:
    """Render a basic vertical video with an audio track using FFmpeg."""

    _check_ffmpeg()
    duration = seconds or settings.default_video_seconds
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        settings.ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x101820:s=1080x1920:d={duration}:r=30",
        "-i",
        str(audio_path),
        "-shortest",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(output_path),
    ]
    logger.debug("Running FFmpeg color render command: %s", command)
    subprocess.run(command, check=True)
    return output_path
