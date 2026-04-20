#!/usr/bin/env python3
"""
Offline indexing pipeline for HealthFirst Pharmacy RAG corpus.

Usage:
    python scripts/index_documents.py
    python scripts/index_documents.py --docs-dir ./documents --chunk-size 512 --overlap 64
    python scripts/index_documents.py --docs-dir ./documents --chroma-dir ./chroma_db
"""
import argparse
import logging
import sys
import os
import time

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.retrieval.indexer import DocumentIndexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Index pharmacy documents for RAG retrieval")
    parser.add_argument(
        "--docs-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "documents"),
        help="Directory containing .txt/.md documents (default: ./documents)",
    )
    parser.add_argument(
        "--chroma-dir",
        default=os.environ.get("CHROMA_PERSIST_DIR", os.path.join(os.path.dirname(__file__), "..", "chroma_db")),
        help="ChromaDB persistence directory (default: ./chroma_db)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Number of words per chunk (default: 512)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=64,
        help="Word overlap between consecutive chunks (default: 64)",
    )
    parser.add_argument(
        "--embedding-model",
        default="all-MiniLM-L6-v2",
        help="Sentence-transformers model for embedding (default: all-MiniLM-L6-v2)",
    )
    args = parser.parse_args()

    docs_dir = os.path.abspath(args.docs_dir)
    chroma_dir = os.path.abspath(args.chroma_dir)

    if not os.path.isdir(docs_dir):
        logger.error(f"Documents directory not found: {docs_dir}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("HealthFirst Pharmacy — RAG Document Indexer")
    logger.info("=" * 60)
    logger.info(f"  Documents dir : {docs_dir}")
    logger.info(f"  ChromaDB dir  : {chroma_dir}")
    logger.info(f"  Chunk size    : {args.chunk_size} words")
    logger.info(f"  Overlap       : {args.overlap} words")
    logger.info(f"  Embedding     : {args.embedding_model}")
    logger.info("=" * 60)

    start = time.time()
    indexer = DocumentIndexer(
        chroma_persist_dir=chroma_dir,
        embedding_model=args.embedding_model,
    )
    total_chunks = indexer.index(
        docs_dir=docs_dir,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    elapsed = time.time() - start

    logger.info("=" * 60)
    logger.info(f"Indexing complete: {total_chunks} chunks in {elapsed:.1f}s")
    logger.info(f"Vector store saved to: {chroma_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
