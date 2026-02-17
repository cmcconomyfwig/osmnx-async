# ruff: noqa: S101
"""Verify osmnx_async exports at least the same public symbols as osmnx.

When osmnx adds new public functions, this test fails with a clear message
so the decision to wrap or exclude is explicit rather than an oversight.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

# ── Mapping of osmnx submodules to their osmnx_async counterparts ────────
_SUBMODULE_PAIRS: list[tuple[str, str]] = [
    ("osmnx.elevation", "osmnx_async.elevation"),
    ("osmnx.features", "osmnx_async.features"),
    ("osmnx.geocoder", "osmnx_async.geocoder"),
    ("osmnx.graph", "osmnx_async.graph"),
]

# ── Functions that osmnx_async intentionally does NOT wrap ───────────────
# All local-I/O or pure-computation functions with no network requests.
_KNOWN_EXCLUSIONS: dict[str, set[str]] = {
    "osmnx.elevation": {"add_node_elevations_raster", "add_edge_grades"},
    "osmnx.features": {"features_from_xml"},
    "osmnx.geocoder": set(),
    "osmnx.graph": {"graph_from_xml"},
}


def _public_functions(module_path: str) -> set[str]:
    """Return the set of public function names defined in a module."""
    mod = importlib.import_module(module_path)
    return {
        name
        for name in dir(mod)
        if not name.startswith("_")
        and inspect.isfunction(getattr(mod, name))
        and getattr(mod, name).__module__ == module_path
    }


def _submodule_cases() -> list[tuple[str, str, str]]:
    """Generate (osmnx_module, async_module, symbol) test cases."""
    cases = []
    for osmnx_mod, async_mod in _SUBMODULE_PAIRS:
        excluded = _KNOWN_EXCLUSIONS.get(osmnx_mod, set())
        for symbol in sorted(_public_functions(osmnx_mod) - excluded):
            cases.append((osmnx_mod, async_mod, symbol))
    return cases


def _exclusion_cases() -> list[tuple[str, str]]:
    """Generate (osmnx_module, symbol) for every known exclusion."""
    return [
        (osmnx_mod, symbol)
        for osmnx_mod, excluded in sorted(_KNOWN_EXCLUSIONS.items())
        for symbol in sorted(excluded)
    ]


class TestExportCoverage:
    """Verify osmnx_async re-exports all wrapped osmnx public symbols."""

    @pytest.mark.parametrize(
        ("osmnx_mod", "async_mod", "symbol"),
        _submodule_cases(),
    )
    def test_submodule_exports_symbol(
        self, osmnx_mod: str, async_mod: str, symbol: str
    ) -> None:
        """Async submodule exposes the same symbol as osmnx."""
        async_module = importlib.import_module(async_mod)
        assert hasattr(async_module, symbol), (
            f"{async_mod} is missing '{symbol}' which is public in {osmnx_mod}. "
            f"If intentional, add it to _KNOWN_EXCLUSIONS['{osmnx_mod}']."
        )

    @pytest.mark.parametrize(
        ("osmnx_mod", "async_mod", "symbol"),
        _submodule_cases(),
    )
    def test_flat_namespace_exports_symbol(
        self, osmnx_mod: str, async_mod: str, symbol: str
    ) -> None:
        """Top-level osmnx_async namespace re-exports the symbol."""
        import osmnx_async

        assert hasattr(osmnx_async, symbol), (
            f"osmnx_async.__init__ is missing flat re-export of '{symbol}' "
            f"(defined in {async_mod}). Add it to __init__.py imports."
        )

    @pytest.mark.parametrize(("osmnx_mod", "symbol"), _exclusion_cases())
    def test_exclusion_still_exists_in_osmnx(
        self, osmnx_mod: str, symbol: str
    ) -> None:
        """Excluded symbol still exists in osmnx (exclusion is not stale)."""
        mod = importlib.import_module(osmnx_mod)
        assert hasattr(mod, symbol), (
            f"Excluded symbol '{symbol}' no longer exists in {osmnx_mod}. "
            f"Remove it from _KNOWN_EXCLUSIONS."
        )
