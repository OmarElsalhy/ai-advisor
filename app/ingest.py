"""Ingest the Arabic knowledge base into a local Chroma vector store."""

import hashlib
import logging
import re
import shutil
from pathlib import Path

import chromadb
import yaml
from sentence_transformers import SentenceTransformer

from .config import (
    BUSINESS_GUIDES_DIR,
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    GENERAL_GUIDES_DIR,
)
from .database import connection, initialize

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
COLLECTION_NAME = "shopspace_knowledge"


def _split_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, flags=re.DOTALL)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, match.group(2).strip()


def _chunks(text: str) -> list[str]:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue
        if current:
            chunks.append(current)
        overlap = current[-CHUNK_OVERLAP:] if current else ""
        current = f"{overlap}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def _documents() -> list[Path]:
    return sorted(GENERAL_GUIDES_DIR.glob("*.md")) + sorted(BUSINESS_GUIDES_DIR.glob("*.md"))


def ingest(reset: bool = True) -> dict[str, int]:
    logger.info("Starting knowledge base ingestion...")
    initialize()
    if reset and CHROMA_DIR.exists():
        logger.info(f"Resetting Chroma directory at {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        # ignore if collection does not exist
        pass
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    document_count = 0
    chunk_count = 0
    with connection() as conn:
        conn.execute("DELETE FROM knowledge_documents")
        documents = _documents()
        logger.info(f"Found {len(documents)} documents to ingest")
        for path in documents:
            logger.debug(f"Ingesting document: {path.name}")
            metadata, body = _split_frontmatter(path.read_text(encoding="utf-8"))
            doc_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
            title = str(metadata.get("title", path.stem))
            category = str(metadata.get("category", "general"))
            business_type = str(metadata.get("business_type", "general"))
            language = str(metadata.get("language", "ar"))
            conn.execute(
                """INSERT INTO knowledge_documents
                (id, path, title, category, business_type, language, version, last_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_id, str(path), title, category, business_type, language, metadata.get("version"), metadata.get("last_reviewed")),
            )
            pieces = _chunks(body)
            if not pieces:
                logger.warning(f"No chunks generated for {path.name}")
                continue
            ids = [f"{doc_id}-{index}" for index in range(len(pieces))]
            vectors = model.encode([f"passage: {piece}" for piece in pieces], normalize_embeddings=True).tolist()
            metadatas = [
                {
                    "document_id": doc_id,
                    "title": title,
                    "category": category,
                    "business_type": business_type,
                    "language": language,
                    "source_path": path.name,
                }
                for _ in pieces
            ]
            collection.add(ids=ids, documents=pieces, embeddings=vectors, metadatas=metadatas)
            document_count += 1
            chunk_count += len(pieces)
            logger.debug(f"Ingested {path.name}: {len(pieces)} chunks")
    logger.info(f"Knowledge base ingestion complete: {document_count} documents, {chunk_count} chunks")
    return {"documents": document_count, "chunks": chunk_count}


if __name__ == "__main__":
    print(ingest())
