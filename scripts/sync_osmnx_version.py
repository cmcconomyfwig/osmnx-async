"""Fetch the latest osmnx version from PyPI and pin it in pyproject.toml.

Run directly:  uv run python scripts/sync_osmnx_version.py
Or use:        make sync_osmnx_version
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
PYPI_URL = "https://pypi.org/pypi/osmnx/json"


def get_latest_osmnx_version() -> str:
    """Query PyPI for the latest osmnx release version."""
    resp = httpx.get(PYPI_URL, timeout=30)
    resp.raise_for_status()
    version: str = resp.json()["info"]["version"]
    return version


def pin_osmnx_version(version: str) -> None:
    """Rewrite the osmnx dependency in pyproject.toml to pin an exact version."""
    content = PYPROJECT.read_text()
    new_content, count = re.subn(
        r'"osmnx[><=!~][^"]*"',
        f'"osmnx=={version}"',
        content,
    )
    if count == 0:
        raise RuntimeError("Could not find osmnx dependency in pyproject.toml")
    PYPROJECT.write_text(new_content)
    logger.info("Pinned osmnx==%s in %s", version, PYPROJECT)


def sync_osmnx_version() -> str:
    """Fetch the latest version and pin it. Returns the version string."""
    version = get_latest_osmnx_version()
    pin_osmnx_version(version)
    print(f"osmnx pinned to =={version} in pyproject.toml")  # noqa: T201
    return version


if __name__ == "__main__":
    sync_osmnx_version()
