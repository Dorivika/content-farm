"""Logging setup for console and rotating file output."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from src.settings import settings

LOG_PATH = Path("data") / "logs" / "pipeline.log"


def configure_logging() -> None:
    """Configure root logging once for Rich console and file output."""

    root = logging.getLogger()
    if getattr(root, "_content_farm_configured", False):
        return

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)
    root._content_farm_configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger using the shared application configuration."""

    configure_logging()
    return logging.getLogger(name)
