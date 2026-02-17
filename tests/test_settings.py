# ruff: noqa: PLR2004, S101
"""Test the async-safe settings accessor."""

from __future__ import annotations

import asyncio

import osmnx as ox

import osmnx_async
from osmnx_async._settings import _settings_overrides, get


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

    def test_settings_exported_from_package(self) -> None:
        """settings module is accessible as osmnx_async.settings."""
        assert hasattr(osmnx_async, "settings")
        assert osmnx_async.settings.get("use_cache") is True

    def test_reads_from_osmnx_settings(self) -> None:
        """get() reads live values from osmnx.settings, not copies."""
        original = ox.settings.requests_timeout
        try:
            ox.settings.requests_timeout = 999.0
            assert get("requests_timeout") == 999.0
        finally:
            ox.settings.requests_timeout = original


class TestSettingsProxy:
    """Test the attribute-access proxy on osmnx_async.settings."""

    def test_read_attribute_returns_default(self) -> None:
        """Reading a setting via attribute falls back to osmnx.settings."""
        assert osmnx_async.settings.use_cache is True

    def test_write_attribute_stores_in_contextvar(self) -> None:
        """Writing a setting via attribute stores it in the contextvar."""
        token = _settings_overrides.set(None)
        try:
            osmnx_async.settings.use_cache = False
            assert osmnx_async.settings.use_cache is False
            # The underlying osmnx.settings should be untouched.
            assert ox.settings.use_cache is True
        finally:
            _settings_overrides.reset(token)

    def test_write_does_not_mutate_upstream(self) -> None:
        """Attribute writes never leak into osmnx.settings globals."""
        original = ox.settings.requests_timeout
        token = _settings_overrides.set(None)
        try:
            osmnx_async.settings.requests_timeout = 42
            assert osmnx_async.settings.requests_timeout == 42
            assert ox.settings.requests_timeout == original
        finally:
            _settings_overrides.reset(token)

    def test_read_falls_through_to_live_upstream(self) -> None:
        """Without an override, reads reflect live upstream changes."""
        original = ox.settings.requests_timeout
        try:
            ox.settings.requests_timeout = 777
            assert osmnx_async.settings.requests_timeout == 777
        finally:
            ox.settings.requests_timeout = original

    def test_override_shadows_upstream(self) -> None:
        """A contextvar override takes priority over upstream."""
        original = ox.settings.requests_timeout
        token = _settings_overrides.set(None)
        try:
            osmnx_async.settings.requests_timeout = 42
            ox.settings.requests_timeout = 999
            # Override wins
            assert osmnx_async.settings.requests_timeout == 42
        finally:
            _settings_overrides.reset(token)
            ox.settings.requests_timeout = original

    def test_unknown_attribute_raises(self) -> None:
        """Accessing a non-existent setting raises AttributeError."""
        import pytest

        with pytest.raises(AttributeError, match="no_such_setting_xyz"):
            _ = osmnx_async.settings.no_such_setting_xyz

    def test_dir_includes_osmnx_settings(self) -> None:
        """dir() lists osmnx setting names for tab-completion."""
        names = dir(osmnx_async.settings)
        assert "use_cache" in names
        assert "requests_timeout" in names
        assert "overpass_url" in names

    def test_async_task_isolation(self) -> None:
        """Concurrent tasks get independent setting overrides via create_task.

        asyncio.create_task copies the current context, so each task gets its
        own contextvar space automatically.
        """
        results: dict[str, bool | None] = {}

        async def task_a() -> None:
            osmnx_async.settings.use_cache = False
            await asyncio.sleep(0.01)
            results["a"] = osmnx_async.settings.use_cache

        async def task_b() -> None:
            osmnx_async.settings.use_cache = True
            await asyncio.sleep(0.01)
            results["b"] = osmnx_async.settings.use_cache

        async def _run() -> None:
            # create_task snapshots the current context per-task.
            await asyncio.gather(
                asyncio.create_task(task_a()),
                asyncio.create_task(task_b()),
            )
            assert results["a"] is False
            assert results["b"] is True

        token = _settings_overrides.set(None)
        try:
            asyncio.run(_run())
        finally:
            _settings_overrides.reset(token)
