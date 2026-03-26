Generate Prometheus alert rules from findings.
Requirements:
- One alert per finding
- Include traceability annotation in format postmortem://<incident_id>#<finding_id>
- Prefer service-specific expressions over generic metrics where possible
