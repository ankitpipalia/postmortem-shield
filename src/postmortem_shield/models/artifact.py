from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from postmortem_shield.models.incident import Incident


class ArtifactType(StrEnum):
    PROMETHEUS_ALERTS = "prometheus_alerts"
    KYVERNO_POLICY = "kyverno_policy"
    CHAOS_MANIFEST = "chaos_manifest"
    OPA_POLICY = "opa_policy"


class ValidationResult(BaseModel):
    artifact_type: ArtifactType
    validator: str
    ok: bool
    messages: list[str] = Field(default_factory=list)


class GeneratedArtifact(BaseModel):
    artifact_type: ArtifactType
    filename: str
    content: str
    finding_ids: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResult | None = None


class ShieldBundle(BaseModel):
    incident: Incident
    artifacts: list[GeneratedArtifact]
    traceability: dict[str, list[dict[str, str]]]
    generated_at: datetime
