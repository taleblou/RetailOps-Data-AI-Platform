from __future__ import annotations

from datetime import timedelta

from feast import Entity, FeatureView, Field
from feast.types import Float32, Int64

sku = Entity(name="sku", join_keys=["sku"])
shipment_id = Entity(name="shipment_id", join_keys=["shipment_id"])

stockout_features_view = FeatureView(
    name="stockout_features_view",
    entities=[sku],
    ttl=timedelta(days=14),
    schema=[
        Field(name="avg_daily_demand_7d", dtype=Float32),
        Field(name="days_to_stockout", dtype=Float32),
        Field(name="reorder_urgency_score", dtype=Float32),
    ],
    online=True,
)

shipment_delay_features_view = FeatureView(
    name="shipment_delay_features_view",
    entities=[shipment_id],
    ttl=timedelta(days=7),
    schema=[
        Field(name="inventory_lag_days", dtype=Int64),
        Field(name="carrier_delay_rate_30d", dtype=Float32),
        Field(name="region_delay_trend_30d", dtype=Float32),
    ],
    online=True,
)
