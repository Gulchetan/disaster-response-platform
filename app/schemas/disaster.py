import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.db.models import DisasterStatus


class DisasterCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: DisasterStatus = DisasterStatus.active

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return [t.strip().lower() for t in v if t.strip()]


class DisasterUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=5000)
    tags: list[str] | None = Field(None, max_length=20)
    status: DisasterStatus | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return [t.strip().lower() for t in v if t.strip()]


class DisasterResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    location_name: str | None
    latitude: float | None
    longitude: float | None
    tags: list[str]
    status: DisasterStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    latitude: float
    longitude: float
    distance_km: float


class ReportResponse(BaseModel):
    content: str
    user: str
    created_at: str
    source: Literal["cache", "external"] = "external"
