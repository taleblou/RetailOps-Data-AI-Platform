.PHONY: sync check test hooks

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