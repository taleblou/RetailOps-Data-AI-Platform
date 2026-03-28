# dashboards

Starter phase 8 dashboard assets for Metabase.

## What is included

- `metabase/executive_overview.dashboard.json`
- `metabase/sales_dashboard.dashboard.json`
- `metabase/inventory_dashboard.dashboard.json`
- `metabase/shipment_dashboard.dashboard.json`
- `sql/executive_overview.sql`
- `sql/sales_dashboard.sql`
- `sql/inventory_dashboard.sql`
- `sql/shipment_dashboard.sql`

## Purpose

These files provide a practical dashboard starter pack for the KPI analytics module described in phase 8.

They are intentionally source-controlled and human-readable. They can be used in two ways:

1. as the blueprint for manual Metabase dashboard setup
2. as inputs to a future dashboard bootstrap script or Metabase API importer

## Recommended import order

1. connect Metabase to the project PostgreSQL database
2. expose the mart tables built by dbt
3. create SQL questions from the files in `sql/`
4. create dashboards using the layout hints in `metabase/`

## Expected source tables

- `mart.mart_store_kpis`
- `mart.fct_daily_sales`
- `mart.fct_inventory_daily`
- `mart.fct_shipments`

## Dashboard list

### Executive Overview

High-level revenue, orders, average order value, stock health, and shipment SLA signals.

### Sales Dashboard

Daily sales trend and revenue by category.

### Inventory Dashboard

Current inventory position, days of cover, and low-stock flags.

### Shipment Dashboard

Shipment volume, delayed shipment counts, and on-time rate.
