# Documentation Index

The `docs/` directory organizes long-form repository documentation by stable platform concern.

## Documentation groups

- `architecture/` system-layer references and diagrams.
- `modules/` long-form documentation for key platform modules.
- `platform/` serving, monitoring, setup, and extension references.
- `business/` reporting packs and business-facing intelligence guides.
- `operations/` release and operational guidance.
- `history/` modularization records, audits, and repository transition notes.
- `quickstart/` deployment-profile walkthroughs.

## Reading order

1. Start with `architecture/platform_overview.md` and `architecture/system_layers.md`.
2. Use `module_boundaries.md` and `modules/module_catalog.md` to understand capability ownership.
3. Read `platform/` and `business/` documents for surface-specific details.
4. Use `history/` only when you need repository evolution context.

## Maintenance notes

- Keep document names and wording aligned with module names, API paths, artifact directories, and README terminology.
- Prefer adding new docs under the relevant capability group instead of creating mixed-purpose top-level files.
- Preserve `history/` as historical context, not as the main source of current operating guidance.
