# Phase 24 Business Expansion

This final pass adds four more practical modules that fit the current retail order model and extend the earlier business layer.

## Added modules

### `modules/customer_churn_intelligence`

Purpose:
- estimate churn risk from customer purchase cadence
- prioritize retention action lists
- separate new, low-risk, high-risk, and lost customers

Main outputs:
- churn score
- churn risk band
- recency and average inter-order gap
- recommended recovery action

### `modules/sales_anomaly_intelligence`

Purpose:
- detect unusual sales spikes and drops by day
- identify the dominant category behind each anomaly
- support incident review and campaign readouts

Main outputs:
- anomaly type by day
- revenue delta ratio versus baseline
- dominant category for the day
- largest positive and negative movement summary

### `modules/seasonality_intelligence`

Purpose:
- classify SKU seasonality from monthly sales concentration
- surface peak and trough months
- support buying, safety-stock, and campaign planning

Main outputs:
- seasonality band
- peak month
- peak-month revenue share
- active month count

### `modules/fulfillment_sla_intelligence`

Purpose:
- measure actual SLA performance on delivered and open orders
- distinguish delayed deliveries from open breach risk
- support carrier escalation and customer communication

Main outputs:
- delayed order count
- open breach risk count
- on-time delivery rate
- delay days and recommended action by order

## Why these were added

These modules fill four more common retail operating gaps that were not yet covered directly:
- customer churn prevention
- abnormal sales monitoring
- seasonality planning
- actual fulfillment SLA control

They work on the same uploaded retail order data already used by the other modules and stay compatible with the existing connector and API surface.
