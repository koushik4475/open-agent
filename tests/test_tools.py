# openagent/tests/test_tools.py
"""
Tests for offline tools: sandbox command execution and routing.
"""

import pytest
import asyncio

from openagent.core.router import route, ToolName


# ─── Router Tests ─────────────────────────────────────────────

class TestRouter:
    @pytest.mark.asyncio
    async def test_routes_file_reference(self):
        tool, ctx = await route("[FILE:/tmp/test.pdf] analyze this")
        assert tool == ToolName.PARSE_FILE
        assert "filepath" in ctx

    @pytest.mark.asyncio
    async def test_routes_search_keywords(self):
        # We can't guarantee online status in tests, but we can check routing logic
        tool, ctx = await route("search for python tutorials")
        # Will be WEB_SEARCH if online, GENERAL with warning if offline
        assert tool in (ToolName.WEB_SEARCH, ToolName.GENERAL)

    @pytest.mark.asyncio
    async def test_routes_summarize(self):
        tool, ctx = await route("summarize the following text: blah blah blah")
        assert tool == ToolName.SUMMARIZE

    @pytest.mark.asyncio
    async def test_routes_command(self):
        tool, ctx = await route("run command: echo hello")
        assert tool == ToolName.RUN_COMMAND

    @pytest.mark.asyncio
    async def test_routes_url_fetch(self):
        tool, ctx = await route("fetch https://example.com and tell me what it says")
        # Will be WEB_FETCH if online, GENERAL if offline
        assert tool in (ToolName.WEB_FETCH, ToolName.GENERAL)

    @pytest.mark.asyncio
    async def test_routes_general_fallback(self):
        tool, ctx = await route("what is the meaning of life?")
        assert tool == ToolName.GENERAL

    @pytest.mark.asyncio
    async def test_routes_ocr_keywords(self):
        tool, ctx = await route("ocr this image please")
        assert tool == ToolName.OCR_IMAGE


# ─── Sandbox Validation Tests ─────────────────────────────────
# These test the command validation logic without needing Ollama

class TestSandboxValidation:
    def test_allowed_commands_from_config(self):
        from openagent.config import settings
        allowed = settings.sandbox.allowed_commands
        assert "echo" in allowed
        assert "ls" in allowed
        # Dangerous commands must NOT be in the whitelist
        assert "rm" not in allowed
        assert "sudo" not in allowed
        assert "wget" not in allowed
        assert "curl" not in allowed

    def test_sandbox_timeout_is_reasonable(self):
        from openagent.config import settings
        assert 1 <= settings.sandbox.max_execution_seconds <= 60

    def test_sandbox_is_enabled_by_default(self):
        from openagent.config import settings
        assert settings.sandbox.enabled is True
