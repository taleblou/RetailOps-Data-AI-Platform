# Personas

## Persona 1: Small Store with CSV
### Profile
A small retail business that manages sales and inventory in spreadsheets or exported CSV files.

### Current Situation
- Data is manual
- No central dashboard
- No technical team

### Pain Points
- Hard to consolidate reports
- Inventory decisions are reactive
- No forecast

### What They Need First
- Easy CSV upload
- Mapping wizard
- Basic dashboard
- Simple forecast

### Technical Level
Low

### Success Criteria
- Can upload CSV without engineering help
- Can see dashboards quickly
- Can get a basic demand forecast

---

## Persona 2: Medium Store with Database
### Profile
A retailer that already has PostgreSQL, MySQL, or another operational database.

### Current Situation
- Data exists in systems
- Some technical ability exists
- Reporting is fragmented

### Pain Points
- KPI definitions are inconsistent
- No unified canonical model
- AI outputs are not operationalized

### What They Need First
- DB connector
- Canonical model
- KPI dashboards
- Forecasting and shipment risk

### Technical Level
Medium

### Success Criteria
- Can sync from database
- Can build trusted marts
- Can use AI outputs in operations

---

## Persona 3: Technical Team with CDC and Streaming
### Profile
A more advanced team that wants near-real-time pipelines and data platform capabilities.

### Current Situation
- Multiple systems
- Engineering resources available
- Need more scalable architecture

### Pain Points
- Batch-only sync is not enough
- No lineage or metadata layer
- Hard to operationalize advanced platform modules

### What They Need First
- CDC
- Streaming
- Metadata
- Lakehouse
- Feature store

### Technical Level
High

### Success Criteria
- Can extend core platform with Pro modules
- Can maintain modular deployment
- Can support advanced serving and governance