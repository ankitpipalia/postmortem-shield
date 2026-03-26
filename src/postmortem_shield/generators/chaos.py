from __future__ import annotations

import yaml

from postmortem_shield.models.artifact import ArtifactType, GeneratedArtifact
from postmortem_shield.models.incident import Incident


def _chaos_experiment_for_signal(signal: str) -> str:
    s = signal.lower()
    if "latency" in s:
        return "pod-network-latency"
    if "cpu" in s:
        return "pod-cpu-hog"
    return "pod-delete"


def generate_chaos_manifest(incident: Incident) -> GeneratedArtifact:
    service = incident.services[0] if incident.services else "platform"
    experiments: list[dict[str, object]] = []

    for finding in incident.findings:
        experiments.append(
            {
                "name": _chaos_experiment_for_signal(finding.signal),
                "spec": {
                    "components": {
                        "env": [
                            {
                                "name": "TOTAL_CHAOS_DURATION",
                                "value": "60",
                            },
                            {
                                "name": "RAMP_TIME",
                                "value": "15",
                            },
                            {
                                "name": "TRACEABILITY_REF",
                                "value": f"postmortem://{incident.incident_id}#{finding.id}",
                            },
                        ]
                    }
                },
            }
        )

    payload = {
        "apiVersion": "litmuschaos.io/v1alpha1",
        "kind": "ChaosEngine",
        "metadata": {
            "name": f"shield-{incident.incident_id}",
            "namespace": "litmus",
            "annotations": {
                "postmortem-shield/incident": incident.incident_id,
                "postmortem-shield/findings": ",".join(f.id for f in incident.findings),
            },
        },
        "spec": {
            "appinfo": {
                "appns": "default",
                "applabel": f"app={service}",
                "appkind": "deployment",
            },
            "chaosServiceAccount": "litmus-admin",
            "engineState": "active",
            "annotationCheck": "false",
            "experiments": experiments,
        },
    }

    content = yaml.safe_dump(payload, sort_keys=False)
    return GeneratedArtifact(
        artifact_type=ArtifactType.CHAOS_MANIFEST,
        filename="chaos-engine.yaml",
        content=content,
        finding_ids=[f.id for f in incident.findings],
        metadata={"traceability": [f"{incident.incident_id}#{f.id}" for f in incident.findings]},
    )
