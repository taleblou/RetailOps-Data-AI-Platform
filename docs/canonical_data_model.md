# Canonical Data Model

## Goal
Create a shared retail data model for all connectors and downstream modules.

## Schemas
- raw
- staging
- mart
- features
- predictions
- ops

## Canonical business tables
- stores
- products
- customers
- orders
- order_items
- payments
- shipments
- inventory_snapshots
- promotions

## System tables
- import_jobs
- sync_runs
- dq_results
- model_runs
- prediction_runs
- drift_runs
- override_logs

## Data contracts
- No connector writes directly to mart.
- All source data lands in raw first.
- Transformations move data from raw to staging and mart.