from pathlib import Path

from postmortem_shield.models.artifact import ArtifactType
from postmortem_shield.pipeline import ShieldPipeline

SAMPLE = Path("samples/postmortems/payment-api-latency.md")


def test_pipeline_generates_artifacts_and_traceability(tmp_path: Path) -> None:
    bundle = ShieldPipeline(provider_name="mock").run(SAMPLE, tmp_path)

    assert len(bundle.artifacts) == 4
    assert {artifact.artifact_type for artifact in bundle.artifacts} == {
        ArtifactType.PROMETHEUS_ALERTS,
        ArtifactType.KYVERNO_POLICY,
        ArtifactType.CHAOS_MANIFEST,
        ArtifactType.OPA_POLICY,
    }

    for artifact in bundle.artifacts:
        assert artifact.validation is not None
        assert artifact.validation.ok

    generated_dir = tmp_path / bundle.incident.incident_id
    assert (generated_dir / "prometheus-rules.yaml").exists()
    assert (generated_dir / "traceability.json").exists()


def test_bundle_summary_is_deterministic(tmp_path: Path) -> None:
    pipeline = ShieldPipeline(provider_name="mock")

    first_bundle = pipeline.run(SAMPLE, tmp_path)
    summary_path = tmp_path / first_bundle.incident.incident_id / "bundle-summary.json"
    first_summary = summary_path.read_text(encoding="utf-8")

    pipeline.run(SAMPLE, tmp_path)
    second_summary = summary_path.read_text(encoding="utf-8")

    assert first_summary == second_summary
