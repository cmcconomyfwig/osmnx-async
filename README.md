# osmnx-async

Async versions of [osmnx](https://github.com/gboeing/osmnx)'s network-bound functions. Same names, same parameters, same return types — just add `await`.

## Why?

osmnx makes synchronous HTTP requests to the Overpass and Nominatim APIs. If you're building an async application (FastAPI, aiohttp, Discord bots, data pipelines with `asyncio.gather`), those blocking calls stall your entire event loop.

**osmnx-async** replaces only the HTTP layer with [httpx](https://www.python-httpx.org/) `AsyncClient`. All business logic — graph construction, simplification, GeoDataFrame creation — is delegated to osmnx itself. You get identical results, verified by integration tests that compare every node, edge, and attribute.

## Installation

```bash
pip install osmnx-async
```

Requires Python 3.11+ and osmnx 2.x.

## Quick start

```python
import asyncio
import osmnx_async as ox

async def main():
    # Exactly the same call you'd make with osmnx — just awaited
    G = await ox.graph_from_place("Piedmont, CA, USA", network_type="drive")
    print(f"{len(G)} nodes, {len(G.edges)} edges")

asyncio.run(main())
```

## Migrating from osmnx

The function signatures are identical. Add `await` and swap the import:

```python
# Before (sync)
import osmnx as ox

G = ox.graph_from_address("1600 Pennsylvania Ave, Washington DC", dist=500)
gdf = ox.features_from_place("Manhattan, NY", tags={"building": True})
point = ox.geocode("London, UK")
```

```python
# After (async)
import osmnx_async as ox

G = await ox.graph_from_address("1600 Pennsylvania Ave, Washington DC", dist=500)
gdf = await ox.features_from_place("Manhattan, NY", tags={"building": True})
point = await ox.geocode("London, UK")
```

Module-level access works too:

```python
from osmnx_async import graph, features, geocoder

G = await graph.graph_from_place("Piedmont, CA, USA")
gdf = await features.features_from_bbox(bbox, tags={"amenity": True})
point = await geocoder.geocode("Tokyo, Japan")
```

## Settings

osmnx-async reads settings directly from `osmnx.settings`. Configure them the same way you always have:

```python
import osmnx as ox

ox.settings.use_cache = True
ox.settings.cache_folder = "./my_cache"
ox.settings.overpass_rate_limit = True
ox.settings.requests_timeout = 300
```

The cache is shared — a response cached by a sync osmnx call is reused by osmnx-async, and vice versa.

## Concurrent requests

The main reason to go async. Fetch multiple graphs in parallel instead of sequentially:

```python
import asyncio
import osmnx_async as ox

async def main():
    cities = ["Piedmont, CA, USA", "Berkeley, CA, USA", "Emeryville, CA, USA"]
    graphs = await asyncio.gather(
        *(ox.graph_from_place(c, network_type="drive") for c in cities)
    )
    for city, G in zip(cities, graphs):
        print(f"{city}: {len(G)} nodes")

asyncio.run(main())
```

Note: Overpass and Nominatim enforce rate limits. osmnx-async respects these automatically (Nominatim: 1 req/sec per hostname, Overpass: server-side slot management). Concurrent tasks will wait as needed.

## Available functions

Every osmnx function that makes HTTP requests has an async equivalent:

| Module | Function | What it does |
|---|---|---|
| `graph` | `graph_from_bbox` | Graph within bounding box |
| `graph` | `graph_from_point` | Graph within distance of point |
| `graph` | `graph_from_address` | Graph within distance of address |
| `graph` | `graph_from_place` | Graph within place boundary |
| `graph` | `graph_from_polygon` | Graph within polygon |
| `features` | `features_from_bbox` | OSM features within bounding box |
| `features` | `features_from_point` | OSM features within distance of point |
| `features` | `features_from_address` | OSM features within distance of address |
| `features` | `features_from_place` | OSM features within place boundary |
| `features` | `features_from_polygon` | OSM features within polygon |
| `geocoder` | `geocode` | Place name to (lat, lon) |
| `geocoder` | `geocode_to_gdf` | Place name to GeoDataFrame |
| `elevation` | `add_node_elevations_google` | Add elevation data to graph nodes |

Functions that don't make network requests (plotting, stats, simplification, IO, routing, etc.) are pure computation and don't need async variants. Use them directly from osmnx as usual.

## Compatibility

osmnx-async validates at import time that the osmnx internals it depends on are present and have the expected signatures. If osmnx releases a breaking change, you'll get a clear error at `import osmnx_async` rather than a cryptic failure deep in a call stack:

```
OsmnxCompatibilityError: osmnx-async depends on osmnx internals that are
missing in the installed version. Missing: osmnx.graph._create_graph
```

Supported: osmnx >= 2.0, < 3.0.

## Development

```bash
git clone https://github.com/cmcconomyfwig/osmnx-async.git
cd osmnx-async
uv sync

# Unit tests (mocked, fast)
make test

# Integration tests (real API calls, slower)
make test-integration

# Build (syncs version from installed osmnx, then builds wheel)
make build
```

## License

MIT
