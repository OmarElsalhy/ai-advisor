from collections.abc import Sequence
import logging

import chromadb
from sentence_transformers import SentenceTransformer

from .config import CHROMA_DIR, TOP_K
from .ingest import COLLECTION_NAME, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._collection = None

    def _load(self) -> None:
        if self._collection is not None:
            return
        logger.info("Loading embedding model and Chroma collection")
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self._collection = client.get_collection(COLLECTION_NAME)
        self._model = SentenceTransformer(EMBEDDING_MODEL)
        logger.debug("Embedding model and collection loaded successfully")

    def search(self, question: str, limit: int = TOP_K) -> list[dict]:
        self._load()
        assert self._model is not None and self._collection is not None
        logger.debug(f"Searching for matches: '{question}' (limit={limit})")
        vector = self._model.encode([f"query: {question}"], normalize_embeddings=True).tolist()
        result = self._collection.query(query_embeddings=vector, n_results=limit, include=["documents", "metadatas", "distances"])
        documents: Sequence[str] = result["documents"][0]
        metadatas: Sequence[dict] = result["metadatas"][0]
        distances: Sequence[float] = result["distances"][0]
        matches = [
            {"content": content, "metadata": metadata, "distance": distance}
            for content, metadata, distance in zip(documents, metadatas, distances)
        ]
        logger.info(f"Found {len(matches)} matches for question")
        return matches


retriever = Retriever()
