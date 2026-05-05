"""Caption and subtitle helpers for generated scripts."""

import subprocess
from pathlib import Path

from src.logger import get_logger
from src.models import Script
from src.settings import settings

logger = get_logger(__name__)


def build_plain_caption(script: Script, max_chars: int = 140) -> str:
    """Create a short caption from the script hook and CTA."""

    caption = f"{script.hook} {script.cta}".strip()
    return caption[: max_chars - 3].rstrip() + "..." if len(caption) > max_chars else caption


def _format_timestamp(seconds: float) -> str:
    """Format seconds as an SRT timestamp."""

    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _segments(script: Script) -> list[str]:
    """Return script sections as subtitle segments."""

    return [
        script.hook,
        script.problem,
        script.old_way,
        *script.steps,
        script.caveat,
        script.cta,
    ]


def segment_timings(script: Script, audio_duration: float) -> list[tuple[str, float, float]]:
    """Estimate segment timings proportional to word count."""

    segments = [segment.strip() for segment in _segments(script) if segment.strip()]
    word_counts = [max(1, len(segment.split())) for segment in segments]
    total_words = max(1, sum(word_counts))
    cursor = 0.0
    timings = []
    for index, segment in enumerate(segments):
        if index == len(segments) - 1:
            end = max(cursor + 0.5, audio_duration)
        else:
            end = cursor + (audio_duration * word_counts[index] / total_words)
        timings.append((segment, cursor, end))
        cursor = end
    return timings


def generate_srt(script: Script, audio_duration: float, output_path: Path) -> Path:
    """Generate an SRT subtitle file from a structured script."""

    # TODO: Add faster-whisper integration for production-quality sync.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    for index, (segment, start, end) in enumerate(segment_timings(script, audio_duration), 1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_format_timestamp(start)} --> {_format_timestamp(end)}",
                    segment,
                ]
            )
        )
    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return output_path


def _pycaps_commands(audio_path: Path, output_path: Path) -> list[list[str]]:
    """Return possible pycaps CLI invocations."""

    return [
        [
            "python",
            "-m",
            "pycaps",
            str(audio_path),
            str(output_path),
            "--word-level",
            "--transparent",
        ],
        ["pycaps", str(audio_path), str(output_path), "--word-level", "--transparent"],
    ]


def generate_caption_overlay(audio_path: Path, output_path: Path) -> Path | None:
    """Generate an animated word-level caption overlay video with pycaps."""

    if settings.offline_mode:
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for command in _pycaps_commands(audio_path, output_path):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
        except FileNotFoundError:
            continue
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return output_path
        logger.warning("pycaps failed with command %s: %s", command, result.stderr)
    return None


def build_srt(script: Script, seconds_per_line: int = 4) -> str:
    """Create a simple SRT subtitle string from script sections."""

    duration = max(seconds_per_line, seconds_per_line * len(_segments(script)))
    blocks = []
    for index, (segment, start, end) in enumerate(segment_timings(script, duration), 1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_format_timestamp(start)} --> {_format_timestamp(end)}",
                    segment,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"
