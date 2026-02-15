# ruff: noqa: PLR2004, S101
"""Test async Nominatim request logic with mocked HTTP."""

from __future__ import annotations

from collections import OrderedDict
from unittest.mock import AsyncMock
from unittest.mock import patch

from osmnx_async import _nominatim


class TestAsyncNominatim:
    """Test async Nominatim request logic with mocked HTTP."""

    async def test_nominatim_request_uses_cache(self) -> None:
        """Nominatim request returns cached data when available."""
        cached_data = [{"place_id": 1, "lat": "37.0", "lon": "-122.0"}]

        with patch(
            "osmnx_async._http._async_retrieve_from_cache",
            new_callable=AsyncMock,
            return_value=cached_data,
        ):
            params: OrderedDict[str, int | str] = OrderedDict()
            params["format"] = "json"
            params["q"] = "test query"
            result = await _nominatim._nominatim_request(params=params)

        assert result == cached_data
