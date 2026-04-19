# Configuration

The `config/` directory holds typed runtime settings and profile-oriented environment samples.

## Main files

- `settings.py` typed settings loader used by the API and shared services
- `samples/lite.env` starter profile sample
- `samples/standard.env` operational AI profile sample
- `samples/pro.env` full platform-extension profile sample

## Important configuration keys

- `APP_PROFILE` active runtime profile
- `ENABLED_CONNECTORS` comma-separated connector list used by install scripts and the runtime registry
- `ENABLED_OPTIONAL_EXTRAS` comma-separated optional dependency list used by install and upgrade scripts
- `COMPOSE_FILES` resolved overlay list for the active installation
- PostgreSQL, MinIO, Redis, Redpanda, MLflow, Metabase, and metadata-service connection settings
- `PRO_PLATFORM_ARTIFACT_DIR` output root for extension bundles

## Design intent

Configuration should describe what the current installation can actually run. The selected connectors, compose overlays, and optional extras should tell the same story.

## Maintenance rules

- When a new runtime option is added, update `settings.py`, `.env.example`, and the relevant profile sample.
- Keep environment-variable names aligned with actual routes, services, and artifact paths.
- Prefer opinionated samples instead of dumping every possible setting into every profile.
