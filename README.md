# Postmortem Shield

Postmortem Shield turns incident postmortems into **validated preventive artifacts** with clear traceability to findings.

## Why this is different
- Deterministic incident schema extraction (Pydantic models) instead of ad-hoc summarization.
- Multi-artifact generation in one pass: Prometheus alerts, Kyverno policy, LitmusChaos skeleton, and OPA/Rego policy.
- Validator-gated output: artifacts are not marked usable until checks run.
- Works offline by default with a deterministic mock provider (no API keys required).

## 2-3 minute local demo
```bash
make setup
make demo
```

Generated output appears in `samples/generated/pm-2026-03-11-payment-api/` with:
- `prometheus-rules.yaml`
- `kyverno-policy.yaml`
- `chaos-engine.yaml`
- `policy.rego`
- `traceability.json`
- `bundle-summary.json`

## Project structure
```text
src/postmortem_shield/
  api/            FastAPI app
  extractors/     deterministic schema extraction
  generators/     artifact generators
  validators/     promtool/opa/kubectl wrappers + safe fallbacks
  models/         Pydantic incident + artifact models
  providers/      pluggable generation provider interface + mock provider
samples/
  postmortems/    sample incident inputs
  generated/      committed deterministic outputs
prompts/          domain prompts/templates in version control
docs/adr/         architecture decisions
deploy/helm/      Kubernetes Helm chart skeleton
```

## CLI usage
```bash
postmortem-shield generate --input samples/postmortems/payment-api-latency.md --output samples/generated
postmortem-shield demo
postmortem-shield serve --port 8000
```

## API usage
Start server:
```bash
postmortem-shield serve --reload
```

Generate via API:
```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d @- <<'JSON'
{
  "provider": "mock",
  "source_file": "payment-api-latency.md",
  "postmortem_text": "---\nincident_id: demo-001\ntitle: Demo Incident\n---\n\n## Summary\nsummary\n\n## Impact\nimpact\n\n## Services\n- api\n\n## Root Causes\n- missing probe\n\n## Findings\n- [F001] Missing probe\n  - Evidence: startup failures\n  - Component: api\n  - Signal: error_rate\n  - Severity: high\n"
}
JSON
```

## Validation behavior
- Prometheus: uses `promtool check rules` if available, otherwise structural YAML checks.
- OPA policy: uses `opa check` or `conftest test` if available, otherwise structural Rego checks.
- Kubernetes YAML (Kyverno/Litmus): uses `kubectl apply --dry-run=client --validate=false` if available, otherwise structural YAML checks.

## CI
GitHub Actions runs lint, tests, and deterministic demo generation checks.

## Security
- No secrets required.
- No fake enterprise connectors.
- Offline deterministic mode is default.
