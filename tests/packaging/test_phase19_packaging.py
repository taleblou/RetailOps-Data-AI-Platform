from __future__ import annotations

import subprocess
from pathlib import Path


def test_phase19_required_scripts_and_docs_exist() -> None:
    required_paths = [
        Path("scripts/install.sh"),
        Path("scripts/upgrade.sh"),
        Path("scripts/backup.sh"),
        Path("scripts/restore.sh"),
        Path("scripts/load_demo_data.sh"),
        Path("scripts/health.sh"),
        Path("docs/quickstart/lite.md"),
        Path("docs/quickstart/standard.md"),
        Path("docs/quickstart/pro.md"),
        Path("config/samples/lite.env"),
        Path("config/samples/standard.env"),
        Path("config/samples/pro.env"),
        Path("docs/release_notes_phase19.md"),
        Path("docs/phase_1_to_19_gap_report.md"),
        Path("docs/phase_1_to_19_audit.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    assert not missing, f"Missing required phase 19 files: {missing}"


def test_phase19_scripts_have_valid_bash_syntax() -> None:
    for script in [
        Path("scripts/common.sh"),
        Path("scripts/install.sh"),
        Path("scripts/upgrade.sh"),
        Path("scripts/backup.sh"),
        Path("scripts/restore.sh"),
        Path("scripts/load_demo_data.sh"),
        Path("scripts/health.sh"),
    ]:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_phase19_quickstarts_reference_expected_profiles() -> None:
    assert "Lite profile" in Path("docs/quickstart/lite.md").read_text(encoding="utf-8")
    assert "Standard profile" in Path("docs/quickstart/standard.md").read_text(encoding="utf-8")
    assert "Pro profile" in Path("docs/quickstart/pro.md").read_text(encoding="utf-8")
