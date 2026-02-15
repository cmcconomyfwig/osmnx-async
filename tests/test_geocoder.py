# ruff: noqa: PLR2004, S101
"""Test async geocoder with mocked Nominatim."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from osmnx._errors import InsufficientResponseError

from osmnx_async import geocoder as aio_geocoder


class TestAsyncGeocoder:
    """Test async geocoder with mocked Nominatim."""

    async def test_geocode(self) -> None:
        """Async geocode returns (lat, lon) tuple."""
        mock_response = [{"lat": "37.7952", "lon": "-122.4028"}]

        with patch(
            "osmnx_async._nominatim._nominatim_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await aio_geocoder.geocode("test address")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert abs(result[0] - 37.7952) < 0.001
        assert abs(result[1] - (-122.4028)) < 0.001

    async def test_geocode_no_results_raises(self) -> None:
        """Async geocode raises InsufficientResponseError on empty results."""
        with (
            patch(
                "osmnx_async._nominatim._nominatim_request",
                new_callable=AsyncMock,
                return_value=[],
            ),
            pytest.raises(InsufficientResponseError),
        ):
            await aio_geocoder.geocode("nonexistent place xyz123")
