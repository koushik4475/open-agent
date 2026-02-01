# openagent/core/network.py
"""
Lightweight connectivity check.
Pings a DNS server (no HTTP overhead).
Returns True/False — used by the router to gate online tools.
"""

from __future__ import annotations
import socket
import asyncio

from openagent.config import settings


async def check_connectivity() -> bool:
    """
    Non-blocking check: can we reach the configured DNS host?
    """
    cfg = settings.network
    loop = asyncio.get_event_loop()
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
        return True
    except Exception:
        return False


def _tcp_ping(host: str, port: int, timeout: int) -> None:
    """Blocking TCP connect — runs in thread pool via executor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    finally:
        sock.close()
