# ADR-0001: Schema-First Deterministic Extraction

## Status
Accepted (2026-03-26)

## Context
Postmortem text quality varies, and free-form extraction makes downstream artifact generation brittle. We need deterministic behavior for a local demo and CI.

## Decision
Use a strict section-based markdown parser backed by Pydantic models (`Incident`, `Finding`, `TimelineEvent`). Generation is blocked if no valid findings are extracted.

## Consequences
- Pros: repeatable outputs, testable behavior, stable CI.
- Cons: requires postmortems to follow expected sections and finding format.
