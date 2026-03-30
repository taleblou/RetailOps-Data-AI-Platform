# Pro Quickstart

Use this Pro profile when you need the core platform plus deployment-ready extension bundles.

## Includes

- core platform services
- connector overlays for CSV, database, Shopify, WooCommerce, Adobe Commerce, BigCommerce, and PrestaShop
- CDC and streaming bundles
- lakehouse and query-layer bundles
- metadata, feature-store, and advanced-serving bundles

## 1. Prepare the environment

1. Copy `.env.example` to `.env` if it does not already exist.
2. Review ports, credentials, and object-store values.
3. Optionally merge `config/samples/pro.env` into `.env`.

## 2. Start the Pro stack

```bash
docker compose \
  -f compose/compose.core.yaml \
  -f compose/compose.connectors.yaml \
  -f compose/compose.analytics.yaml \
  -f compose/compose.ml.yaml \
  -f compose/compose.monitoring.yaml \
  -f compose/compose.cdc.yaml \
  -f compose/compose.streaming.yaml \
  -f compose/compose.lakehouse.yaml \
  -f compose/compose.query.yaml \
  -f compose/compose.metadata.yaml \
  -f compose/compose.feature_store.yaml \
  -f compose/compose.advanced_serving.yaml \
  up -d
```

Or use the packaging helper:

```bash
bash scripts/install.sh --profile pro
```

## 3. Generate extension bundles

```bash
python scripts/generate_pro_platform_bundle.py --artifact-dir data/artifacts/pro_platform --refresh
```

This writes deployment bundles for:

- `cdc/`
- `streaming/`
- `lakehouse/`
- `query_layer/`
- `metadata/`
- `feature_store/`
- `advanced_serving/`

## 4. Run health checks

```bash
bash scripts/health.sh
python scripts/validate_compose_profiles.py
```

You can also inspect the API readiness surface:

- `GET /api/v1/pro-platform/summary`
- `GET /api/v1/pro-platform/readiness`

## 5. Load demo data and verify core analytics

```bash
bash scripts/load_demo_data.sh --upload-id demo-pro
```

Then verify:

- KPI overview routes
- forecast summary routes
- shipment-risk routes
- stockout-risk routes
- reorder recommendations
- monitoring summary

## Environment-specific items

The repository now includes the control-plane logic, bundle generation, compose overlays, runbooks, and validation helpers. Production hostnames, secrets, storage classes, and cluster sizing still depend on the target installation.
