from pathlib import Path

from fastapi.testclient import TestClient

from postmortem_shield.api.main import app

SAMPLE = Path("samples/postmortems/payment-api-latency.md")


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_endpoint() -> None:
    client = TestClient(app)
    payload = {
        "postmortem_text": SAMPLE.read_text(encoding="utf-8"),
        "source_file": "payment-api-latency.md",
        "provider": "mock",
    }
    response = client.post("/generate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["incident"]["incident_id"] == "pm-2026-03-11-payment-api"
    assert len(body["artifacts"]) == 4
