# Model Registry and Lifecycle

The registry and lifecycle layer standardizes how champion and challenger models are described inside the repository.

## Responsibilities

- register model versions and metadata
- expose current champion selections
- persist lifecycle events for approval or review
- provide a stable source of truth for serving and monitoring

## Related module

See `modules/ml_registry/` for the implementation used by API routes and monitoring services.
