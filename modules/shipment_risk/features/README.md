# Shipment risk feature SQL assets

This folder holds the feature layer used by the shipment-delay model.

## Purpose

The SQL here separates reusable model features from the online scoring API. That keeps training and serving aligned and makes it easier to test the phase 11 logic independently.

## Feature themes

- promised versus actual delivery timing
- warehouse backlog signals
- carrier history and regional delay trends
- order timing features such as hour, weekday, and holiday effects
- inventory lag context for orders at risk

## Why this matters

The roadmap asks for a real operational risk module, not just a score endpoint. These shared feature assets support that requirement.
