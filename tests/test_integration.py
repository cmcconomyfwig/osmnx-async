# ruff: noqa: PLR2004, S101, TC002
"""Integration tests comparing sync osmnx vs async osmnx_async results.

These tests make REAL network requests (or use cached responses) to verify
that the async wrapper produces identical results to the sync original.

Run with: uv run pytest tests/test_integration.py -v
"""

from __future__ import annotations

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
import pytest

import osmnx_async

# Use a very small, stable area to minimize API load.
# Piedmont, CA is a tiny city entirely surrounded by Oakland.
PLACE = "Piedmont, California, USA"
BBOX = (-122.232, 37.819, -122.211, 37.832)  # small bbox inside Piedmont
POINT = (37.824, -122.222)  # center of Piedmont
DIST = 500  # meters
ADDRESS = "399 Highland Ave, Piedmont, CA"
TAGS = {"amenity": "school"}

# Mark all tests as integration so they can be skipped with -m "not integration"
pytestmark = pytest.mark.integration


def _graphs_equivalent(g_sync: nx.MultiDiGraph, g_async: nx.MultiDiGraph) -> None:
    """Assert two graphs have identical topology and attributes."""
    assert len(g_sync) == len(g_async), (
        f"Node count mismatch: sync={len(g_sync)}, async={len(g_async)}"
    )
    assert len(g_sync.edges) == len(g_async.edges), (
        f"Edge count mismatch: sync={len(g_sync.edges)}, async={len(g_async.edges)}"
    )
    assert set(g_sync.nodes) == set(g_async.nodes), "Node sets differ"
    assert set(g_sync.edges) == set(g_async.edges), "Edge sets differ"

    # Compare node attributes
    for node in g_sync.nodes:
        sync_data = g_sync.nodes[node]
        async_data = g_async.nodes[node]
        assert sync_data == async_data, f"Node {node} attributes differ"

    # Compare edge attributes
    for u, v, k in g_sync.edges:
        sync_data = g_sync.edges[u, v, k]
        async_data = g_async.edges[u, v, k]
        assert sync_data == async_data, f"Edge ({u},{v},{k}) attributes differ"


def _gdfs_equivalent(gdf_sync: gpd.GeoDataFrame, gdf_async: gpd.GeoDataFrame) -> None:
    """Assert two GeoDataFrames have identical content."""
    assert len(gdf_sync) == len(gdf_async), (
        f"Row count mismatch: sync={len(gdf_sync)}, async={len(gdf_async)}"
    )
    assert set(gdf_sync.columns) == set(gdf_async.columns), "Column sets differ"

    # Sort both by index for stable comparison
    gdf_s = gdf_sync.sort_index()
    gdf_a = gdf_async.sort_index()

    pd.testing.assert_frame_equal(
        gdf_s.reset_index(drop=True),
        gdf_a.reset_index(drop=True),
        check_like=True,
    )


# ---------------------------------------------------------------------------
# Geocoder
# ---------------------------------------------------------------------------


class TestGeocoderIntegration:
    """Compare sync vs async geocoder results."""

    async def test_geocode(self) -> None:
        """geocode returns identical (lat, lon) tuple."""
        sync_result = ox.geocoder.geocode(ADDRESS)
        async_result = await osmnx_async.geocode(ADDRESS)

        assert sync_result == async_result

    async def test_geocode_to_gdf(self) -> None:
        """geocode_to_gdf returns identical GeoDataFrame."""
        sync_gdf = ox.geocoder.geocode_to_gdf(PLACE)
        async_gdf = await osmnx_async.geocode_to_gdf(PLACE)

        assert len(sync_gdf) == len(async_gdf)
        assert set(sync_gdf.columns) == set(async_gdf.columns)
        # Compare geometry: both should resolve to the same Piedmont boundary
        assert sync_gdf.geometry.iloc[0].equals(async_gdf.geometry.iloc[0])


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


class TestGraphIntegration:
    """Compare sync vs async graph results."""

    async def test_graph_from_bbox(self) -> None:
        """graph_from_bbox returns identical graph."""
        sync_g = ox.graph.graph_from_bbox(BBOX, network_type="drive")
        async_g = await osmnx_async.graph_from_bbox(BBOX, network_type="drive")

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_from_point(self) -> None:
        """graph_from_point returns identical graph."""
        sync_g = ox.graph.graph_from_point(POINT, DIST, network_type="walk")
        async_g = await osmnx_async.graph_from_point(POINT, DIST, network_type="walk")

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_from_address(self) -> None:
        """graph_from_address returns identical graph."""
        sync_g = ox.graph.graph_from_address(ADDRESS, DIST, network_type="drive")
        async_g = await osmnx_async.graph_from_address(ADDRESS, DIST, network_type="drive")

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_from_place(self) -> None:
        """graph_from_place returns identical graph."""
        sync_g = ox.graph.graph_from_place(PLACE, network_type="drive")
        async_g = await osmnx_async.graph_from_place(PLACE, network_type="drive")

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_from_polygon(self) -> None:
        """graph_from_polygon returns identical graph."""
        polygon = ox.utils_geo.bbox_to_poly(BBOX)

        sync_g = ox.graph.graph_from_polygon(polygon, network_type="drive")
        async_g = await osmnx_async.graph_from_polygon(polygon, network_type="drive")

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_unsimplified(self) -> None:
        """graph_from_bbox with simplify=False returns identical graph."""
        sync_g = ox.graph.graph_from_bbox(BBOX, network_type="drive", simplify=False)
        async_g = await osmnx_async.graph_from_bbox(
            BBOX, network_type="drive", simplify=False,
        )

        _graphs_equivalent(sync_g, async_g)

    async def test_graph_retain_all(self) -> None:
        """graph_from_bbox with retain_all=True returns identical graph."""
        sync_g = ox.graph.graph_from_bbox(BBOX, network_type="drive", retain_all=True)
        async_g = await osmnx_async.graph_from_bbox(
            BBOX, network_type="drive", retain_all=True,
        )

        _graphs_equivalent(sync_g, async_g)


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


class TestFeaturesIntegration:
    """Compare sync vs async features results."""

    async def test_features_from_bbox(self) -> None:
        """features_from_bbox returns identical GeoDataFrame."""
        sync_gdf = ox.features.features_from_bbox(BBOX, tags=TAGS)
        async_gdf = await osmnx_async.features_from_bbox(BBOX, tags=TAGS)

        _gdfs_equivalent(sync_gdf, async_gdf)

    async def test_features_from_point(self) -> None:
        """features_from_point returns identical GeoDataFrame."""
        # Use broader tags to ensure results exist in the small radius
        point_tags = {"building": True}
        sync_gdf = ox.features.features_from_point(POINT, tags=point_tags, dist=DIST)
        async_gdf = await osmnx_async.features_from_point(POINT, tags=point_tags, dist=DIST)

        _gdfs_equivalent(sync_gdf, async_gdf)

    async def test_features_from_place(self) -> None:
        """features_from_place returns identical GeoDataFrame."""
        sync_gdf = ox.features.features_from_place(PLACE, tags=TAGS)
        async_gdf = await osmnx_async.features_from_place(PLACE, tags=TAGS)

        _gdfs_equivalent(sync_gdf, async_gdf)

    async def test_features_from_polygon(self) -> None:
        """features_from_polygon returns identical GeoDataFrame."""
        polygon = ox.utils_geo.bbox_to_poly(BBOX)

        sync_gdf = ox.features.features_from_polygon(polygon, tags=TAGS)
        async_gdf = await osmnx_async.features_from_polygon(polygon, tags=TAGS)

        _gdfs_equivalent(sync_gdf, async_gdf)
