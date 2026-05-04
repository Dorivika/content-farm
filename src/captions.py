"""Caption and subtitle helpers for generated scripts."""

from src.models import Script


def build_plain_caption(script: Script, max_chars: int = 140) -> str:
    """Create a short caption from the script hook and CTA."""

    caption = f"{script.hook} {script.cta}".strip()
    return caption[: max_chars - 3].rstrip() + "..." if len(caption) > max_chars else caption


def build_srt(script: Script, seconds_per_line: int = 4) -> str:
    """Create a simple SRT subtitle file from script sections."""

    lines = [line for line in script.full_text.splitlines() if line.strip()]
    blocks = []
    for index, line in enumerate(lines, start=1):
        start = (index - 1) * seconds_per_line
        end = index * seconds_per_line
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"00:00:{start:02d},000 --> 00:00:{end:02d},000",
                    line,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"
