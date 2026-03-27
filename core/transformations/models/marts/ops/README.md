# Operational marts folder

This folder is reserved for dbt marts that support operational workflows rather than executive reporting.
Examples include setup-session summaries, data-quality trend tables, import-run state, override activity,
and other service-level marts that help the platform explain what happened during ingestion or model usage.

## Why this folder exists

Phase 7 builds the modular dbt foundation first. The executive KPI marts live under the analytics module,
while this folder keeps space for cross-cutting operational marts that may be shared by setup, monitoring,
and future orchestration work.

## Expected kinds of models

- setup wizard progress marts
- import and transform run summaries
- data-quality event summaries
- override and feedback activity marts
- service-health support marts for internal dashboards

The folder is intentionally light today, but it is not a placeholder. It is a documented reserved location
for operational marts that belong in the core transformation layer.
