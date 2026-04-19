# RetailOps Data & AI Platform

RetailOps is a modular retail data and AI platform for source onboarding, trusted transformations, KPI analytics, operational intelligence, business reporting, and optional data-platform extensions.

The repository is organized around stable capability boundaries. Core platform code lives under `core/`. Business and connector capabilities live under `modules/`. Environment assembly lives under `compose/`, `config/`, and `scripts/`.

## What the platform includes

### Core platform

- FastAPI application composition and route registration
- source management, connector registration, raw loading, and sync-state persistence
- setup wizard flows for onboarding, first import, first transform, and first training
- monitoring, override logging, serving metadata, and worker orchestration
- dbt-oriented transformation assets and shared runtime services

### Connector modules

- CSV
- database
- Shopify
- WooCommerce
- Adobe Commerce
- BigCommerce
- PrestaShop

The installer and registry now treat connectors as first-class modular units. Users choose the connector overlays they want instead of installing or starting every connector service.

### Operational intelligence modules

- forecasting
- shipment risk
- stockout intelligence
- reorder engine
- returns intelligence

### Commercial, planning, and reporting modules

- analytics KPI
- dashboard hub and dashboards
- business review reporting
- profitability intelligence
- payment reconciliation
- assortment intelligence
- basket affinity intelligence
- customer intelligence
- customer cohort intelligence
- customer churn intelligence
- sales anomaly intelligence
- seasonality intelligence
- inventory aging intelligence
- promotion pricing intelligence
- supplier procurement intelligence
- fulfillment SLA intelligence
- ABC/XYZ intelligence

### Optional platform extensions

- CDC
- streaming
- lakehouse
- metadata and lineage
- feature store
- query layer
- advanced serving

## Repository map

- `core/` shared platform layers used across modules
- `modules/` bounded connectors, intelligence services, dashboards, and platform extensions
- `compose/` Docker Compose overlays split by capability slice
- `config/` typed settings and profile-oriented environment samples
- `scripts/` install, upgrade, health, backup, restore, validation, and bundle-generation helpers
- `docs/` architecture, module, business, platform, operations, history, and quickstart documentation
- `tests/` regression coverage grouped by capability family
- `packages/` thin packaging workspaces for selective distribution
- `data/` sample inputs, upload roots, and generated artifact locations

## Runtime profiles

### Lite profile

Use Lite for connector onboarding, trusted data foundations, dashboards, and starter analytics.

### Standard profile

Use Standard when you also need operational intelligence, MLflow-oriented lifecycle surfaces, and monitoring.

### Pro profile

Use Pro when you also need the optional data-platform extensions such as CDC, streaming, lakehouse, metadata, feature store, query layer, and advanced serving.

## Selective connector installation

Connector services are enabled one by one.

Examples:

```bash
./scripts/install.sh --profile lite --connectors csv
./scripts/install.sh --profile standard --connectors csv,database,shopify
./scripts/install.sh --profile pro --connectors woocommerce
```

You can inspect the available connector names before installation:

```bash
./scripts/install.sh --list-connectors
```

The installer writes `ENABLED_CONNECTORS` into `.env`, the runtime registry only registers those connectors, and Compose only adds the matching `compose.connector_*.yaml` overlays.

## Optional dependency surfaces

Some capabilities rely on optional Python extras instead of forcing every installation to carry every dependency.

- `reporting` for PDF-oriented business review reporting helpers
- `feature-store` for Feast-based feature-store assets
- `advanced-serving` for BentoML-oriented serving assets

The install and upgrade helpers choose profile-aligned extras automatically. You can also override them explicitly:

```bash
./scripts/install.sh --profile standard --connectors csv,database --extras reporting
./scripts/install.sh --profile pro --connectors shopify --extras reporting,feature-store,advanced-serving
./scripts/install.sh --profile lite --connectors csv --extras none
```

## Quick start

1. Review `.env.example` and, if needed, the matching sample file under `config/samples/`.
2. Run `./scripts/install.sh` with the desired profile and connectors.
3. Run `bash scripts/health.sh`.
4. Open the API health route or the setup wizard flows.
5. Load demo data with `bash scripts/load_demo_data.sh` when you want a smoke-test run.

## Validation and maintenance

- `python scripts/validate_compose_profiles.py` validates compose overlays, referenced Dockerfiles, and profile samples.
- `pytest -q` runs the automated regression suite.
- `bash scripts/health.sh` checks runtime readiness.

## Reading order

- Start with `core/README.md` for shared platform layers.
- Continue with `modules/README.md` for the module catalog.
- Use `compose/README.md`, `config/README.md`, and `scripts/README.md` for deployment mechanics.
- Use `docs/README.md` for long-form references.
- Use `packages/README.md` when you want the selective distribution surface.

## Documentation rules

- Keep README claims aligned with actual routes, services, file paths, and environment keys.
- Keep module names consistent across code, docs, and compose overlays.
- Prefer module-oriented wording. Do not reintroduce staged-delivery wording.
