from __future__ import annotations

import shutil
import subprocess
import tempfile

import yaml

from postmortem_shield.models.artifact import ArtifactType, ValidationResult

_CLUSTER_UNREACHABLE_MARKERS = (
    "connection refused",
    "couldn't get current server API group list",
    "Unable to connect to the server",
    "no configuration has been provided",
)


def _required_keys_check(
    parsed: dict, artifact_type: ArtifactType, reason: str = "kubectl not found"
) -> ValidationResult:
    required = ["apiVersion", "kind", "metadata", "spec"]
    missing = [key for key in required if key not in parsed]
    if missing:
        return ValidationResult(
            artifact_type=artifact_type,
            validator="yaml-structure",
            ok=False,
            messages=[f"missing required keys: {', '.join(missing)}"],
        )

    if artifact_type == ArtifactType.KYVERNO_POLICY and parsed.get("kind") != "ClusterPolicy":
        return ValidationResult(
            artifact_type=artifact_type,
            validator="yaml-structure",
            ok=False,
            messages=["kyverno artifact kind must be ClusterPolicy"],
        )
    if artifact_type == ArtifactType.CHAOS_MANIFEST and parsed.get("kind") != "ChaosEngine":
        return ValidationResult(
            artifact_type=artifact_type,
            validator="yaml-structure",
            ok=False,
            messages=["chaos artifact kind must be ChaosEngine"],
        )

    return ValidationResult(
        artifact_type=artifact_type,
        validator="yaml-structure",
        ok=True,
        messages=[f"YAML structural checks passed ({reason})."],
    )


def _structural_fallback(
    content: str, artifact_type: ArtifactType, reason: str
) -> ValidationResult:
    try:
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise ValueError("YAML root must be a mapping")
        return _required_keys_check(parsed, artifact_type, reason=reason)
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            artifact_type=artifact_type,
            validator="yaml-structure",
            ok=False,
            messages=[f"YAML validation failed: {exc}"],
        )


def validate_kubernetes_yaml(content: str, artifact_type: ArtifactType) -> ValidationResult:
    kubectl = shutil.which("kubectl")
    if kubectl:
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(content)
            path = handle.name
        result = subprocess.run(
            [kubectl, "apply", "--dry-run=client", "--validate=false", "-f", path],
            capture_output=True,
            text=True,
            check=False,
        )
        combined = result.stdout + result.stderr
        if result.returncode != 0 and any(
            marker in combined for marker in _CLUSTER_UNREACHABLE_MARKERS
        ):
            # kubectl exists but has no cluster to talk to (client dry-run still
            # performs API discovery). Fall back to structural checks with a
            # deterministic message instead of failing on environment state.
            return _structural_fallback(
                content, artifact_type, reason="kubectl present but no cluster reachable"
            )
        combined = combined.replace(path, "manifest.yaml")
        output = [line for line in combined.splitlines() if line.strip()]
        return ValidationResult(
            artifact_type=artifact_type,
            validator="kubectl --dry-run=client",
            ok=result.returncode == 0,
            messages=output or ["kubectl returned no output"],
        )

    return _structural_fallback(content, artifact_type, reason="kubectl not found")
