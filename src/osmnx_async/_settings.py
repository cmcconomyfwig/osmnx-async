"""Async-safe settings accessor for osmnx configuration.

Provides per-task isolation via ``contextvars.ContextVar`` so that concurrent
``asyncio.Task`` objects can override settings without affecting each other.
Falls back to the module-level globals in ``osmnx.settings``.
"""

from __future__ import annotations

import contextvars
from typing import Any

import osmnx.settings as _osmnx_settings

_settings_overrides: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "_settings_overrides",
    default=None,
)


def get(name: str) -> Any:  # noqa: ANN401
    """Get a setting value with per-task override support for async safety.

    Checks the per-task override dict first, then falls back to
    ``osmnx.settings.<name>``.

    Parameters
    ----------
    name
        The name of the setting to retrieve.

    Returns
    -------
    value
        The setting's current value.
    """
    overrides = _settings_overrides.get()
    if overrides is not None and name in overrides:
        return overrides[name]
    return getattr(_osmnx_settings, name)
