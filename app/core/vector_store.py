from __future__ import annotations

import chromadb
from typing import Protocol, List, Dict, Any

from app.config import COLLECTION_NAME, VECTOR_STORE_DIR
from app.core.state import SearchResult


class VectorStore(Protocol):
    def query_embeddings(self, query_embeddings: List[List[float]], k: int = 5) -> List[SearchResult]:
        ...


class ChromaVectorStore:
    def __init__(self, collection):
        self._collection = collection

    def query_embeddings(self, query_embeddings: List[List[float]], k: int = 5) -> List[SearchResult]:
        results = self._collection.query(
            query_embeddings=query_embeddings,
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        # For now a single query per call
        sr = SearchResult(query="", documents=docs, metadatas=metas, distances=dists)
        return [sr]


def get_vector_store() -> ChromaVectorStore:
    """Get a standardized ChromaVectorStore instance."""
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, 
        metadata={"hnsw:space": "cosine"}
    )
    return ChromaVectorStore(collection)


