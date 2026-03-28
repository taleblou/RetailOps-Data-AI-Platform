# Stockout intelligence feature SQL assets

This folder contains the shared inventory and demand features that support stockout scoring and reorder decision support.

## Purpose

The SQL layer prepares the operational context needed by later phases:

- inventory position by SKU and date
- recent demand and stock-consumption patterns
- inbound stock context
- lead-time-aware demand pressure

## Relationship to later modules

Phase 12 uses these assets for stockout scoring. Phase 13 can then reuse the same feature foundation when producing reorder recommendations.
