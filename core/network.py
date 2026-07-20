# openagent/core/network.py
"""
Lightweight connectivity check.
Pings a DNS server (no HTTP overhead).
Returns True/False — used by the router to gate online tools.

The result is cached for a short TTL (monotonic clock): the router
calls this on EVERY online-routed request, and without the cache each
request pays a fresh TCP connect — or a multi-second timeout when
offline. Both online and offline results are cached; pass
force_refresh=True to bypass the cache.
"""

from __future__ import annotations
import socket
import asyncio
import threading
import time

from openagent.config import settings

# ── TTL cache (module-level, shared across event loops/threads) ──
_CACHE_TTL_SECONDS = 30.0
_cache_lock = threading.Lock()
_cached_result: bool | None = None
_cached_at: float = 0.0


def reset_connectivity_cache() -> None:
    """Forget the cached result (used by tests and force-refresh paths)."""
    global _cached_result, _cached_at
    with _cache_lock:
        _cached_result = None
        _cached_at = 0.0


async def check_connectivity(force_refresh: bool = False) -> bool:
    """
    Non-blocking check: can we reach the configured DNS host?
    Result is cached for ~30 seconds; force_refresh=True re-probes now.
    """
    global _cached_result, _cached_at

    with _cache_lock:
        if (
            not force_refresh
            and _cached_result is not None
            and time.monotonic() - _cached_at < _CACHE_TTL_SECONDS
        ):
            return _cached_result

    cfg = settings.network
    loop = asyncio.get_running_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                None,
                _tcp_ping,
                cfg.check_host,
                cfg.check_port,
                cfg.check_timeout_seconds,
            ),
            timeout=cfg.check_timeout_seconds + 1,
        )
        result = True
    except Exception:
        result = False

    with _cache_lock:
        _cached_result = result
        _cached_at = time.monotonic()
    return result


def _tcp_ping(host: str, port: int, timeout: int) -> None:
    """Blocking TCP connect — runs in thread pool via executor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    finally:
        sock.close()
