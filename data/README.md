# Data Directory

The `data/` directory is the repository-local home for uploads, generated artifacts, sample inputs, and runtime bundle outputs.

## Typical contents

- onboarding uploads consumed by source and setup workflows
- generated dashboard artifacts
- forecasting, shipment-risk, stockout, reorder, returns, serving, and monitoring outputs
- setup-session state
- Pro platform bundle outputs for CDC, streaming, lakehouse, metadata, query layer, feature store, and advanced serving
- small sample assets used by demos and smoke tests

## Rules

- Keep committed sample files small and representative.
- Do not commit machine-local secrets or transient runtime state.
- Keep artifact folder names aligned with service code and documentation.
