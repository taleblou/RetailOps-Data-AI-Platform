# Platform Extensions Gap Report

This note records the remaining separation between repository-provided extension logic and site-specific production rollout.

## What is already covered in the repository

- deployment-ready bundle generators for all Pro modules
- compose overlay summaries and service inventories
- bootstrap command lists, health checks, and readiness checks
- generated companion files for configs, SQL, and runbooks

## Remaining environment-specific work

- credentials and secret management
- production sizing and network topology
- external object storage, Kafka-compatible clusters, and metadata backing services
