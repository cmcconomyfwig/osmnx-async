# ruff: noqa: PLR2004, S101
"""Test async Overpass request logic with mocked HTTP."""

from __future__ import annotations

from collections import OrderedDict
from unittest.mock import AsyncMock, patch

from osmnx_async import _overpass


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
