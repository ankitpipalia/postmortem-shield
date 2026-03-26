from __future__ import annotations

import yaml

from postmortem_shield.models.artifact import ArtifactType, GeneratedArtifact
from postmortem_shield.models.incident import Finding, Incident


def _alert_expr(finding: Finding, service_hint: str) -> str:
    signal = finding.signal.lower()
    component = finding.impacted_component
    service = component or service_hint
    if "latency" in signal:
        return (
            "histogram_quantile(0.95, "
            f"sum(rate(http_request_duration_seconds_bucket{{service=\"{service}\"}}[5m])) "
            "by (le)) > 0.75"
        )
    if "error" in signal or "availability" in signal:
        return (
            f"sum(rate(http_requests_total{{service=\"{service}\",status=~\"5..\"}}[5m])) "
            f"/ sum(rate(http_requests_total{{service=\"{service}\"}}[5m])) > 0.03"
        )
    if "cpu" in signal:
        return (
            f"avg(rate(container_cpu_usage_seconds_total{{pod=~\"{service}.*\"}}[5m])) "
            "> 0.8"
        )
    return f"increase(shield_finding_events_total{{finding_id=\"{finding.id}\"}}[15m]) > 0"


def _for_duration(severity: str) -> str:
    if severity == "critical":
        return "1m"
    if severity == "high":
        return "2m"
    if severity == "medium":
        return "5m"
    return "10m"


def generate_prometheus_rules(incident: Incident) -> GeneratedArtifact:
    service_hint = incident.services[0] if incident.services else "platform"

    rules: list[dict[str, object]] = []
    for finding in incident.findings:
        rules.append(
            {
                "alert": f"PostmortemShield{finding.id}",
                "expr": _alert_expr(finding, service_hint),
                "for": _for_duration(finding.severity),
                "labels": {
                    "severity": finding.severity,
                    "incident_id": incident.incident_id,
                    "finding_id": finding.id,
                },
                "annotations": {
                    "summary": finding.title,
                    "description": finding.evidence,
                    "traceability": f"postmortem://{incident.incident_id}#{finding.id}",
                },
            }
        )

    payload = {
        "groups": [
            {
                "name": f"postmortem-shield.{incident.incident_id}",
                "rules": rules,
            }
        ]
    }
    content = yaml.safe_dump(payload, sort_keys=False)

    return GeneratedArtifact(
        artifact_type=ArtifactType.PROMETHEUS_ALERTS,
        filename="prometheus-rules.yaml",
        content=content,
        finding_ids=[f.id for f in incident.findings],
        metadata={
            "title": incident.title,
            "traceability": [
                f"{incident.incident_id}#{finding.id}" for finding in incident.findings
            ],
        },
    )
