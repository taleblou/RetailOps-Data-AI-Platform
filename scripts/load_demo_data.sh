#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

UPLOAD_ID="demo-packaging"

while [ $# -gt 0 ]; do
  case "$1" in
    --upload-id)
      UPLOAD_ID="$2"
      shift 2
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

ensure_runtime_dirs
bootstrap_env_file "standard"

log "Generating demo artifacts for upload_id '$UPLOAD_ID'"
python3 - "$ROOT_DIR" "$UPLOAD_ID" <<'PY'
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
upload_id = sys.argv[2]

sys.path.insert(0, str(root))

from core.transformations.service import run_first_transform
from modules.analytics_kpi.service import publish_first_dashboard
from modules.forecasting.service import run_first_forecast

source_file = root / 'data' / 'demo_csv' / 'sample_orders_easy_csv_150.csv'
if not source_file.exists():
    raise SystemExit(f'Missing demo source CSV: {source_file}')

uploads_dir = root / 'data' / 'uploads'
transforms_dir = root / 'data' / 'artifacts' / 'transforms'
dashboards_dir = root / 'data' / 'artifacts' / 'dashboards'
forecasts_dir = root / 'data' / 'artifacts' / 'forecasts'
setup_dir = root / 'data' / 'artifacts' / 'setup'

for directory in (uploads_dir, transforms_dir, dashboards_dir, forecasts_dir, setup_dir):
    directory.mkdir(parents=True, exist_ok=True)

target_csv = uploads_dir / f'{upload_id}_sample_orders_easy_csv_150.csv'
shutil.copy2(source_file, target_csv)

metadata = {
    'upload_id': upload_id,
    'filename': target_csv.name,
    'stored_path': str(target_csv),
    'delimiter': ',',
    'encoding': 'utf-8',
    'mapping': {
        'order_id': 'Order ID',
        'order_date': 'Order Date',
        'customer_id': 'Customer ID',
        'sku': 'SKU',
        'quantity': 'Quantity',
        'unit_price': 'Unit Price',
        'store_code': 'Store Code',
    },
    'transform_summary': None,
    'forecast_summary': None,
    'dashboard_summary': None,
}
metadata_path = uploads_dir / f'{upload_id}.json'
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')

transform = run_first_transform(upload_id=upload_id, artifact_dir=transforms_dir, metadata=metadata)
transform_payload = transform.to_dict()
forecast = run_first_forecast(upload_id=upload_id, artifact_dir=forecasts_dir, transform_summary=transform_payload)
forecast_payload = forecast.to_dict()
dashboard = publish_first_dashboard(
    upload_id=upload_id,
    filename=target_csv.name,
    transform_summary=transform_payload,
    artifact_dir=dashboards_dir,
)
dashboard_payload = dashboard.to_dict()

metadata['transform_summary'] = transform_payload
metadata['forecast_summary'] = forecast_payload
metadata['dashboard_summary'] = dashboard_payload
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')

manifest = {
    'upload_id': upload_id,
    'metadata_path': str(metadata_path),
    'transform_artifact_path': transform_payload['artifact_path'],
    'forecast_artifact_path': forecast_payload['artifact_path'],
    'dashboard_artifact_path': dashboard_payload['artifact_path'],
}
manifest_path = setup_dir / f'{upload_id}_manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

print(json.dumps(manifest, ensure_ascii=False, indent=2))
PY
