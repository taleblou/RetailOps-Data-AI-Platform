# Dataset Builders and Freshness Checks

This package turns phase 9 from a document-only milestone into executable platform scaffolding.

Included pieces:

- `contracts.py` loads YAML feature contracts
- `builder.py` generates point-in-time-safe dataset SQL with leakage prevention
- `freshness.py` evaluates feature freshness against the contract policy
- `models.py` defines the typed contract representation

The code is intentionally lightweight so later phases can plug in dbt, orchestration, and model
training jobs without rewriting the core contract interface.
