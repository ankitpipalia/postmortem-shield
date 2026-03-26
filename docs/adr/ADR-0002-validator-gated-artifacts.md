# ADR-0002: Validator-Gated Artifact Delivery

## Status
Accepted (2026-03-26)

## Context
Generated prevention artifacts are only useful if they pass basic operational checks. Many environments may not have `promtool`, `opa`, `conftest`, or `kubectl` installed.

## Decision
Run tool-based validation when binaries are available. Fall back to deterministic structural validation otherwise. Every artifact carries a `validation` status in the bundle.

## Consequences
- Pros: works offline, still enforces quality gates, easy to demo.
- Cons: fallback checks are weaker than full runtime validators.
