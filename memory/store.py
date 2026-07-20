# openagent/memory/store.py
"""
Memory Store — ChromaDB + sentence-transformers.

What it does:
  - After every interaction, embeds (user_input + response) and stores it.
  - Before every LLM call, retrieves the most semantically similar past
    interactions to inject as context (lightweight RAG).

Why ChromaDB:
  - Embedded (no server process needed).
  - Persists to disk automatically.
  - Apache 2.0. Zero cost.
  - Handles 100K+ vectors on a laptop.

Why sentence-transformers (all-MiniLM-L6-v2):
  - 22 MB model. Runs on CPU in <100 ms.
  - 384-dimensional embeddings.
  - Quality is excellent for semantic similarity.
"""

from __future__ import annotations
import asyncio
import logging
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from openagent.config import settings

logger = logging.getLogger("openagent.memory")

# Single-worker executor for background (fire-and-forget) stores.
# One worker serializes ChromaDB writes; plain threads (not asyncio
# tasks) survive per-request `asyncio.run()` loop teardown, and
# non-daemon executor threads are joined at interpreter exit so
# pending writes still flush on shutdown.
_STORE_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="openagent-memstore")


class MemoryStore:
    def __init__(self, client: chromadb.ClientAPI, collection):
        self._client = client
        self._collection = collection
        self.cfg = settings.memory

    @classmethod
    async def create(cls) -> "MemoryStore":
        """
        Factory: sets up persistent ChromaDB + embedding function.
        Called once at agent startup.
        """
        cfg = settings.memory

        # Embedding function — uses sentence-transformers locally
        embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=cfg.embedding_model
        )

        # Determine the effective DB path.
        # On ephemeral hosts (e.g. HuggingFace Spaces) the container filesystem
        # resets on rebuild/restart, so a relative cfg.db_path loses memory.
        # HF persistent storage (when enabled on the Space) is mounted at /data.
        # Priority: CHROMA_DB_PATH env → /data/chroma (if writable) → cfg.db_path.
        if os.environ.get("CHROMA_DB_PATH"):
            effective_path = os.environ["CHROMA_DB_PATH"]
        elif os.path.isdir("/data") and os.access("/data", os.W_OK):
            effective_path = "/data/chroma"
        else:
            effective_path = cfg.db_path

        # Ensure the chosen directory exists; on failure fall back to cfg.db_path
        # so a permission error can't crash startup.
        try:
            os.makedirs(effective_path, exist_ok=True)
        except OSError as e:
            logger.warning(
                f"Could not create memory dir {effective_path}: {e}. "
                f"Falling back to {cfg.db_path}"
            )
            effective_path = cfg.db_path

        # Persistent client — data survives restarts
        try:
            # Explicitly specify tenant and database to avoid "default_tenant" errors in newer Chroma versions
            client = chromadb.PersistentClient(
                path=effective_path,
                settings=chromadb.config.Settings(
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )
        except Exception as e:
            logger.error(f"Failed to create Chroma client: {e}")
            raise

        try:
            collection = client.get_or_create_collection(
                name=cfg.collection_name,
                embedding_function=embed_fn,
                metadata={"hnsw:space": "cosine"},  # cosine similarity
            )
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            # If default tenant fails, try to be even more explicit (some versions need this)
            raise

        logger.info(
            f"Memory store initialized: {effective_path} "
            f"| collection={cfg.collection_name} "
            f"| items={collection.count()}"
        )
        return cls(client=client, collection=collection)

    def store_sync(self, user_input: str, response: str) -> None:
        """
        Embed and persist one interaction (blocking).
        Document = "user: ... | agent: ..." for retrieval coherence.
        Skips trivial interactions to keep memory clean.
        """
        # Don't store trivial/short interactions — they add noise
        if len(user_input.strip()) < 10 or len(response.strip()) < 20:
            logger.debug("Skipping trivial interaction (too short to be useful)")
            return

        doc = f"user: {user_input}\nagent: {response}"
        self._collection.add(
            documents=[doc],
            ids=[str(uuid.uuid4())],
            metadatas=[{"timestamp": time.time()}],
        )
        logger.debug(f"Stored memory item (total: {self._collection.count()})")

    def _store_safe(self, user_input: str, response: str) -> None:
        """store_sync wrapper that logs instead of raising (background use)."""
        try:
            self.store_sync(user_input, response)
        except Exception as e:
            logger.warning(f"Background memory store failed: {e}")

    def store_background(self, user_input: str, response: str) -> None:
        """
        Fire-and-forget store: submits the embedding + write to a
        background thread so the caller can return the response to the
        user without paying the embedding latency. Safe to call from
        any thread/event loop; failures are logged, never raised.
        """
        _STORE_EXECUTOR.submit(self._store_safe, user_input, response)

    async def store(self, user_input: str, response: str) -> None:
        """
        Awaitable store — runs the blocking embed/write in a thread so
        the event loop isn't stalled. Completes before returning (use
        store_background() when the caller shouldn't wait at all).
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.store_sync, user_input, response)

    def retrieve_sync(self, query: str) -> str:
        """
        Retrieve the top-N most relevant past interactions (blocking).
        Returns a formatted string ready to inject into the prompt.
        """
        n = settings.memory.max_context_chunks
        count = self._collection.count()

        if count == 0:
            return ""

        # Can't request more results than exist
        n = min(n, count)

        results = self._collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        if not docs:
            return ""

        # Filter by similarity — only include relevant memories
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Threshold 0.8 = only reasonably similar memories
        RELEVANCE_THRESHOLD = 0.8
        chunks = []
        for i, (doc, dist) in enumerate(zip(docs, distances), 1):
            if dist < RELEVANCE_THRESHOLD:
                chunks.append(f"[Memory {i}]\n{doc}")
            else:
                logger.debug(f"Skipping memory {i} (distance={dist:.2f}, too far)")

        return "\n\n".join(chunks)

    async def retrieve(self, query: str) -> str:
        """
        Awaitable retrieve — runs the blocking embed + vector query in a
        thread so a shared event loop isn't stalled during embedding.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.retrieve_sync, query)
