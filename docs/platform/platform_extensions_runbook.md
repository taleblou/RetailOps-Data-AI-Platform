# Platform Extensions Runbook

## Goal

Use this runbook when you want to activate the Pro platform surfaces on top of the core RetailOps stack.

## 1. Validate the repository before startup

```bash
python scripts/validate_compose_profiles.py
bash scripts/health.sh
```

## 2. Start only the overlays you need

Core first:

```bash
docker compose -f compose/compose.core.yaml up -d
```

Then add overlays by capability:

- connectors: `compose/compose.connectors.yaml`
- CDC: `compose/compose.cdc.yaml`
- streaming: `compose/compose.streaming.yaml`
- lakehouse: `compose/compose.lakehouse.yaml`
- query layer: `compose/compose.query.yaml`
- metadata: `compose/compose.metadata.yaml`
- feature store: `compose/compose.feature_store.yaml`
- advanced serving: `compose/compose.advanced_serving.yaml`

## 3. Generate deployment bundles

```bash
python scripts/generate_pro_platform_bundle.py --artifact-dir data/artifacts/pro_platform --refresh
```

Generated bundles are written under:

- `data/artifacts/pro_platform/cdc/`
- `data/artifacts/pro_platform/streaming/`
- `data/artifacts/pro_platform/lakehouse/`
- `data/artifacts/pro_platform/query_layer/`
- `data/artifacts/pro_platform/metadata/`
- `data/artifacts/pro_platform/feature_store/`
- `data/artifacts/pro_platform/advanced_serving/`

## 4. Confirm readiness

Use either the script output or the API surface:

- `GET /api/v1/pro-platform/summary`
- `GET /api/v1/pro-platform/readiness`

A healthy repository-level deployment should show all requested modules as `deployment_ready`.

## 5. Hand-off checklist

Before handing the environment to a store operator or technical team, confirm:

- compose overlays load without YAML errors
- required Dockerfiles and config templates exist
- generated bundle files were created
- extension-specific health checks were reviewed
- secrets and hostnames were replaced with installation-specific values
