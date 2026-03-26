# Postmortem Shield Knowledge

## Core problem
Postmortems often produce useful findings but fail to become enforceable controls. Postmortem Shield closes that gap by converting findings into prevention artifacts that can be validated and shipped.

## Pipeline stages
1. Deterministic extraction
- Input: markdown postmortem with explicit sections.
- Output: strict `Incident` model with normalized findings.

2. Artifact generation
- Prometheus alert rules
- Kyverno ClusterPolicy
- LitmusChaos-style ChaosEngine skeleton
- OPA/Rego policy text

3. Validation
- Tool-backed validation when local binaries are available.
- Safe structured validation fallback for local environments.

4. Traceability
- Each artifact carries `postmortem://<incident_id>#<finding_id>` references.
- `traceability.json` maps generated files to source findings/evidence.

## Design assumptions
- Initial MVP optimizes deterministic and demoable output over language flexibility.
- Markdown schema is intentional to keep extraction stable and testable.
- Pluggable provider interface exists for future LLM-assisted extraction/generation paths.
