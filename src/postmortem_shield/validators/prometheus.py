from __future__ import annotations

import shutil
import subprocess
import tempfile

import yaml

from postmortem_shield.models.artifact import ArtifactType, ValidationResult


def validate_prometheus_rules(content: str) -> ValidationResult:
    promtool = shutil.which("promtool")
    if promtool:
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(content)
            rule_path = handle.name
        result = subprocess.run(
            [promtool, "check", "rules", rule_path],
            capture_output=True,
            text=True,
            check=False,
        )
        raw = (result.stdout + result.stderr).replace(rule_path, "prometheus-rules.yaml")
        messages = [line for line in raw.splitlines() if line.strip()]
        return ValidationResult(
            artifact_type=ArtifactType.PROMETHEUS_ALERTS,
            validator="promtool",
            ok=result.returncode == 0,
            messages=messages or ["promtool returned no output"],
        )

    try:
        parsed = yaml.safe_load(content)
        groups = parsed.get("groups", []) if isinstance(parsed, dict) else []
        if not groups:
            raise ValueError("missing groups")

        for group in groups:
            rules = group.get("rules", [])
            if not rules:
                raise ValueError(f"group {group.get('name', '<unnamed>')} has no rules")
            for rule in rules:
                if "alert" not in rule or "expr" not in rule:
                    raise ValueError("rule missing alert or expr")
        return ValidationResult(
            artifact_type=ArtifactType.PROMETHEUS_ALERTS,
            validator="static",
            ok=True,
            messages=["Prometheus rule schema checks passed (promtool not found)."],
        )
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            artifact_type=ArtifactType.PROMETHEUS_ALERTS,
            validator="static",
            ok=False,
            messages=[f"Prometheus schema validation failed: {exc}"],
        )
