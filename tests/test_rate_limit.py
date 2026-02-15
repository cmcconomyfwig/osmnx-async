# ruff: noqa: PLR2004, S101
"""Test the async rate limiter."""

from __future__ import annotations

import time

from osmnx_async._rate_limit import AsyncRateLimiter


class TestAsyncRateLimiter:
    """Test the AsyncRateLimiter."""

    async def test_rate_limiter_enforces_interval(self) -> None:
        """Rate limiter enforces minimum interval between calls."""
        limiter = AsyncRateLimiter()
        start = time.monotonic()

        await limiter.wait("test-host", min_interval=0.1)
        await limiter.wait("test-host", min_interval=0.1)

        elapsed = time.monotonic() - start
        assert elapsed >= 0.1

    async def test_rate_limiter_different_hosts_independent(self) -> None:
        """Different hostnames are rate-limited independently."""
        limiter = AsyncRateLimiter()
        start = time.monotonic()

        await limiter.wait("host-a", min_interval=0.5)
        await limiter.wait("host-b", min_interval=0.5)

        elapsed = time.monotonic() - start
        # both should complete nearly immediately since they're independent
        assert elapsed < 0.4
