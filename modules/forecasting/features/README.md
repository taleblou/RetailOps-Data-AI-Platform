# Forecasting feature SQL assets

This folder contains the phase 9 and phase 10 feature SQL used by the forecasting module.

## Purpose

These assets define the daily demand feature layer that feeds training, backtesting, and batch scoring. Keeping them in a dedicated folder makes the feature logic reusable across dbt, SQL jobs, and later orchestration.

## Typical contents

- entity-level daily demand aggregates
- lag and rolling-window features
- inventory-aware demand context where available
- stable relations that can be reused by dataset builders

## Usage note

The repository keeps these queries lightweight and portable so the same feature contract can support both the simple self-hosted path and more advanced phase 20 extensions later.
