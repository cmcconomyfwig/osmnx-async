"""Async-safe settings accessor for osmnx configuration.

Provides per-task isolation via ``contextvars.ContextVar`` so that concurrent
``asyncio.Task`` objects can override settings without affecting each other.
Falls back to the module-level globals in ``osmnx.settings``.

Supports the familiar attribute-access pattern::

    import osmnx_async as oxa
    oxa.settings.use_cache = False        # per-task override (contextvar)
    print(oxa.settings.use_cache)         # reads override, falls back to osmnx.settings
    oxa.settings.get("use_cache")         # same, function form
"""

from __future__ import annotations

import contextvars
import sys
import types
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

import osmnx.settings as _osmnx_settings
import osmnx.utils as _osmnx_utils

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


@contextmanager
def _apply_overrides() -> Generator[None, None, None]:
    """Temporarily apply contextvar overrides to ``osmnx.settings`` for sync calls.

    Safe for synchronous blocks on the event loop thread (no ``await`` inside
    the ``with`` block).  **Not** safe around ``asyncio.to_thread()`` calls
    because other coroutines can run during the ``await``.
    """
    overrides = _settings_overrides.get()
    if overrides is None or len(overrides) == 0:
        yield
        return

    originals = {}
    for key, value in overrides.items():
        originals[key] = getattr(_osmnx_settings, key)
        setattr(_osmnx_settings, key, value)
    try:
        yield
    finally:
        for key, value in originals.items():
            setattr(_osmnx_settings, key, value)


def log(
    message: str,
    level: int | None = None,
    name: str | None = None,
    filename: str | None = None,
) -> None:
    """Contextvar-aware wrapper around ``osmnx.utils.log``."""
    with _apply_overrides():
        _osmnx_utils.log(message, level=level, name=name, filename=filename)


class _SettingsProxy(types.ModuleType):
    """Module replacement that intercepts attribute access for contextvar support.

    * Reads check the per-task contextvar overrides, then fall back to
      ``osmnx.settings``.
    * Writes to recognised osmnx setting names are stored in the contextvar
      override dict rather than on the module instance, giving per-task
      isolation for free.
    """

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        # Only called when normal instance/class lookup misses.
        # Proxy recognised osmnx settings through the contextvar-aware getter.
        if hasattr(_osmnx_settings, name):
            return get(name)
        msg = f"module {self.__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        # Route recognised osmnx settings into the contextvar override dict.
        if hasattr(_osmnx_settings, name):
            overrides = _settings_overrides.get()
            if overrides is None:
                overrides = {}
                _settings_overrides.set(overrides)
            overrides[name] = value
        else:
            # Module internals (__name__, __spec__, etc.) and our own attrs.
            super().__setattr__(name, value)

    def __dir__(self) -> list[str]:
        # Merge module attrs with osmnx settings names for tab-completion.
        own = set(super().__dir__())
        own.update(name for name in dir(_osmnx_settings) if not name.startswith("_"))
        return sorted(own)


# ---------------------------------------------------------------------------
# Replace this module in sys.modules with the proxy so that attribute access
# on ``osmnx_async.settings`` is intercepted.
# ---------------------------------------------------------------------------
_self = sys.modules[__name__]
_proxy = _SettingsProxy(__name__)
_proxy.__doc__ = __doc__
_proxy.__package__ = getattr(_self, "__package__", None)
_proxy.__spec__ = getattr(_self, "__spec__", None)
_proxy.__file__ = getattr(_self, "__file__", None)
_proxy.__loader__ = getattr(_self, "__loader__", None)

# Expose the public API on the proxy instance so that both
# ``from osmnx_async._settings import get`` and
# ``osmnx_async.settings.get(...)`` keep working.
_proxy.get = get  # type: ignore[attr-defined]
_proxy._settings_overrides = _settings_overrides  # type: ignore[attr-defined]
_proxy._apply_overrides = _apply_overrides  # type: ignore[attr-defined]
_proxy.log = log  # type: ignore[attr-defined]

sys.modules[__name__] = _proxy
