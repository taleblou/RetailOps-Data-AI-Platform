# Phase 9 Feature Contracts

This folder contains the YAML contracts that define the first production-style feature layer.

Every contract captures the same minimum metadata requested by the roadmap:

- feature set name
- entity keys
- source relation
- transformation ownership
- freshness policy
- null handling strategy
- owner
- training/serving parity notes

These files are intentionally small, portable, and easy to validate from Python code in
`core/ai/dataset_builders/`.
