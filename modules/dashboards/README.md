# Dashboard Assets

This directory contains supporting assets for the dashboard assets area of the repository.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `metabase/` — Dashboard Assets implementation assets and supporting documentation.
- `sql/` — Dashboard Assets implementation assets and supporting documentation.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/dashboards/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
