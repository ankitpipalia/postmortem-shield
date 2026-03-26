from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from postmortem_shield.extractors import extract_incident
from postmortem_shield.generators import (
    generate_chaos_manifest,
    generate_kyverno_policy,
    generate_opa_policy,
    generate_prometheus_rules,
)
from postmortem_shield.models.artifact import ArtifactType, GeneratedArtifact, ShieldBundle
from postmortem_shield.models.incident import Incident
from postmortem_shield.providers import get_provider
from postmortem_shield.validators import (
    validate_kubernetes_yaml,
    validate_opa_policy,
    validate_prometheus_rules,
)


class ShieldPipeline:
    def __init__(self, provider_name: str = "mock") -> None:
        self.provider = get_provider(provider_name)

    def run(
        self,
        postmortem_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> ShieldBundle:
        source = Path(postmortem_path)
        raw_text = source.read_text(encoding="utf-8")
        return self.run_from_text(raw_text, source_file=str(source), output_dir=output_dir)

    def run_from_text(
        self,
        postmortem_text: str,
        source_file: str = "inline",
        output_dir: str | Path | None = None,
    ) -> ShieldBundle:
        incident = extract_incident(postmortem_text, source_file=source_file)
        artifacts = self._generate_artifacts(incident)

        for artifact in artifacts:
            artifact.validation = self._validate_artifact(artifact)
            artifact.metadata["provider"] = self.provider.name
            artifact.metadata["provider_fingerprint"] = self.provider.complete(
                "artifact-generation",
                f"{incident.incident_id}:{artifact.artifact_type.value}",
            )

        bundle = ShieldBundle(
            incident=incident,
            artifacts=artifacts,
            traceability=self._build_traceability(incident, artifacts),
            generated_at=datetime.now(tz=UTC),
        )

        if output_dir is not None:
            self.write_bundle(bundle, output_dir)
        return bundle

    def write_bundle(self, bundle: ShieldBundle, output_root: str | Path) -> Path:
        output_base = Path(output_root) / bundle.incident.incident_id
        output_base.mkdir(parents=True, exist_ok=True)

        for artifact in bundle.artifacts:
            (output_base / artifact.filename).write_text(artifact.content, encoding="utf-8")

        (output_base / "incident.json").write_text(
            json.dumps(bundle.incident.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        (output_base / "traceability.json").write_text(
            json.dumps(bundle.traceability, indent=2),
            encoding="utf-8",
        )
        normalized_generated_at = bundle.incident.occurred_at or datetime(1970, 1, 1, tzinfo=UTC)
        summary_payload = bundle.model_dump(mode="json")
        summary_payload["generated_at"] = normalized_generated_at.isoformat()
        (output_base / "bundle-summary.json").write_text(
            json.dumps(summary_payload, indent=2),
            encoding="utf-8",
        )
        return output_base

    def _generate_artifacts(self, incident: Incident) -> list[GeneratedArtifact]:
        return [
            generate_prometheus_rules(incident),
            generate_kyverno_policy(incident),
            generate_chaos_manifest(incident),
            generate_opa_policy(incident),
        ]

    def _validate_artifact(self, artifact: GeneratedArtifact):
        if artifact.artifact_type == ArtifactType.PROMETHEUS_ALERTS:
            return validate_prometheus_rules(artifact.content)
        if artifact.artifact_type == ArtifactType.OPA_POLICY:
            return validate_opa_policy(artifact.content)
        if artifact.artifact_type in {ArtifactType.KYVERNO_POLICY, ArtifactType.CHAOS_MANIFEST}:
            return validate_kubernetes_yaml(artifact.content, artifact.artifact_type)
        raise ValueError(f"No validator for artifact type: {artifact.artifact_type}")

    def _build_traceability(
        self,
        incident: Incident,
        artifacts: list[GeneratedArtifact],
    ) -> dict[str, list[dict[str, str]]]:
        finding_lookup = {finding.id: finding for finding in incident.findings}
        traceability: dict[str, list[dict[str, str]]] = {}

        for artifact in artifacts:
            links = []
            for finding_id in artifact.finding_ids:
                finding = finding_lookup[finding_id]
                links.append(
                    {
                        "finding_id": finding.id,
                        "title": finding.title,
                        "evidence": finding.evidence,
                        "component": finding.impacted_component,
                        "trace": f"postmortem://{incident.incident_id}#{finding.id}",
                    }
                )
            traceability[artifact.filename] = links

        return traceability
