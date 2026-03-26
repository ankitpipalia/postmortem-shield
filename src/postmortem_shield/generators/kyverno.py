from __future__ import annotations

import yaml

from postmortem_shield.models.artifact import ArtifactType, GeneratedArtifact
from postmortem_shield.models.incident import Incident


def _rule_pattern(component: str) -> dict[str, object]:
    return {
        "metadata": {
            "labels": {
                "app.kubernetes.io/name": component,
            }
        },
        "spec": {
            "containers": [
                {
                    "(name)": "*",
                    "resources": {
                        "requests": {
                            "cpu": "?*",
                            "memory": "?*",
                        },
                        "limits": {
                            "cpu": "?*",
                            "memory": "?*",
                        },
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "?*",
                            "port": "?*",
                        }
                    },
                }
            ]
        },
    }


def generate_kyverno_policy(incident: Incident) -> GeneratedArtifact:
    rules = []
    for finding in incident.findings:
        rules.append(
            {
                "name": f"enforce-guardrails-{finding.id.lower()}",
                "match": {
                    "any": [
                        {
                            "resources": {
                                "kinds": ["Pod"],
                            }
                        }
                    ]
                },
                "validate": {
                    "message": (
                        f"Finding {finding.id}: {finding.title}. "
                        f"Trace: postmortem://{incident.incident_id}#{finding.id}"
                    ),
                    "pattern": _rule_pattern(finding.impacted_component),
                },
            }
        )

    payload = {
        "apiVersion": "kyverno.io/v1",
        "kind": "ClusterPolicy",
        "metadata": {
            "name": f"shield-{incident.incident_id}",
            "annotations": {
                "postmortem-shield/incident": incident.incident_id,
                "postmortem-shield/findings": ",".join(f.id for f in incident.findings),
            },
        },
        "spec": {
            "validationFailureAction": "Audit",
            "background": True,
            "rules": rules,
        },
    }

    content = yaml.safe_dump(payload, sort_keys=False)
    return GeneratedArtifact(
        artifact_type=ArtifactType.KYVERNO_POLICY,
        filename="kyverno-policy.yaml",
        content=content,
        finding_ids=[f.id for f in incident.findings],
        metadata={"traceability": [f"{incident.incident_id}#{f.id}" for f in incident.findings]},
    )
