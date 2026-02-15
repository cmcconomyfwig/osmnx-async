"""Sync _version.py with the installed osmnx version.

Run before building:  uv run python scripts/sync_version.py
Or use:               make build
"""

from __future__ import annotations

import logging
from pathlib import Path

import osmnx

logger = logging.getLogger(__name__)

VERSION_FILE = Path(__file__).resolve().parent.parent / "src" / "osmnx_async" / "_version.py"


def sync_version() -> None:
    """Write the installed osmnx version into _version.py."""
    version = osmnx.__version__
    content = f'__version__ = "{version}"\n'
    VERSION_FILE.write_text(content)
    logger.info("Updated %s to %s", VERSION_FILE, version)
    print(f"_version.py → {version}")  # noqa: T201


if __name__ == "__main__":
    sync_version()
