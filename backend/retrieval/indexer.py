"""Offline document indexing pipeline: load → chunk → embed → store in ChromaDB."""
import os
import re
import logging
from pathlib import Path
from typing import List, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 64
COLLECTION_NAME = "pharmacy_docs"


class DocumentIndexer:
    def __init__(self, chroma_persist_dir: str, embedding_model: str = EMBEDDING_MODEL):
        self.chroma_persist_dir = chroma_persist_dir
        self.embedding_model_name = embedding_model
        self.model: SentenceTransformer | None = None
        self.client: chromadb.PersistentClient | None = None
        self.collection = None

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name)

    def _init_chroma(self):
        if self.client is None:
            os.makedirs(self.chroma_persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.chroma_persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

    def _load_documents(self, docs_dir: str) -> List[Tuple[str, str]]:
        """Return list of (filename, text) from all .txt and .md files in docs_dir."""
        docs = []
        for path in sorted(Path(docs_dir).glob("*")):
            if path.suffix in {".txt", ".md"}:
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    docs.append((path.name, text))
        logger.info(f"Loaded {len(docs)} documents from {docs_dir}")
        return docs

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into word-count-based chunks with overlap."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            start += chunk_size - overlap
        return chunks

    def index(self, docs_dir: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
        """Full pipeline: load docs → chunk → embed → upsert into ChromaDB."""
        self._load_model()
        self._init_chroma()

        # Clear existing entries so re-runs are idempotent
        existing = self.collection.count()
        if existing > 0:
            logger.info(f"Clearing {existing} existing entries before re-indexing")
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)

        documents = self._load_documents(docs_dir)
        if not documents:
            logger.warning(f"No documents found in {docs_dir}")
            return

        chunk_ids, chunk_texts, chunk_metas = [], [], []
        for doc_name, doc_text in documents:
            chunks = self._chunk_text(doc_text, chunk_size, overlap)
            for i, chunk in enumerate(chunks):
                cid = f"{doc_name}::chunk{i}"
                chunk_ids.append(cid)
                chunk_texts.append(chunk)
                chunk_metas.append({"source": doc_name, "chunk_index": i})

        logger.info(f"Embedding {len(chunk_texts)} chunks from {len(documents)} documents…")
        embeddings = self.model.encode(chunk_texts, batch_size=64, show_progress_bar=False).tolist()

        # Upsert in batches of 500
        batch_size = 500
        for i in range(0, len(chunk_ids), batch_size):
            self.collection.upsert(
                ids=chunk_ids[i : i + batch_size],
                documents=chunk_texts[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                metadatas=chunk_metas[i : i + batch_size],
            )

        logger.info(f"Indexed {len(chunk_ids)} chunks into ChromaDB at {self.chroma_persist_dir}")
        return len(chunk_ids)
