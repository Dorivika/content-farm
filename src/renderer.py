"""FFmpeg rendering helpers for simple vertical videos."""

import subprocess
from pathlib import Path

from src.settings import settings


def render_color_video(audio_path: Path, output_path: Path, seconds: int | None = None) -> Path:
    """Render a basic vertical video with an audio track using FFmpeg."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = seconds or settings.default_video_seconds
    command = [
        settings.ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x101820:s=1080x1920:d={duration}",
        "-i",
        str(audio_path),
        "-shortest",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(output_path),
    ]
    subprocess.run(command, check=True)
    return output_path
