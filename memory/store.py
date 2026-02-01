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
        client = chromadb.PersistentClient(path=cfg.db_path)

        collection = client.get_or_create_collection(
            name=cfg.collection_name,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )

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
        """
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
        )

        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""

        # Format for injection
        chunks = []
        for i, doc in enumerate(docs, 1):
            chunks.append(f"[Memory {i}]\n{doc}")

        return "\n\n".join(chunks)
