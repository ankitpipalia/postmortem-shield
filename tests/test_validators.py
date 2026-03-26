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

deny[msg] {
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
