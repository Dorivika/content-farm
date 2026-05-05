"""Application settings loaded from environment variables."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Typed configuration values for the local automation pipeline."""

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    google_sheet_id: str = Field(default="", alias="GOOGLE_SHEET_ID")
    google_sheet_tab: str = Field(default="Ideas", alias="GOOGLE_SHEET_TAB")
    google_credentials_path: Path = Field(
        default=Path("config/service_account.json"),
        alias="GOOGLE_CREDENTIALS_PATH",
    )
    tts_voice: str = Field(default="en-US-GuyNeural", alias="TTS_VOICE")
    backlog_minimum: int = Field(default=20, alias="BACKLOG_MINIMUM")
    ideas_to_generate: int = Field(default=50, alias="IDEAS_TO_GENERATE")
    default_video_seconds: int = Field(default=45, alias="DEFAULT_VIDEO_SECONDS")
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    offline_mode: bool = Field(default=False, alias="OFFLINE_MODE")
    gemini_deep_research_agent: str = Field(
        default="deep-research-preview-04-2026",
        alias="GEMINI_DEEP_RESEARCH_AGENT",
    )
    deep_research_timeout_seconds: int = Field(
        default=1800,
        alias="DEEP_RESEARCH_TIMEOUT_SECONDS",
    )
    deep_research_poll_seconds: int = Field(
        default=10,
        alias="DEEP_RESEARCH_POLL_SECONDS",
    )
    performance_history_limit: int = Field(default=50, alias="PERFORMANCE_HISTORY_LIMIT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
