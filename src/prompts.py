"""Helpers for loading prompt and YAML configuration files."""

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path("config")
PROMPT_DIR = CONFIG_DIR / "prompts"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return dict(data)


def load_account_config() -> dict[str, Any]:
    """Load account-level brand configuration."""

    return load_yaml(CONFIG_DIR / "account.yaml")


def load_niche_config() -> dict[str, Any]:
    """Load niche and content-pillar configuration."""

    return load_yaml(CONFIG_DIR / "niche.yaml")


def load_prompt(name: str) -> str:
    """Load a named Markdown prompt from config/prompts."""

    path = PROMPT_DIR / name
    if path.suffix != ".md":
        path = path.with_suffix(".md")
    return path.read_text(encoding="utf-8")
