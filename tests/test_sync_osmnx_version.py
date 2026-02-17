# ruff: noqa: S101
"""Tests for scripts/sync_osmnx_version.py."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

import httpx
import pytest

from scripts.sync_osmnx_version import get_latest_osmnx_version, pin_osmnx_version

SAMPLE_PYPI_RESPONSE = {
    "info": {"version": "2.1.0"},
}


@pytest.fixture
def tmp_pyproject(tmp_path: Path) -> Path:
    """Create a temporary pyproject.toml with an osmnx dependency."""
    p = tmp_path / "pyproject.toml"
    p.write_text(
        '[project]\nname = "test"\ndependencies = [\n    "osmnx>=2.0,<3.0",\n]\n'
    )
    return p


def test_get_latest_osmnx_version() -> None:
    mock_response = httpx.Response(
        200,
        json=SAMPLE_PYPI_RESPONSE,
        request=httpx.Request("GET", "https://pypi.org/pypi/osmnx/json"),
    )
    with patch("scripts.sync_osmnx_version.httpx.get", return_value=mock_response):
        version = get_latest_osmnx_version()
    assert version == "2.1.0"


def test_pin_osmnx_version(tmp_pyproject: Path) -> None:
    with patch("scripts.sync_osmnx_version.PYPROJECT", tmp_pyproject):
        pin_osmnx_version("2.1.0")

    content = tmp_pyproject.read_text()
    assert '"osmnx==2.1.0"' in content
    # Ensure no leftover range specifier
    assert ">=2.0" not in content


def test_pin_osmnx_version_already_pinned(tmp_pyproject: Path) -> None:
    """Pinning over an already-pinned version should work."""
    tmp_pyproject.write_text(
        '[project]\nname = "test"\ndependencies = [\n    "osmnx==2.0.7",\n]\n'
    )
    with patch("scripts.sync_osmnx_version.PYPROJECT", tmp_pyproject):
        pin_osmnx_version("2.1.0")

    content = tmp_pyproject.read_text()
    assert '"osmnx==2.1.0"' in content
    assert "==2.0.7" not in content


def test_pin_does_not_corrupt_project_name(tmp_path: Path) -> None:
    """Pinning should not touch the project name even if it contains 'osmnx'."""
    p = tmp_path / "pyproject.toml"
    p.write_text(
        '[project]\nname = "osmnx-async"\ndependencies = [\n    "osmnx>=2.0,<3.0",\n]\n'
    )
    with patch("scripts.sync_osmnx_version.PYPROJECT", p):
        pin_osmnx_version("2.1.0")

    content = p.read_text()
    assert 'name = "osmnx-async"' in content
    assert '"osmnx==2.1.0"' in content


def test_pin_osmnx_version_missing_dep(tmp_path: Path) -> None:
    """Should raise if osmnx dependency is not found."""
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "test"\ndependencies = []\n')
    with patch("scripts.sync_osmnx_version.PYPROJECT", p), pytest.raises(RuntimeError):
        pin_osmnx_version("2.1.0")
