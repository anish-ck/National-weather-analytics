from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class EventType(StrEnum):
    HEAVY_RAINFALL = "HEAVY_RAINFALL"; FLOOD = "FLOOD"; THUNDERSTORM = "THUNDERSTORM"
    LIGHTNING = "LIGHTNING"; CYCLONE = "CYCLONE"; HEATWAVE = "HEATWAVE"; COLDWAVE = "COLDWAVE"
    FOG = "FOG"; DUST_STORM = "DUST_STORM"; STRONG_WIND = "STRONG_WIND"; LANDSLIDE = "LANDSLIDE"
    DROUGHT = "DROUGHT"; OTHER = "OTHER"


class Verdict(StrEnum):
    SUPPORTED = "SUPPORTED"; REFUTED = "REFUTED"; MISLEADING = "MISLEADING"; UNCERTAIN = "UNCERTAIN"


class ReportCreate(BaseModel):
    text: str = Field(min_length=4, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType = EventType.OTHER
    image_url: str | None = Field(default=None, max_length=2048)
    location_name: str | None = Field(default=None, max_length=255)

    @field_validator("text")
    @classmethod
    def text_is_useful(cls, value: str) -> str:
        return " ".join(value.split())


class EvidenceOut(BaseModel):
    source: str; title: str; content: str; similarity_score: float | None = None; rerank_score: float | None = None


class EventOut(BaseModel):
    event_id: UUID; source: str; event_type: EventType; description: str
    latitude: float | None; longitude: float | None; location_name: str | None
    state: str | None; district: str | None; timestamp: datetime
    verification_status: Verdict; confidence_score: float; verification_reason: str
    image_url: str | None = None; evidence: list[EvidenceOut] = []


class AdminVerification(BaseModel):
    verdict: Verdict
    reviewer: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=3, max_length=2000)


class ReportAccepted(BaseModel):
    event_id: UUID; status: str = "queued"


class VerificationRequest(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    source: str = "CITIZEN"
    text: str
    event_type: EventType = EventType.OTHER
    latitude: float | None = None; longitude: float | None = None
    location_name: str | None = None; timestamp: datetime
    image_url: str | None = None
    metadata: dict[str, Any] = {}
