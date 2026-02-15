# ruff: noqa: PLR2004, S101
"""Test the async-safe settings accessor."""

from __future__ import annotations

import osmnx as ox

from osmnx_async._settings import _settings_overrides
from osmnx_async._settings import get


class TestAsyncSettings:
    """Test the contextvars-based settings accessor."""

    def test_get_returns_module_default(self) -> None:
        """get() returns the osmnx module-level default when no override."""
        assert get("use_cache") is True
        assert get("overpass_url") == "https://overpass-api.de/api"

    def test_get_returns_override(self) -> None:
        """get() returns the override value when one is set."""
        token = _settings_overrides.set({"use_cache": False})
        try:
            assert get("use_cache") is False
            # non-overridden setting still returns module default
            assert get("overpass_url") == "https://overpass-api.de/api"
        finally:
            _settings_overrides.reset(token)

    def test_override_isolation(self) -> None:
        """Overrides are isolated per-context (simulated with set/reset)."""
        assert get("use_cache") is True
        token = _settings_overrides.set({"use_cache": False})
        assert get("use_cache") is False
        _settings_overrides.reset(token)
        assert get("use_cache") is True

    def test_reads_from_osmnx_settings(self) -> None:
        """get() reads live values from osmnx.settings, not copies."""
        original = ox.settings.requests_timeout
        try:
            ox.settings.requests_timeout = 999.0
            assert get("requests_timeout") == 999.0
        finally:
            ox.settings.requests_timeout = original
