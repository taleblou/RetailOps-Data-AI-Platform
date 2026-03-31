# Pro Platform Sample Output

This directory is intentionally kept lightweight in the repository.

Generate fresh Pro platform bundles for your own environment with:

```bash
python scripts/generate_pro_platform_bundle.py --artifact-dir data/artifacts/pro_platform --refresh
```

The generated files are installation-specific because they include runtime paths, compose overlays, and environment-dependent artifact locations.
