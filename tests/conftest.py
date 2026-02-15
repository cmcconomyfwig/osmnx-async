# ruff: noqa: S101
"""Shared fixtures for osmnx_async tests."""

from __future__ import annotations

import osmnx as ox

# configure osmnx settings for tests
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.cache_folder = ".temp/cache"
