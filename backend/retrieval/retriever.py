"""Query-time retrieval: embed user query → cosine search → return top-k chunks."""
import logging
from functools import lru_cache
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "pharmacy_docs"
DEFAULT_TOP_K = 3


class DocumentRetriever:
    def __init__(self, chroma_persist_dir: str, embedding_model: str = EMBEDDING_MODEL, top_k: int = DEFAULT_TOP_K):
        self.chroma_persist_dir = chroma_persist_dir
        self.embedding_model_name = embedding_model
        self.top_k = top_k
        self.model: SentenceTransformer | None = None
        self.collection = None
        self._query_cache: Dict[str, List[Dict[str, Any]]] = {}

    def load(self):
        """Load the embedding model and connect to ChromaDB. Call once at startup."""
        logger.info(f"Loading retriever with model: {self.embedding_model_name}")
        self.model = SentenceTransformer(self.embedding_model_name)
        client = chromadb.PersistentClient(
            path=self.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = client.get_collection(name=COLLECTION_NAME)
        doc_count = self.collection.count()
        logger.info(f"Retriever ready — {doc_count} chunks in vector store")

    def is_ready(self) -> bool:
        return self.model is not None and self.collection is not None

    def retrieve(self, query: str, top_k: int | None = None) -> List[Dict[str, Any]]:
        """Return top-k relevant document chunks for the given query.

        Each result dict contains: text, source, chunk_index, distance.
        Results are cached per query string (LRU-style, capped at 256 entries).
        """
        if not self.is_ready():
            logger.warning("Retriever not loaded — returning empty results")
            return []

        k = top_k or self.top_k
        cache_key = f"{query}::k{k}"

        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results and results.get("documents"):
            for text, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                chunks.append({
                    "text": text,
                    "source": meta.get("source", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": round(dist, 4),
                })

        # Simple bounded cache
        if len(self._query_cache) >= 256:
            oldest = next(iter(self._query_cache))
            del self._query_cache[oldest]
        self._query_cache[cache_key] = chunks

        return chunks

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a concise context block for the prompt."""
        if not chunks:
            return ""
        lines = ["[Relevant pharmacy information retrieved]"]
        for i, chunk in enumerate(chunks, 1):
            source = chunk["source"].replace("_", " ").replace(".txt", "").replace(".md", "")
            lines.append(f"\n--- Source: {source} ---\n{chunk['text']}")
        return "\n".join(lines)
