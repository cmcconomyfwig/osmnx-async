# ruff: noqa: PLR2004, S101
"""Test async HTTP helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import osmnx as ox
import pytest

from osmnx_async._http import (
    _async_retrieve_from_cache,
    _async_save_to_cache,
    _build_request_kwargs,
    _get_http_headers,
    _parse_response,
    _resolve_url_to_ip,
)


class TestAsyncHttp:
    """Test async HTTP helper functions."""

    def test_get_http_headers(self) -> None:
        """Headers are built correctly from settings."""
        headers = _get_http_headers()
        assert "User-Agent" in headers
        assert "referer" in headers
        assert "Accept-Language" in headers

    def test_get_http_headers_custom(self) -> None:
        """Custom header values override settings."""
        headers = _get_http_headers(
            user_agent="test-agent",
            referer="test-referer",
            accept_language="fr",
        )
        assert headers["User-Agent"] == "test-agent"
        assert headers["referer"] == "test-referer"
        assert headers["Accept-Language"] == "fr"

    def test_build_request_kwargs_empty(self) -> None:
        """Empty requests_kwargs produces empty dicts."""
        client_kw, request_kw = _build_request_kwargs()
        assert client_kw == {}
        assert request_kw == {}

    def test_build_request_kwargs_proxies_deprecation(self) -> None:
        """Proxies dict triggers deprecation warning."""
        original = ox.settings.requests_kwargs
        try:
            ox.settings.requests_kwargs = {"proxies": {"https": "http://proxy:8080"}}
            with pytest.warns(DeprecationWarning, match="proxies"):
                client_kw, request_kw = _build_request_kwargs()
            assert client_kw["proxy"] == "http://proxy:8080"
            assert "proxies" not in request_kw
        finally:
            ox.settings.requests_kwargs = original

    def test_build_request_kwargs_client_vs_request(self) -> None:
        """Client-level kwargs are separated from per-request kwargs."""
        original = ox.settings.requests_kwargs
        try:
            ox.settings.requests_kwargs = {"verify": False, "custom_param": "value"}
            client_kw, request_kw = _build_request_kwargs()
            assert client_kw == {"verify": False}
            assert request_kw == {"custom_param": "value"}
        finally:
            ox.settings.requests_kwargs = original

    async def test_resolve_url_to_ip(self) -> None:
        """Resolve returns original URL unchanged (no rewrite for TLS safety)."""
        url = "https://overpass-api.de/api/interpreter"
        resolved_url, headers = await _resolve_url_to_ip(url)
        assert resolved_url == url
        assert headers == {}

    def test_parse_response_success(self) -> None:
        """_parse_response correctly parses a successful JSON response."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://example.com/api"
        mock_response.content = b'{"key": "value"}'
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"key": "value"}

        result = _parse_response(mock_response)
        assert result == {"key": "value"}


class TestAsyncCache:
    """Test async cache wrappers."""

    async def test_cache_round_trip(self) -> None:
        """Save and retrieve from cache produces consistent results."""
        test_url = "https://test.example.com/osmnx-async-cache-test-12345"
        test_data = {"test": "async_cache_data"}

        await _async_save_to_cache(test_url, test_data, ok=True)
        result = await _async_retrieve_from_cache(test_url)
        assert result == test_data

    async def test_cache_miss_returns_none(self) -> None:
        """Cache miss returns None."""
        result = await _async_retrieve_from_cache(
            "https://test.example.com/nonexistent-url-67890",
        )
        assert result is None

    async def test_retrieve_respects_use_cache_false(self) -> None:
        """Cache retrieval returns None when use_cache is False via contextvar."""
        from osmnx_async._settings import _settings_overrides

        test_url = "https://test.example.com/osmnx-async-cache-override-test"
        test_data = {"cached": "data"}

        # Populate cache with default settings (use_cache=True)
        await _async_save_to_cache(test_url, test_data, ok=True)
        assert await _async_retrieve_from_cache(test_url) == test_data

        # Override use_cache=False → retrieval must return None
        token = _settings_overrides.set({"use_cache": False})
        try:
            result = await _async_retrieve_from_cache(test_url)
            assert result is None
        finally:
            _settings_overrides.reset(token)

    async def test_save_respects_use_cache_false(self) -> None:
        """Cache save is skipped when use_cache is False via contextvar."""
        from osmnx_async._settings import _settings_overrides

        test_url = "https://test.example.com/osmnx-async-no-save-test"
        test_data = {"should_not": "be_cached"}

        # Try to save with use_cache=False
        token = _settings_overrides.set({"use_cache": False})
        try:
            await _async_save_to_cache(test_url, test_data, ok=True)
        finally:
            _settings_overrides.reset(token)

        # With default use_cache=True, data should not be found
        result = await _async_retrieve_from_cache(test_url)
        assert result is None

    async def test_cache_isolation_between_tasks(self) -> None:
        """Concurrent tasks with different use_cache settings are isolated."""
        import asyncio
        from typing import Any

        from osmnx_async._settings import _settings_overrides

        test_url = "https://test.example.com/osmnx-async-isolation-test"
        test_data = {"isolation": "test"}
        results: dict[str, Any] = {}

        # Pre-populate cache
        await _async_save_to_cache(test_url, test_data, ok=True)

        async def task_cache_disabled() -> None:
            _settings_overrides.set({"use_cache": False})
            results["disabled"] = await _async_retrieve_from_cache(test_url)

        async def task_cache_enabled() -> None:
            # No override → use_cache defaults to True
            results["enabled"] = await _async_retrieve_from_cache(test_url)

        await asyncio.gather(
            asyncio.create_task(task_cache_disabled()),
            asyncio.create_task(task_cache_enabled()),
        )

        assert results["disabled"] is None
        assert results["enabled"] == test_data
