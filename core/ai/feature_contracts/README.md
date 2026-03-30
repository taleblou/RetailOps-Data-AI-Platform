# Feature Contracts

Marks core.ai.feature_contracts as a Python package and centralizes its package-level imports.

## Directory contents

- `__init__.py` — Defines the core.ai.feature_contracts package surface and package-level exports.
- `customer_return_features.yaml` — YAML configuration or contract asset used by this component.
- `inventory_position_daily.yaml` — YAML configuration or contract asset used by this component.
- `product_demand_daily.yaml` — YAML configuration or contract asset used by this component.
- `shipment_delay_features.yaml` — YAML configuration or contract asset used by this component.
- `stockout_features.yaml` — YAML configuration or contract asset used by this component.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Scope profile: internal (1).
- Status profile: internal (1).
- Important dependencies: Standard library only.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `README.md` repository-level overview and navigation entry point
