from __future__ import annotations

from postmortem_shield.models.artifact import ArtifactType, GeneratedArtifact
from postmortem_shield.models.incident import Incident


def _deny_rule(incident_id: str, finding_id: str, title: str, component: str) -> str:
    message = (
        f"{finding_id} ({title}): deployment {component} must define resources and probes "
        f"[trace=postmortem://{incident_id}#{finding_id}]"
    )
    return f"""deny[msg] {{
  input.kind == \"Deployment\"
  input.metadata.labels[\"app.kubernetes.io/name\"] == \"{component}\"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.cpu
  msg := \"{message}\"
}}
"""


def generate_opa_policy(incident: Incident) -> GeneratedArtifact:
    package_name = incident.incident_id.replace("-", "_")
    parts = [
        f"package postmortem_shield.{package_name}",
        "",
        "default deny = []",
        "",
    ]

    for finding in incident.findings:
        parts.append(f"# Finding {finding.id}: {finding.evidence}")
        parts.append(
            _deny_rule(
                incident.incident_id,
                finding.id,
                finding.title,
                finding.impacted_component,
            )
        )

    content = "\n".join(parts).strip() + "\n"

    return GeneratedArtifact(
        artifact_type=ArtifactType.OPA_POLICY,
        filename="policy.rego",
        content=content,
        finding_ids=[f.id for f in incident.findings],
        metadata={
            "format": "opa_rego",
            "traceability": [f"{incident.incident_id}#{f.id}" for f in incident.findings],
        },
    )
