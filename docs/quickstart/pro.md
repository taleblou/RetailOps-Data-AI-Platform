# Quickstart - Pro profile

The Pro profile is the full phase 20 profile.
It includes the standard stack plus CDC, streaming, lakehouse, query federation, metadata, feature store, and advanced serving overlays.

## Included modules

- everything in Standard
- CDC and Debezium planning surface
- streaming overlay
- lakehouse overlay
- query-layer overlay
- metadata overlay
- feature-store overlay
- advanced-serving overlay

## Installation

```bash
./scripts/install.sh --profile pro
```

## Upgrade

```bash
./scripts/upgrade.sh --profile pro
```

## Backup

```bash
./scripts/backup.sh --profile pro
```

## Restore

```bash
./scripts/restore.sh --latest --profile pro
```

## Health check

```bash
./scripts/health.sh
```

## Main phase 20 APIs

- `/api/v1/pro/cdc/blueprint`
- `/api/v1/pro/streaming/blueprint`
- `/api/v1/pro/lakehouse/blueprint`
- `/api/v1/pro/query-layer/blueprint`
- `/api/v1/pro/metadata/blueprint`
- `/api/v1/pro/feature-store/blueprint`
- `/api/v1/pro/advanced-serving/blueprint`
- `/api/v1/pro-platform/summary`

## Notes for technical teams

- profile defaults live in `config/samples/pro.env`
- the compose layers are selected automatically by the packaging scripts
- the module config starters live under `modules/*/config`, `modules/*/repo`, and `modules/*/bentoml`
- the phase 20 documentation lives in `docs/pro_data_platform_phase20.md`

## When to choose Pro

Choose Pro when the customer has a technical team and wants to extend the hosted-self product into a broader data platform with CDC, streaming, lakehouse analytics, metadata governance, feature serving, and separate model runtimes.
