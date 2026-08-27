from collections.abc import Sequence

import chromadb
from sentence_transformers import SentenceTransformer

from .config import CHROMA_DIR, TOP_K
from .ingest import COLLECTION_NAME, EMBEDDING_MODEL
from .lang import detect_language


class Retriever:
    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._collection = None

    def _load(self) -> None:
        if self._collection is not None:
            return
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self._collection = client.get_collection(COLLECTION_NAME)
        self._model = SentenceTransformer(EMBEDDING_MODEL)

    def search(self, question: str, limit: int = TOP_K) -> list[dict]:
        self._load()
        assert self._model is not None and self._collection is not None
        vector = self._model.encode([f"query: {question}"], normalize_embeddings=True).tolist()
        language = detect_language(question)

        # Prefer chunks matching the question's language, so an English
        # question doesn't get answered from Arabic-only context (or vice
        # versa) once both languages exist side by side in the collection.
        result = self._collection.query(
            query_embeddings=vector,
            n_results=limit,
            where={"language": language},
            include=["documents", "metadatas", "distances"],
        )
        documents: Sequence[str] = result["documents"][0]

        if not documents:
            # Fallback: no content in the detected language yet (e.g. English
            # guides are still being added) -- search without the language
            # filter so the advisor still returns something useful instead
            # of an empty result.
            result = self._collection.query(
                query_embeddings=vector,
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            documents = result["documents"][0]

        metadatas: Sequence[dict] = result["metadatas"][0]
        distances: Sequence[float] = result["distances"][0]
        return [
            {"content": content, "metadata": metadata, "distance": distance}
            for content, metadata, distance in zip(documents, metadatas, distances)
        ]


retriever = Retriever()
