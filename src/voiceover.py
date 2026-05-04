"""Voiceover generation using edge-tts."""

from pathlib import Path

from src.settings import settings


async def synthesize_voiceover(text: str, output_path: Path, voice: str | None = None) -> Path:
    """Generate an MP3 voiceover file from narration text."""

    import edge_tts

    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice or settings.tts_voice)
    await communicate.save(str(output_path))
    return output_path
