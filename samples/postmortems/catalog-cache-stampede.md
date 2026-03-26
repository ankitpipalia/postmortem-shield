---
incident_id: pm-2026-02-07-catalog-cache
title: Catalog API cache stampede after deploy
occurred_at: 2026-02-07T14:05:00Z
---

## Summary
A deploy invalidated the catalog cache and caused synchronized misses, overwhelming the backing store.

## Impact
Search response time exceeded 2.5s p95 and error rate rose to 6% for 12 minutes.

## Services
- catalog-api
- memcached

## Root Causes
- Cache key versioning changed without gradual rollout.
- No request coalescing in miss path.

## Findings
- [F001] Missing coalescing in miss path amplified load.
  - Evidence: 4.2x DB QPS increase within 90 seconds after deploy.
  - Component: catalog-api
  - Signal: latency
  - Severity: high
- [F002] Cache invalidation lacked progressive strategy.
  - Evidence: 100% cache invalidation executed globally in one release step.
  - Component: memcached
  - Signal: availability
  - Severity: medium

## Timeline
- 2026-02-07T14:05:00Z | Deploy completed and cache warmup job started.
- 2026-02-07T14:08:00Z | DB saturation alert triggered.
- 2026-02-07T14:17:00Z | Rollback completed and latency normalized.
