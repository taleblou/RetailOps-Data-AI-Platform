# Phase 23 Business Expansion

This final pass adds three more practical modules that fit the current retail order model and extend the earlier business layer.

## Added modules

### `modules/customer_cohort_intelligence`

Purpose:
- group customers by acquisition month
- measure repeat behavior by cohort
- compare cohort revenue depth
- support lifecycle and retention analysis

Main outputs:
- cohort size
- repeat customer count
- repeat customer rate
- average orders per customer
- average revenue per customer

### `modules/inventory_aging_intelligence`

Purpose:
- detect stale inventory
- quantify days since last sale
- estimate stock cover when on-hand units are present
- support overstock cleanup and markdown decisions

Main outputs:
- stale SKU count
- critical aging count
- days since last sale
- average daily units
- days of cover
- aging band

### `modules/abc_xyz_intelligence`

Purpose:
- classify SKUs by value contribution and demand variability
- support differentiated replenishment policy
- complement forecasting and reorder planning

Main outputs:
- A/B/C value class
- X/Y/Z variability class
- combined class such as AX or CZ
- revenue share
- demand coefficient of variation

## Why these were added

These modules close three more decision gaps that are common in retail operations:
- retention and lifecycle visibility
- overstock and aging inventory visibility
- SKU policy segmentation for planning

They work on the same uploaded order data used by the other modules and do not require extra infrastructure.
