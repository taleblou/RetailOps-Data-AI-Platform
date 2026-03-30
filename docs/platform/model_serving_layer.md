# Model Serving Layer

The serving layer standardizes prediction and explanation responses across forecasting, shipment risk, stockout, and reorder capabilities.

## Responsibilities

- create common batch-serving artifacts
- keep response envelopes consistent across modules
- provide one API surface for summary, detail, and explanation-style outputs

## Related code

See `core/serving/` for shared contracts and `core/api/routes/serving.py` for the unified route layer.
