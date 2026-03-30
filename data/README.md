# Data Directory

The `data/` directory is the repository-local home for sample uploads, generated artifacts, and other runtime file outputs used by demos, smoke tests, and module workflows.

## Typical contents

- sample CSV or source files for onboarding and test flows
- upload roots consumed by setup and ingestion workflows
- generated artifacts written by forecasting, monitoring, serving, and other modules
- temporary workspace outputs used during local execution

## Maintenance notes

- Keep committed sample data small and representative.
- Pro platform sample outputs are generated on demand instead of shipping stale machine-local bundle snapshots.
- Do not commit environment-specific secrets or machine-local runtime state.
- Keep artifact folder names aligned with the paths documented in module services and README files.
