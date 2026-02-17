# ruff: noqa: PLR2004, S101
"""Test async Overpass request logic with mocked HTTP."""

from __future__ import annotations

from collections import OrderedDict
from unittest.mock import AsyncMock, patch

import osmnx as ox

from osmnx_async import _overpass
from osmnx_async._settings import _settings_overrides


class TestOverpassWrappers:
    """Test that re-exported overpass helpers respect contextvar overrides."""

    def test_make_overpass_settings_respects_timeout_override(self) -> None:
        """_make_overpass_settings uses the contextvar-overridden timeout."""
        token = _settings_overrides.set({"requests_timeout": 999})
        try:
            result = _overpass._make_overpass_settings()
            assert "999" in result
        finally:
            _settings_overrides.reset(token)

    def test_make_overpass_settings_respects_memory_override(self) -> None:
        """_make_overpass_settings uses the contextvar-overridden memory."""
        token = _settings_overrides.set({"overpass_memory": 123456})
        try:
            result = _overpass._make_overpass_settings()
            assert "123456" in result
        finally:
            _settings_overrides.reset(token)

    def test_get_network_filter_respects_default_access_override(self) -> None:
        """_get_network_filter uses the contextvar-overridden default_access."""
        custom_access = '["access"!~"private|restricted"]'
        token = _settings_overrides.set({"default_access": custom_access})
        try:
            result = _overpass._get_network_filter("drive")
            assert custom_access in result
        finally:
            _settings_overrides.reset(token)

    def test_wrapper_does_not_leak_to_upstream(self) -> None:
        """Overrides are cleaned up after the wrapper returns."""
        original_timeout = ox.settings.requests_timeout
        token = _settings_overrides.set({"requests_timeout": 777})
        try:
            _overpass._make_overpass_settings()
            # After the wrapper returns, upstream must be restored
            assert ox.settings.requests_timeout == original_timeout
        finally:
            _settings_overrides.reset(token)


class TestAsyncOverpass:
    """Test async Overpass request logic with mocked HTTP."""

    async def test_overpass_request_uses_cache(self) -> None:
        """Overpass request returns cached data when available."""
        cached_data = {"elements": []}

        with (
            patch(
                "osmnx_async._http._async_retrieve_from_cache",
                new_callable=AsyncMock,
                return_value=cached_data,
            ),
            patch(
                "osmnx_async._http._resolve_url_to_ip",
                new_callable=AsyncMock,
                return_value=("https://overpass-api.de/api/interpreter", {}),
            ),
        ):
            result = await _overpass._overpass_request(OrderedDict(data="test"))

        assert result == cached_data
