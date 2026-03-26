from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from postmortem_shield.models.artifact import ArtifactType, ValidationResult


def _structured_rego_validation(content: str) -> ValidationResult:
    messages: list[str] = []
    ok = True

    if not re.search(r"^package\s+", content, flags=re.MULTILINE):
        ok = False
        messages.append("missing package declaration")
    if "deny[" not in content and "deny [" not in content:
        ok = False
        messages.append("no deny rule found")
    if "postmortem://" not in content:
        ok = False
        messages.append("no traceability references found")

    if ok:
        messages.append("OPA-style policy structural checks passed (opa/conftest not found).")

    return ValidationResult(
        artifact_type=ArtifactType.OPA_POLICY,
        validator="structured",
        ok=ok,
        messages=messages,
    )


def validate_opa_policy(content: str) -> ValidationResult:
    opa = shutil.which("opa")
    if opa:
        with tempfile.NamedTemporaryFile("w", suffix=".rego", delete=False) as handle:
            handle.write(content)
            policy_path = handle.name
        result = subprocess.run(
            [opa, "check", policy_path],
            capture_output=True,
            text=True,
            check=False,
        )
        output = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
        return ValidationResult(
            artifact_type=ArtifactType.OPA_POLICY,
            validator="opa check",
            ok=result.returncode == 0,
            messages=output or ["opa check returned no output"],
        )

    conftest = shutil.which("conftest")
    if conftest:
        with tempfile.TemporaryDirectory() as temp_dir:
            policy_path = Path(temp_dir) / "policy.rego"
            input_path = Path(temp_dir) / "input.json"
            policy_path.write_text(content, encoding="utf-8")
            input_path.write_text(
                json.dumps(
                    {
                        "kind": "Deployment",
                        "metadata": {
                            "labels": {
                                "app.kubernetes.io/name": "safe-service",
                            }
                        },
                        "spec": {
                            "template": {
                                "spec": {
                                    "containers": [
                                        {
                                            "name": "app",
                                            "resources": {"limits": {"cpu": "100m"}},
                                        }
                                    ]
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [conftest, "test", str(input_path), "--policy", temp_dir],
                capture_output=True,
                text=True,
                check=False,
            )
        output = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
        return ValidationResult(
            artifact_type=ArtifactType.OPA_POLICY,
            validator="conftest",
            ok=result.returncode == 0,
            messages=output or ["conftest returned no output"],
        )

    return _structured_rego_validation(content)
