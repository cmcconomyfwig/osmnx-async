# ruff: noqa: PLR2004, S101
"""Test async graph module with mocked Overpass."""

from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import networkx as nx
from shapely.geometry import box

from osmnx_async import graph as aio_graph


def _make_mock_graph() -> nx.MultiDiGraph:
    """Create a small mock graph for testing."""
    G = nx.MultiDiGraph()
    G.add_node(1, x=-122.4, y=37.7, street_count=2)
    G.add_node(2, x=-122.5, y=37.8, street_count=2)
    G.add_edge(1, 2, length=100)
    G.add_edge(2, 1, length=100)
    return G


class TestAsyncGraph:
    """Test async graph functions with mocked HTTP."""

    async def test_graph_from_polygon(self) -> None:
        """graph_from_polygon downloads async then delegates to sync construction."""
        polygon = box(-122.5, 37.7, -122.4, 37.8)
        mock_response = {"elements": []}
        mock_graph = _make_mock_graph()

        async def _mock_download(*_args, **_kwargs):  # noqa: ANN002, ANN003
            yield mock_response

        with (
            patch(
                "osmnx_async._overpass._download_overpass_network",
                side_effect=_mock_download,
            ),
            patch("osmnx.graph._create_graph", return_value=mock_graph),
            patch("osmnx.truncate.truncate_graph_polygon", return_value=mock_graph),
            patch("osmnx.truncate.largest_component", return_value=mock_graph),
            patch("osmnx.simplification.simplify_graph", return_value=mock_graph),
            patch(
                "osmnx.stats.count_streets_per_node",
                return_value={1: 2, 2: 2},
            ),
            patch("osmnx.projection.project_geometry") as mock_proj,
        ):
            mock_proj.return_value = (polygon, "EPSG:32610")
            result = await aio_graph.graph_from_polygon(polygon)

        assert isinstance(result, nx.MultiDiGraph)

    async def test_graph_from_bbox(self) -> None:
        """graph_from_bbox delegates to graph_from_polygon."""
        mock_graph = _make_mock_graph()

        with patch(
            "osmnx_async.graph.graph_from_polygon",
            new_callable=AsyncMock,
            return_value=mock_graph,
        ):
            result = await aio_graph.graph_from_bbox(
                (-122.5, 37.7, -122.4, 37.8),
            )

        assert isinstance(result, nx.MultiDiGraph)

    async def test_graph_from_address(self) -> None:
        """graph_from_address geocodes then delegates to graph_from_point."""
        mock_graph = _make_mock_graph()

        with (
            patch(
                "osmnx_async.geocoder.geocode",
                new_callable=AsyncMock,
                return_value=(37.75, -122.45),
            ),
            patch(
                "osmnx_async.graph.graph_from_point",
                new_callable=AsyncMock,
                return_value=mock_graph,
            ),
        ):
            result = await aio_graph.graph_from_address("test address", dist=1000)

        assert isinstance(result, nx.MultiDiGraph)

    async def test_graph_from_place(self) -> None:
        """graph_from_place geocodes to GDF then delegates to graph_from_polygon."""
        mock_graph = _make_mock_graph()
        mock_gdf = MagicMock()
        mock_gdf.union_all.return_value = box(-122.5, 37.7, -122.4, 37.8)

        with (
            patch(
                "osmnx_async.geocoder.geocode_to_gdf",
                new_callable=AsyncMock,
                return_value=mock_gdf,
            ),
            patch(
                "osmnx_async.graph.graph_from_polygon",
                new_callable=AsyncMock,
                return_value=mock_graph,
            ),
        ):
            result = await aio_graph.graph_from_place("test place")

        assert isinstance(result, nx.MultiDiGraph)
