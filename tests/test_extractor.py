from pathlib import Path

from postmortem_shield.extractors import extract_incident

SAMPLE = Path("samples/postmortems/payment-api-latency.md")


def test_extract_incident_schema() -> None:
    incident = extract_incident(SAMPLE.read_text(encoding="utf-8"), source_file=str(SAMPLE))

    assert incident.incident_id == "pm-2026-03-11-payment-api"
    assert incident.title == "Payment API latency spike during cache failover"
    assert len(incident.findings) == 3
    assert incident.findings[0].id == "F001"
    assert incident.findings[1].severity == "critical"
    assert incident.services == ["payment-api", "redis-cluster"]
