.PHONY: build test test-integration lint

build:
	uv run python scripts/sync_version.py
	uv build

test:
	uv run pytest -m "not integration"

test-integration:
	uv run pytest -m integration

lint:
	uv run ruff check src tests
