# ruff: noqa: PLR2004, S101
"""Test osmnx compatibility validation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from osmnx_async._compat import OsmnxCompatibilityError
from osmnx_async._compat import check_osmnx_compatibility


class TestOsmnxCompat:
    """Test osmnx compatibility checking."""

    def test_check_passes_with_current_osmnx(self) -> None:
        """Compatibility check passes with the currently installed osmnx."""
        # Should not raise
        check_osmnx_compatibility()

    def test_check_fails_with_old_version(self) -> None:
        """Compatibility check fails when osmnx version is too old."""
        with (
            patch("osmnx.__version__", "1.9.0"),
            pytest.raises(OsmnxCompatibilityError, match="requires osmnx>=2.0.0"),
        ):
            check_osmnx_compatibility()

    def test_check_fails_with_missing_function(self) -> None:
        """Compatibility check fails when a required internal is missing."""
        import osmnx._http as _http_mod

        original = _http_mod._retrieve_from_cache
        try:
            delattr(_http_mod, "_retrieve_from_cache")
            with pytest.raises(OsmnxCompatibilityError, match="Missing"):
                check_osmnx_compatibility()
        finally:
            _http_mod._retrieve_from_cache = original

    def test_check_warns_on_signature_change(self, caplog: pytest.LogCaptureFixture) -> None:
        """Compatibility check logs a warning when a signature changes."""
        import osmnx._http as _http_mod

        original = _http_mod._hostname_from_url

        def _fake_hostname_from_url(url: str, extra: str = "") -> str:
            return original(url)

        try:
            _http_mod._hostname_from_url = _fake_hostname_from_url
            with caplog.at_level("WARNING", logger="osmnx_async"):
                check_osmnx_compatibility()
            assert "signature changed" in caplog.text
        finally:
            _http_mod._hostname_from_url = original
