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
import logging
import uuid
import time

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from openagent.config import settings

logger = logging.getLogger("openagent.memory")


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

        # Persistent client — data survives restarts
        try:
            # Explicitly specify tenant and database to avoid "default_tenant" errors in newer Chroma versions
            client = chromadb.PersistentClient(
                path=cfg.db_path,
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
            f"Memory store initialized: {cfg.db_path} "
            f"| collection={cfg.collection_name} "
            f"| items={collection.count()}"
        )
        return cls(client=client, collection=collection)

    async def store(self, user_input: str, response: str) -> None:
        """
        Embed and persist one interaction.
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

    async def retrieve(self, query: str) -> str:
        """
        Retrieve the top-N most relevant past interactions.
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
