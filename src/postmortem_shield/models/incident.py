from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

FINDING_ID_PATTERN = re.compile(r"^F\d{3}$")


class TimelineEvent(BaseModel):
    timestamp: datetime | None = None
    description: str = Field(min_length=3)


class Finding(BaseModel):
    id: str
    title: str = Field(min_length=3)
    evidence: str = Field(min_length=3)
    impacted_component: str = Field(min_length=1)
    signal: str = Field(default="availability")
    severity: Literal["low", "medium", "high", "critical"] = "medium"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not FINDING_ID_PATTERN.match(value):
            raise ValueError("finding id must follow pattern F###")
        return value


class Incident(BaseModel):
    incident_id: str = Field(min_length=3)
    title: str = Field(min_length=3)
    source_file: str
    occurred_at: datetime | None = None
    summary: str = Field(min_length=3)
    impact: str = Field(min_length=3)
    services: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(min_length=1)
    timeline: list[TimelineEvent] = Field(default_factory=list)
