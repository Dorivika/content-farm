"""FFmpeg rendering helpers for vertical videos."""

import hashlib
import re
import subprocess
from pathlib import Path

from src import broll, captions, db, visual_generator
from src.logger import get_logger
from src.settings import settings
from src.voiceover import estimate_duration_seconds

logger = get_logger(__name__)


def _to_filter_path(path: Path) -> str:
    """Convert a path for use inside FFmpeg filter arguments."""

    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def _check_ffmpeg() -> None:
    """Ensure FFmpeg can be executed."""

    try:
        subprocess.run([settings.ffmpeg_path, "-version"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"FFmpeg not found at '{settings.ffmpeg_path}'. Install from "
            "https://ffmpeg.org and set FFMPEG_PATH in .env"
        ) from exc


def _textfile_path(text: str) -> str:
    """Write drawtext content to a text file and return its filter path."""

    clean = re.sub(r"[\r\n]+", " ", text)
    digest = hashlib.sha1(clean.encode("utf-8")).hexdigest()
    path = Path("outputs") / "packages" / "render_text" / f"{digest}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(clean, encoding="utf-8")
    return _to_filter_path(path)


def _font_filter_part() -> str:
    """Return an optional drawtext fontfile filter fragment."""

    fonts = list((Path("assets") / "fonts").glob("*.ttf"))
    if not fonts:
        fonts = list((Path("assets") / "fonts").glob("*.otf"))
    return f":fontfile={_to_filter_path(fonts[0])}" if fonts else ""


def _drawtext(text: str, y: str, size: int, enable: str = "") -> str:
    """Build one FFmpeg drawtext filter."""

    return (
        f"drawtext=textfile='{_textfile_path(text)}'{_font_filter_part()}:"
        f"fontsize={size}:fontcolor=white:box=1:boxcolor=black@0.45:"
        f"boxborderw=24:x=(w-text_w)/2:y={y}{enable}"
    )


def _probe_audio_duration(audio_path: Path, fallback: float) -> float:
    """Return actual audio duration using ffprobe when available."""

    try:
        result = subprocess.run(
            [
                "ffprobe",
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


def _keywords(idea, script) -> list[str]:
    """Derive b-roll keywords from idea and script metadata."""

    raw = [idea.content_pillar, idea.target_viewer, idea.title, idea.tools_needed, idea.suggested_visuals]
    raw.extend(script.steps)
    words = []
    for item in raw:
        words.extend(part.strip(" .") for part in re.split(r"[,;|]", item) if part.strip())
    return words[:8]


def _input_args(brolls: list[Path], images: list[Path], caption_overlay: Path | None) -> list[str]:
    """Build FFmpeg input arguments for generated assets."""

    args: list[str] = []
    for clip in brolls:
        args.extend(["-stream_loop", "-1", "-i", str(clip)])
    for image in images:
        args.extend(["-loop", "1", "-i", str(image)])
    if caption_overlay is not None:
        args.extend(["-i", str(caption_overlay)])
    return args


def _broll_filters(start_index: int, count: int, duration: float) -> tuple[list[str], str]:
    """Build sequential b-roll overlay filters."""

    filters = ["[0:v]format=yuv420p[bg0]"]
    current = "bg0"
    for index in range(count):
        start = index * 4.0
        end = min(duration, start + 4.0)
        src = start_index + index
        filters.append(f"[{src}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[br{index}]")
        filters.append(f"[{current}][br{index}]overlay=0:0:enable=between(t\\,{start:.2f}\\,{end:.2f})[bg{index + 1}]")
        current = f"bg{index + 1}"
    return filters, current


def _image_filters(start_index: int, images: list[Path], base: str, script, duration: float) -> tuple[list[str], str]:
    """Build workflow step image overlay filters."""

    filters = []
    current = base
    step_times = captions.segment_timings(script, duration)[3: 3 + len(images)]
    for index, (_, start, end) in enumerate(step_times):
        src = start_index + index
        filters.append(f"[{src}:v]scale=900:-1[img{index}]")
        filters.append(f"[{current}][img{index}]overlay=(W-w)/2:520:enable=between(t\\,{start:.2f}\\,{end:.2f})[im{index}]")
        current = f"im{index}"
    return filters, current


def _text_filters(base: str, idea, script, duration: float, use_fallback_captions: bool) -> tuple[list[str], str]:
    """Build hook and fallback caption drawtext filters."""

    draw_filters = [_drawtext(idea.title, "170", 48), _drawtext(script.hook, "330", 52, ":enable=between(t\\,0\\,3)")]
    if use_fallback_captions:
        for segment, start, end in captions.segment_timings(script, duration):
            draw_filters.append(_drawtext(segment, "h-360", 36, f":enable=between(t\\,{start:.2f}\\,{end:.2f})"))
    return [f"[{base}]{','.join(draw_filters)}[txt]"], "txt"


def _build_filter_complex(idea, script, duration: float, brolls: list[Path], images: list[Path], caption_overlay: Path | None) -> str:
    """Build the full FFmpeg filter graph."""

    filters, base = _broll_filters(2, len(brolls), duration)
    image_filters, base = _image_filters(2 + len(brolls), images, base, script, duration)
    filters.extend(image_filters)
    text_filters, base = _text_filters(base, idea, script, duration, caption_overlay is None)
    filters.extend(text_filters)
    if caption_overlay is not None:
        cap_index = 2 + len(brolls) + len(images)
        filters.append(f"[{cap_index}:v]scale=1080:1920[cap]")
        filters.append(f"[{base}][cap]overlay=0:0:format=auto[vout]")
    else:
        filters.append(f"[{base}]format=yuv420p[vout]")
    return ";".join(filters)


def render_video(idea_id: str) -> Path:
    """Render a vertical MP4 for an idea using FFmpeg."""

    _check_ffmpeg()
    idea = db.get_idea(idea_id)
    script = db.get_script(idea_id)
    if idea is None or script is None:
        raise ValueError(f"Idea or script not found: {idea_id}")
    audio_path = Path("outputs") / "audio" / f"{idea_id}.mp3"
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    duration = _probe_audio_duration(audio_path, estimate_duration_seconds(script.full_text))
    srt_path = captions.generate_srt(script, duration, Path("outputs") / "subtitles" / f"{idea_id}.srt")
    caption_overlay = captions.generate_caption_overlay(audio_path, Path("outputs") / "captions" / f"{idea_id}_captions.mov")
    brolls = broll.fetch_broll(_keywords(idea, script), count=5)
    images = visual_generator.generate_step_images(idea, script)
    output_path = Path("outputs") / "videos" / f"{idea_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        settings.ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x101820:s=1080x1920:d={duration:.2f}:r=30",
        "-i",
        str(audio_path),
        *_input_args(brolls, images, caption_overlay),
        "-filter_complex",
        _build_filter_complex(idea, script, duration, brolls, images, caption_overlay),
        "-map",
        "[vout]",
        "-map",
        "1:a:0",
        "-t",
        f"{duration:.2f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    logger.debug("Running FFmpeg render command: %s; subtitles=%s", command, srt_path)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg render failed: %s", result.stderr)
        raise RuntimeError("FFmpeg render failed. See data/logs/pipeline.log for stderr.")
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg did not produce a playable file at {output_path}")
    return output_path
