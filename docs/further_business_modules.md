# Further Business Modules Added in the Final Recheck

This final recheck extends the previously added business layer with three more practical modules that fit the current canonical retail model and work on uploaded order data.

## New modules

### `modules/assortment_intelligence`

Purpose:
- identify hero SKUs
- detect slow movers
- quantify long-tail concentration
- support assortment review and merchandising cleanup

Main outputs:
- SKU movement class
- revenue share by SKU
- hero SKU share
- long-tail revenue share

### `modules/basket_affinity_intelligence`

Purpose:
- find products frequently bought together
- surface cross-sell candidates
- support bundle design and merchandising placement

Main outputs:
- SKU pair support
- confidence
- lift
- strongest product pair summary

### `modules/profitability_intelligence`

Purpose:
- estimate SKU-level profitability
- detect discount leakage
- detect loss-making or thin-margin SKUs
- support pricing and margin review

Main outputs:
- revenue
- cost
- gross profit
- gross margin rate
- discount rate
- margin band

## Why these modules were chosen

These modules add direct business value without forcing new infrastructure dependencies.
They work on the same canonical retail order data already used by the existing CSV and connector flows.
They also complement the earlier additions:
- `promotion_pricing_intelligence`
- `supplier_procurement_intelligence`
- `customer_intelligence`
- `payment_reconciliation`

Together, the business layer now covers:
- pricing and promotion
- supplier execution
- customer value
- payment control
- assortment quality
- basket affinity
- profitability


## Additional phase 23 additions

- `customer_cohort_intelligence`
- `inventory_aging_intelligence`
- `abc_xyz_intelligence`

These modules extend the business layer toward retention analysis, stale-stock control, and SKU policy segmentation.

## Additional phase 24 additions

- `customer_churn_intelligence`
- `sales_anomaly_intelligence`
- `seasonality_intelligence`
- `fulfillment_sla_intelligence`

These modules extend the business layer toward retention recovery, anomaly monitoring, seasonality planning, and real fulfillment SLA control.
