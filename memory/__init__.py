# openagent/memory/__init__.py
"""
Memory package — public surface.

The live implementation lives in openagent.memory.store.MemoryStore.
This file used to hold a stale full duplicate of an older store.py;
it is now a thin re-export so there is exactly one implementation.
"""

from __future__ import annotations

from openagent.memory.store import MemoryStore

__all__ = ["MemoryStore"]
