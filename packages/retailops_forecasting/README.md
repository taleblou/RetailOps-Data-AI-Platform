# retailops_forecasting

This package wrapper is reserved for forecasting logic and shared ML utilities.

## Intended scope

It can later absorb reusable forecasting services, schemas, batch-scoring helpers, and training contracts that currently live under `modules/forecasting/`.

## Why it exists now

The wrapper keeps the monorepo structurally ready for a future package split while the project remains easier to develop as one repository.
