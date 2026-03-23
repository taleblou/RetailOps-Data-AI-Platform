# Product Tiering

## Lite
### Intended User
Small stores with CSV files

### Included Modules
- Core ingestion (CSV)
- Core transformations
- Basic dashboards
- Basic monitoring
- Setup wizard
- Basic forecasting

### Not Included
- CDC
- Streaming
- Lakehouse
- Metadata
- Feature store

---

## Standard
### Intended User
Stores with database sources and operational analytics needs

### Included Modules
- All Lite capabilities
- Database connector
- KPI analytics
- Forecasting
- Shipment risk
- Stockout intelligence
- ML registry
- Monitoring

### Not Included
- CDC
- Streaming
- Lakehouse
- Metadata
- Advanced feature store

---

## Pro
### Intended User
Technical teams needing platform-grade architecture

### Included Modules
- All Standard capabilities
- CDC
- Streaming
- Lakehouse
- Metadata
- Feature store
- Advanced model serving

### Key Rule
Pro modules must extend the core. They must not be required for core execution.