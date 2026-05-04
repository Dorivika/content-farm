"""Voiceover generation with edge-tts and FFmpeg silent fallback."""

import asyncio
import subprocess
from pathlib import Path

from src.logger import get_logger
from src.settings import settings

logger = get_logger(__name__)


def estimate_duration_seconds(text: str) -> float:
    """Estimate spoken audio duration from word count."""

    word_count = max(1, len(text.split()))
    return max(1.0, word_count / 2.5)


def _generate_silent_mp3(text: str, output_path: Path) -> Path:
    """Generate a silent MP3 placeholder with FFmpeg."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = estimate_duration_seconds(text)
    command = [
        settings.ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-t",
        f"{duration:.2f}",
        "-q:a",
        "9",
        str(output_path),
    ]
    logger.debug("Running FFmpeg silent audio command: %s", command)
    subprocess.run(command, check=True, capture_output=True, text=True)
    return output_path


async def generate_voiceover_async(text: str, output_path: Path) -> Path:
    """Generate an MP3 voiceover using edge-tts."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, settings.tts_voice)
        await communicate.save(str(output_path))
        return output_path
    except Exception as exc:
        logger.error("edge-tts failed: %s. Generating silent audio placeholder.", exc)
        return _generate_silent_mp3(text, output_path)


def generate_voiceover(text: str, output_path: Path) -> Path:
    """Generate an MP3 voiceover from sync code."""

    return asyncio.run(generate_voiceover_async(text, output_path))


async def synthesize_voiceover(text: str, output_path: Path, voice: str | None = None) -> Path:
    """Generate an MP3 voiceover file from narration text."""

    original_voice = settings.tts_voice
    if voice is not None:
        settings.tts_voice = voice
    try:
        return await generate_voiceover_async(text, output_path)
    finally:
        settings.tts_voice = original_voice
