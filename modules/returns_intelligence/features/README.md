# Returns intelligence feature SQL assets

This folder contains the return-risk feature layer reserved in phase 9 and used by the dedicated phase 14 module.

## Purpose

The assets here define a stable feature contract for return modelling before the scoring service is enabled.

## Feature themes

- customer return behaviour
- SKU and category return history
- promotion and discount context
- shipment delay influence on returns
- expected return-cost signals

## Design note

Keeping these features separate from the API and scoring service makes the return-risk module easier to extend, test, and later migrate to a fuller feature-store workflow.
