# ruff: noqa: PLR2004, S101
"""Test async elevation module with mocked HTTP."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import networkx as nx

from osmnx_async import elevation as aio_elevation


def _make_elevation_graph() -> nx.MultiDiGraph:
    """Create a small graph for elevation tests."""
    G = nx.MultiDiGraph()
    G.add_node(1, x=-122.4194, y=37.7749)
    G.add_node(2, x=-122.4090, y=37.7850)
    G.add_edge(1, 2, length=100)
    return G


class TestAsyncElevation:
    """Test async elevation functions with mocked HTTP."""

    async def test_add_node_elevations_google_concurrent(self) -> None:
        """add_node_elevations_google with pause=0 uses asyncio.gather."""
        G = _make_elevation_graph()
        mock_response = {
            "results": [
                {"elevation": 10.0},
                {"elevation": 20.0},
            ],
        }

        with patch(
            "osmnx_async.elevation._elevation_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await aio_elevation.add_node_elevations_google(G, pause=0)

        assert "elevation" in result.nodes[1]
        assert "elevation" in result.nodes[2]

    async def test_add_node_elevations_google_sequential(self) -> None:
        """add_node_elevations_google with pause>0 runs sequentially."""
        G = _make_elevation_graph()
        mock_response = {
            "results": [
                {"elevation": 15.0},
                {"elevation": 25.0},
            ],
        }

        with patch(
            "osmnx_async.elevation._elevation_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await aio_elevation.add_node_elevations_google(G, pause=0.01)

        assert result.nodes[1]["elevation"] == 15.0
        assert result.nodes[2]["elevation"] == 25.0

    async def test_elevation_request_uses_cache(self) -> None:
        """_elevation_request returns cached data when available."""
        cached_data = {"results": [{"elevation": 42.0}]}

        with patch(
            "osmnx_async._http._async_retrieve_from_cache",
            new_callable=AsyncMock,
            return_value=cached_data,
        ):
            from osmnx_async.elevation import _elevation_request

            result = await _elevation_request("https://example.com/elev", 0)

        assert result == cached_data
