# ruff: noqa: E402
"""Async alternatives to osmnx's IO-bound public API functions.

Provides ``async`` versions of all osmnx functions that perform network
requests. Uses ``httpx`` as its HTTP transport library.

Usage example::

    import asyncio
    import osmnx_async

    async def main():
        G = await osmnx_async.graph_from_place("Piedmont, CA, USA")

    asyncio.run(main())
"""

from __future__ import annotations

from importlib.metadata import version as _pkg_version

# Validate osmnx compatibility at import time
from ._compat import check_osmnx_compatibility

check_osmnx_compatibility()

# Package version (set at build time via _version.py)
__version__: str = _pkg_version("osmnx-async")

# Public submodules
from . import _settings as settings  # noqa: F401
from . import elevation as elevation
from . import features as features
from . import geocoder as geocoder
from . import graph as graph

# Flat namespace re-exports
from .elevation import add_node_elevations_google as add_node_elevations_google
from .features import features_from_address as features_from_address
from .features import features_from_bbox as features_from_bbox
from .features import features_from_place as features_from_place
from .features import features_from_point as features_from_point
from .features import features_from_polygon as features_from_polygon
from .geocoder import geocode as geocode
from .geocoder import geocode_to_gdf as geocode_to_gdf
from .graph import graph_from_address as graph_from_address
from .graph import graph_from_bbox as graph_from_bbox
from .graph import graph_from_place as graph_from_place
from .graph import graph_from_point as graph_from_point
from .graph import graph_from_polygon as graph_from_polygon
