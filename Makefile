.PHONY: build test test-integration lint sync_osmnx_version

build: lint
	uv run python scripts/sync_version.py
	uv build

test: lint
	uv run pytest -m "not integration"

test-integration: lint
	uv run pytest -m integration

lint:
	uv run ruff check src tests

sync_osmnx_version: lint
	uv run python scripts/sync_osmnx_version.py
	uv sync
	uv run pytest
