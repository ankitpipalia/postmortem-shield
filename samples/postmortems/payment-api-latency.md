---
incident_id: pm-2026-03-11-payment-api
title: Payment API latency spike during cache failover
occurred_at: 2026-03-11T09:20:00Z
---

## Summary
A Redis primary failover increased upstream latency and surfaced weak deployment guardrails in the payment API tier.

## Impact
Checkout success rate dropped from 99.4% to 94.8% for 18 minutes, triggering customer-visible payment failures in two regions.

## Services
- payment-api
- redis-cluster

## Root Causes
- HPA max replicas cap was too low for failover burst traffic.
- Pods were considered ready before warm connections to Redis were established.
- Chaos drills for cache failover had not run in the previous quarter.

## Findings
- [F001] Autoscaling ceiling delayed recovery under burst traffic.
  - Evidence: HPA hit maxReplicas=12 for 11 minutes while p95 latency stayed above 900ms.
  - Component: payment-api
  - Signal: latency
  - Severity: high
- [F002] Readiness probes allowed stale Redis connections.
  - Evidence: 23% of restarted pods returned 5xx for the first two minutes after start.
  - Component: payment-api
  - Signal: error_rate
  - Severity: critical
- [F003] Cache failover chaos coverage was missing.
  - Evidence: No recorded game-day validating cache failover in the last 90 days.
  - Component: redis-cluster
  - Signal: availability
  - Severity: medium

## Timeline
- 2026-03-11T09:20:00Z | Alert fired for elevated payment API latency.
- 2026-03-11T09:27:00Z | Redis failover completed and write traffic resumed.
- 2026-03-11T09:38:00Z | Scale-out stabilized; p95 latency fell below 400ms.
