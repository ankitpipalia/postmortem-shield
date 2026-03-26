from __future__ import annotations

import shutil
import subprocess
import tempfile

import yaml

from postmortem_shield.models.artifact import ArtifactType, ValidationResult


def _required_keys_check(parsed: dict, artifact_type: ArtifactType) -> ValidationResult:
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
        messages=["YAML structural checks passed (kubectl not found)."],
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
        output = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
        return ValidationResult(
            artifact_type=artifact_type,
            validator="kubectl --dry-run=client",
            ok=result.returncode == 0,
            messages=output or ["kubectl returned no output"],
        )

    try:
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise ValueError("YAML root must be a mapping")
        return _required_keys_check(parsed, artifact_type)
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            artifact_type=artifact_type,
            validator="yaml-structure",
            ok=False,
            messages=[f"YAML validation failed: {exc}"],
        )
