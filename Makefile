.PHONY: sync check test hooks install-lite install-standard install-pro upgrade-standard upgrade-pro backup restore load-demo health

sync:
	uv sync

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .
	uv run pytest

test:
	uv run pytest

hooks:
	uv run pre-commit install
	uv run pre-commit run --all-files

install-lite:
	./scripts/install.sh --profile lite

install-standard:
	./scripts/install.sh --profile standard

install-pro:
	./scripts/install.sh --profile pro

upgrade-standard:
	./scripts/upgrade.sh --profile standard

upgrade-pro:
	./scripts/upgrade.sh --profile pro

backup:
	./scripts/backup.sh --profile standard

restore:
	./scripts/restore.sh --latest --profile standard

load-demo:
	./scripts/load_demo_data.sh --upload-id make-demo

health:
	./scripts/health.sh
