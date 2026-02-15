# ruff: noqa: PLR2004, S101
"""Test async features module with mocked Overpass."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import geopandas as gpd
from shapely.geometry import box

from osmnx_async import features as aio_features


class TestAsyncFeatures:
    """Test async features functions with mocked HTTP."""

    async def test_features_from_polygon(self) -> None:
        """features_from_polygon downloads async then delegates to sync _create_gdf."""
        polygon = box(-122.5, 37.7, -122.4, 37.8)
        mock_response = {"elements": []}
        mock_gdf = gpd.GeoDataFrame()

        async def _mock_download(*_args, **_kwargs):  # noqa: ANN002, ANN003
            yield mock_response

        with (
            patch(
                "osmnx_async._overpass._download_overpass_features",
                side_effect=_mock_download,
            ),
            patch(
                "osmnx.features._create_gdf",
                return_value=mock_gdf,
            ) as mock_create,
        ):
            result = await aio_features.features_from_polygon(
                polygon, tags={"building": True},
            )

        assert mock_create.called
        assert isinstance(result, gpd.GeoDataFrame)

    async def test_features_from_bbox(self) -> None:
        """features_from_bbox delegates to features_from_polygon."""
        mock_gdf = gpd.GeoDataFrame()

        with patch(
            "osmnx_async.features.features_from_polygon",
            new_callable=AsyncMock,
            return_value=mock_gdf,
        ):
            result = await aio_features.features_from_bbox(
                (-122.5, 37.7, -122.4, 37.8),
                tags={"building": True},
            )

        assert isinstance(result, gpd.GeoDataFrame)
