from postmortem_shield.models.artifact import ArtifactType
from postmortem_shield.validators.kubernetes import validate_kubernetes_yaml
from postmortem_shield.validators.policy import validate_opa_policy
from postmortem_shield.validators.prometheus import validate_prometheus_rules


def test_prometheus_structural_validation_passes() -> None:
    result = validate_prometheus_rules(
        """
groups:
  - name: demo
    rules:
      - alert: Example
        expr: vector(1)
        """
    )
    assert result.ok


def test_policy_structural_validation_passes() -> None:
    result = validate_opa_policy(
        """
package postmortem_shield.demo

import rego.v1

deny contains msg if {
  input.kind == \"Deployment\"
  msg := \"trace postmortem://demo#F001\"
}
        """
    )
    assert result.ok


def test_kubernetes_structural_validation_fails_missing_spec() -> None:
    result = validate_kubernetes_yaml(
        """
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: bad
        """,
        ArtifactType.KYVERNO_POLICY,
    )
    assert not result.ok


def test_kubernetes_falls_back_when_cluster_unreachable(monkeypatch) -> None:
    """kubectl on PATH but no cluster: validator must fall back to structural checks
    with a deterministic message instead of failing on environment state."""
    import subprocess
    from types import SimpleNamespace

    from postmortem_shield.validators import kubernetes as k8s_validator

    monkeypatch.setattr(k8s_validator.shutil, "which", lambda _: "/usr/local/bin/kubectl")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=(
                "E0710 memcache.go:265 couldn't get current server API group list: "
                "dial tcp [::1]:8080: connect: connection refused"
            ),
        ),
    )

    result = validate_kubernetes_yaml(
        """
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: ok
spec:
  rules: []
        """,
        ArtifactType.KYVERNO_POLICY,
    )
    assert result.ok
    assert result.validator == "yaml-structure"
    assert "no cluster reachable" in result.messages[0]
