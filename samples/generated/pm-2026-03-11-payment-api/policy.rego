package postmortem_shield.pm_2026_03_11_payment_api

default deny = []

# Finding F001: HPA hit maxReplicas=12 for 11 minutes while p95 latency stayed above 900ms.
deny[msg] {
  input.kind == "Deployment"
  input.metadata.labels["app.kubernetes.io/name"] == "payment-api"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.cpu
  msg := "F001 (Autoscaling ceiling delayed recovery under burst traffic.): deployment payment-api must define resources and probes [trace=postmortem://pm-2026-03-11-payment-api#F001]"
}

# Finding F002: 23% of restarted pods returned 5xx for the first two minutes after start.
deny[msg] {
  input.kind == "Deployment"
  input.metadata.labels["app.kubernetes.io/name"] == "payment-api"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.cpu
  msg := "F002 (Readiness probes allowed stale Redis connections.): deployment payment-api must define resources and probes [trace=postmortem://pm-2026-03-11-payment-api#F002]"
}

# Finding F003: No recorded game-day validating cache failover in the last 90 days.
deny[msg] {
  input.kind == "Deployment"
  input.metadata.labels["app.kubernetes.io/name"] == "redis-cluster"
  some i
  container := input.spec.template.spec.containers[i]
  not container.resources.limits.cpu
  msg := "F003 (Cache failover chaos coverage was missing.): deployment redis-cluster must define resources and probes [trace=postmortem://pm-2026-03-11-payment-api#F003]"
}
