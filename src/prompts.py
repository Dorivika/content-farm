"""Helpers for loading YAML config and Markdown prompt templates."""

from pathlib import Path
import re
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


def _template_path(template_name: str) -> Path:
    """Return the path for a Markdown prompt template."""

    path = PROMPT_DIR / template_name
    if path.suffix != ".md":
        path = path.with_suffix(".md")
    return path


def load_template(template_name: str) -> str:
    """Load a named Markdown prompt from config/prompts."""

    return _template_path(template_name).read_text(encoding="utf-8")


def load_prompt(name: str) -> str:
    """Load a named Markdown prompt from config/prompts."""

    return load_template(name)


def _resolve_variable(expression: str, variables: dict[str, Any]) -> str:
    """Resolve a simple dotted template expression."""

    value: Any = variables
    for part in expression.strip().split("."):
        if isinstance(value, dict):
            value = value.get(part, "")
        else:
            value = getattr(value, part, "")
    return str(value)


def _render_loops(template: str, variables: dict[str, Any]) -> str:
    """Render simple {% for item in items %} loop blocks."""

    pattern = re.compile(
        r"{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}",
        re.DOTALL,
    )

    def replace_loop(match: re.Match[str]) -> str:
        item_name, collection_name, body = match.groups()
        rendered = []
        for item in variables.get(collection_name, []):
            loop_vars = dict(variables)
            loop_vars[item_name] = item
            rendered.append(_render_variables(body, loop_vars))
        return "".join(rendered)

    return pattern.sub(replace_loop, template)


def _render_variables(template: str, variables: dict[str, Any]) -> str:
    """Render {{ variable }} placeholders in a template string."""

    return re.sub(
        r"{{\s*([^{}]+?)\s*}}",
        lambda match: _resolve_variable(match.group(1), variables),
        template,
    )


def render_template(template_name: str, variables: dict[str, Any]) -> str:
    """Render a Markdown prompt template with simple placeholder replacement."""

    template = load_template(template_name)
    return _render_variables(_render_loops(template, variables), variables)
