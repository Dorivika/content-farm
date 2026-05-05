"""Gemini image generation for workflow step mockups."""

from pathlib import Path

from src.logger import get_logger
from src.models import Idea, Script
from src.settings import settings

logger = get_logger(__name__)


def _tool_name(idea: Idea) -> str:
    """Extract the primary tool name from an idea."""

    return (idea.tools_needed.split(",")[0] or "AI workflow").strip()


def _save_response_image(response, output_path: Path) -> bool:
    """Save the first image part from a Gemini response."""

    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
        parts = response.candidates[0].content.parts
    for part in parts or []:
        if getattr(part, "inline_data", None) is not None:
            output_path.write_bytes(part.inline_data.data)
            return True
        if hasattr(part, "as_image"):
            part.as_image().save(output_path)
            return True
    return False


def _generate_image(prompt: str, output_path: Path) -> bool:
    """Generate one image with Gemini and save it."""

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    )
    response = client.models.generate_content(
        model=settings.gemini_image_model,
        contents=[prompt],
        config=config,
    )
    return _save_response_image(response, output_path)


def generate_step_images(idea: Idea, script: Script) -> list[Path]:
    """Generate mockup-style images for each workflow step."""

    if settings.offline_mode or not settings.gemini_api_key:
        return []
    output_dir = Path("outputs") / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, step in enumerate(script.steps, start=1):
        output_path = output_dir / f"{idea.idea_id}_step_{index}.png"
        if output_path.exists():
            paths.append(output_path)
            continue
        prompt = (
            f"Clean minimal screenshot of {_tool_name(idea)} dashboard showing {step}, "
            "dark UI theme, 1080x1920, realistic SaaS interface, no people"
        )
        try:
            if _generate_image(prompt, output_path):
                paths.append(output_path)
        except Exception as exc:
            logger.warning("Gemini image generation failed for step %s: %s", index, exc)
    return paths
