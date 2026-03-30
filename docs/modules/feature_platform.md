# Feature Platform

The feature platform is the contract layer between raw mart logic and AI training or inference workflows.

## Responsibilities

- declare entity keys and time columns
- define feature freshness expectations
- describe feature ownership and column semantics
- support point-in-time safe dataset assembly

## Related code

See `core/ai/feature_contracts/` and `core/ai/dataset_builders/` for the implementation-oriented utilities that back this documentation.
