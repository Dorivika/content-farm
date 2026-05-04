"""Export helpers for human-reviewed platform packages."""

import json
from pathlib import Path

from src.models import PlatformPackage


def save_package(package: PlatformPackage, output_dir: Path) -> Path:
    """Write a platform package JSON file for manual upload."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{package.idea_id}_{package.platform}.json"
    output_path.write_text(
        json.dumps(package.model_dump(mode="json"), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return output_path
