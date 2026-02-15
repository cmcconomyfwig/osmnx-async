"""Validate that the installed osmnx version exposes the internals we need."""

from __future__ import annotations

import importlib
import inspect
import logging

logger = logging.getLogger("osmnx_async")

MIN_OSMNX_VERSION = "2.0.0"


class OsmnxCompatibilityError(ImportError):
    """Raised when osmnx does not expose expected internal APIs."""


# (module_path, function_name, expected_param_names or None)
_REQUIRED_INTERNALS: list[tuple[str, str, list[str] | None]] = [
    ("osmnx._http", "_retrieve_from_cache", ["url"]),
    ("osmnx._http", "_save_to_cache", ["url", "response_json", "ok"]),
    ("osmnx._http", "_hostname_from_url", ["url"]),
    ("osmnx._overpass", "_get_network_filter", ["network_type"]),
    ("osmnx._overpass", "_make_overpass_settings", None),
    ("osmnx._overpass", "_make_overpass_polygon_coord_strs", ["polygon"]),
    ("osmnx._overpass", "_create_overpass_features_query", None),
    ("osmnx.graph", "_create_graph", ["response_jsons", "bidirectional"]),
    ("osmnx.features", "_create_gdf", ["response_jsons", "polygon", "tags"]),
    ("osmnx.geocoder", "_get_first_polygon", ["results"]),
]


def check_osmnx_compatibility() -> None:
    """Validate osmnx version and internal API availability.

    Raises
    ------
    OsmnxCompatibilityError
        If required internal functions are missing from the installed osmnx.
    """
    import osmnx
    from packaging.version import Version

    raw_version = osmnx.__version__.replace("dev", ".dev0")
    installed = Version(raw_version)
    minimum = Version(MIN_OSMNX_VERSION)
    if installed < minimum:
        msg = (
            f"osmnx-async requires osmnx>={MIN_OSMNX_VERSION}, "
            f"but {osmnx.__version__} is installed."
        )
        raise OsmnxCompatibilityError(msg)

    missing: list[str] = []
    for module_path, func_name, expected_params in _REQUIRED_INTERNALS:
        try:
            mod = importlib.import_module(module_path)
            fn = getattr(mod, func_name)
        except (ImportError, AttributeError):
            missing.append(f"{module_path}.{func_name}")
            continue

        if expected_params is not None and callable(fn):
            sig = inspect.signature(fn)
            actual_params = list(sig.parameters.keys())
            if actual_params != expected_params:
                logger.warning(
                    "osmnx internal %s.%s signature changed: expected %s, got %s",
                    module_path,
                    func_name,
                    expected_params,
                    actual_params,
                )

    if missing:
        msg = (
            "osmnx-async depends on osmnx internals that are missing "
            "in the installed version. Missing: " + ", ".join(missing)
        )
        raise OsmnxCompatibilityError(msg)
