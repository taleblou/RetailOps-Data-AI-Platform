# Configuration

The `config/` directory holds typed settings and sample environment profiles for the modular RetailOps runtime.

## Main files

- `settings.py` defines the repository-wide settings object and cached settings loader.
- `__init__.py` exposes the configuration package surface.
- `samples/` contains profile-oriented environment examples such as `lite`, `standard`, and `pro`.

## Responsibilities

- Centralize runtime configuration defaults.
- Keep environment-variable names stable across API, worker, and module runtimes.
- Provide profile samples that match the compose overlays and operational scripts.

## Maintenance notes

- When a new runtime option is added, update `settings.py`, the relevant sample env file, and any affected compose or script documentation.
- Keep configuration names consistent with actual artifact directories, ports, and service names used elsewhere in the repository.
