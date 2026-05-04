"""Pydantic models for ideas, scripts, packages, and analytics."""

from datetime import date, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

PRIMARY_STATUSES = {
    "Backlog",
    "Approved",
    "Scripted",
    "Voiceover Done",
    "Rendered",
    "Ready to Post",
    "Posted",
    "Winner",
    "Loser",
    "Repurpose",
    "Killed",
    "Needs Review",
}
SUB_STATUSES = {"pending", "done", "failed"}


class Idea(BaseModel):
    """A content idea tracked across Sheets and the local database."""

    idea_id: str = Field(default_factory=lambda: str(uuid4()))
    date_added: date = Field(default_factory=date.today)
    source: str = "generated"
    source_url: str = ""
    content_pillar: str
    target_viewer: str
    viewer_pain: str
    title: str
    hook: str
    script_outline: str = ""
    suggested_visuals: str = ""
    tools_needed: str = ""
    monetization_angle: str = ""
    CTA: str = "Follow for one AI workflow a day."
    platform_primary: str = "youtube_shorts"
    platform_secondary: str = "instagram_reels"
    ideal_length_seconds: int = 45
    difficulty_score: int = Field(default=3, ge=1, le=5)
    novelty_score: int = Field(default=3, ge=1, le=5)
    monetization_score: int = Field(default=3, ge=1, le=5)
    production_speed_score: int = Field(default=3, ge=1, le=5)
    risk_score: int = Field(default=3, ge=1, le=5)
    status: str = "Backlog"
    assigned_to: str = ""
    due_date: str = ""
    script_status: str = "pending"
    voiceover_status: str = "pending"
    video_status: str = "pending"
    notes: str = ""

    model_config = ConfigDict(extra="ignore")

    @computed_field
    @property
    def total_score(self) -> float:
        """Calculate the weighted score used for prioritizing production."""

        return round(
            (self.novelty_score * 0.30)
            + (self.monetization_score * 0.25)
            + (self.production_speed_score * 0.25)
            + ((6 - self.difficulty_score) * 0.10)
            + ((6 - self.risk_score) * 0.10),
            2,
        )

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Validate the primary workflow status."""

        if value not in PRIMARY_STATUSES:
            raise ValueError(f"status must be one of {sorted(PRIMARY_STATUSES)}")
        return value

    @field_validator("script_status", "voiceover_status", "video_status")
    @classmethod
    def validate_sub_status(cls, value: str) -> str:
        """Validate a per-step completion status."""

        if value not in SUB_STATUSES:
            raise ValueError(f"sub-status must be one of {sorted(SUB_STATUSES)}")
        return value


class Script(BaseModel):
    """A structured short-form script for one idea."""

    idea_id: str
    hook: str
    problem: str
    old_way: str
    steps: list[str] = Field(min_length=3, max_length=3)
    caveat: str
    cta: str

    @computed_field
    @property
    def full_text(self) -> str:
        """Join all script sections into narration text."""

        sections = [
            self.hook,
            self.problem,
            self.old_way,
            *self.steps,
            self.caveat,
            self.cta,
        ]
        return "\n".join(section.strip() for section in sections if section.strip())

    @computed_field
    @property
    def word_count(self) -> int:
        """Count words in the generated narration."""

        return len(self.full_text.split())


class PlatformPackage(BaseModel):
    """Caption and upload metadata for a platform package."""

    idea_id: str
    platform: Literal["youtube", "tiktok", "instagram"]
    title: str
    caption: str
    hashtags: list[str]
    cta: str
    upload_notes: str


class AnalyticsEvent(BaseModel):
    """A local analytics event captured for later reporting."""

    idea_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any]
