# Postmortem Shield Agent Notes

## Goal
Turn incident postmortems into validated preventive artifacts such as Kyverno policies, Prometheus alert rules, chaos experiment manifests, and policy checks.

## Conventions
- Keep outputs traceable back to source incident findings.
- Prefer deterministic schemas between pipeline stages.
- Validation must run before any generated artifact is marked usable.
