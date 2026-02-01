# openagent/tests/test_memory.py
"""
Tests for the ChromaDB memory store.
Uses a temporary directory so tests don't pollute the real DB.
"""

import pytest
import tempfile
import os

# Patch settings to use a temp directory before importing MemoryStore
import openagent.config as cfg_module


@pytest.fixture
def temp_memory_path(tmp_path, monkeypatch):
    """Override memory db_path to a temp directory for testing."""
    monkeypatch.setattr(
        cfg_module.settings.memory,
        "db_path",
        str(tmp_path / "test_chroma"),
    )
    return tmp_path / "test_chroma"


class TestMemoryStore:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, temp_memory_path):
        from openagent.memory.store import MemoryStore

        store = await MemoryStore.create()

        # Store an interaction
        await store.store(
            "What is Python?",
            "Python is a high-level programming language."
        )

        # Retrieve with a semantically similar query
        result = await store.retrieve("Tell me about Python programming")

        assert result != ""
        assert "Python" in result

    @pytest.mark.asyncio
    async def test_retrieve_empty_store(self, temp_memory_path):
        from openagent.memory.store import MemoryStore

        store = await MemoryStore.create()
        result = await store.retrieve("anything")
        assert result == ""

    @pytest.mark.asyncio
    async def test_multiple_items_retrieval(self, temp_memory_path):
        from openagent.memory.store import MemoryStore

        store = await MemoryStore.create()

        # Store multiple interactions
        await store.store("What is JavaScript?", "JS is a web scripting language.")
        await store.store("What is Python?", "Python is great for data science.")
        await store.store("What is Rust?", "Rust is a systems programming language.")

        # Query should return relevant results
        result = await store.retrieve("Tell me about programming languages")
        assert result != ""
        # Should have multiple memory chunks
        assert "[Memory" in result
