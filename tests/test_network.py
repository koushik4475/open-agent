# openagent/tests/test_network.py
"""
Tests for the network connectivity checker.
"""

import pytest
from unittest.mock import patch, AsyncMock

from openagent.core.network import check_connectivity, reset_connectivity_cache


@pytest.fixture(autouse=True)
def _fresh_connectivity_cache():
    """check_connectivity caches its result (~30s TTL); reset between tests
    so a cached result from one test can't leak into a mocked one."""
    reset_connectivity_cache()
    yield
    reset_connectivity_cache()


class TestNetworkCheck:
    @pytest.mark.asyncio
    async def test_returns_bool(self):
        """check_connectivity always returns a boolean."""
        result = await check_connectivity()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    @patch("openagent.core.network._tcp_ping", side_effect=Exception("no network"))
    async def test_offline_returns_false(self, mock_ping):
        """When TCP ping fails, we're offline."""
        result = await check_connectivity()
        assert result is False

    @pytest.mark.asyncio
    @patch("openagent.core.network._tcp_ping", return_value=None)
    async def test_online_returns_true(self, mock_ping):
        """When TCP ping succeeds, we're online."""
        result = await check_connectivity()
        assert result is True
