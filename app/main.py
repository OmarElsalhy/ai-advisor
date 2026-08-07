from contextlib import asynccontextmanager
from pathlib import Path
import logging
import secrets
import uuid

import chromadb
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import APP_API_KEY, CHROMA_DIR
from .database import add_message, ensure_session, get_messages, initialize
from .ingest import COLLECTION_NAME, ingest
from .llm import answer
from .rag import retriever

logger = logging.getLogger(__name__)

# Logging configuration
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

DISCLAIMER = "المعلومات إرشادية عامة وليست استشارة قانونية أو مهنية. تحقّق من الجهات المختصة قبل اتخاذ قرارات تتعلق بالتراخيص أو العقود."


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        client.get_collection(COLLECTION_NAME)
    except Exception:
        ingest(reset=False)
    yield


app = FastAPI(
    title="ShopSpace AI Business Advisor",
    version="1.0.0",
    description="Arabic RAG API powered by Qwen and the ShopSpace knowledge base.",
    lifespan=lifespan,
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    session_id: str | None = None
    user_id: str | None = Field(default=None, max_length=128)


class Source(BaseModel):
    document_id: str
    title: str
    category: str
    business_type: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[Source]
    disclaimer: str


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """API key check.

    - If APP_API_KEY is empty: allow all requests (local dev only).
    - If APP_API_KEY is set: require a valid X-API-Key header, otherwise reject
      with 401. No silent bypass — an invalid/missing key must never be allowed
      through once a key is configured.
    """
    if not APP_API_KEY:
        # No API key configured — allow all requests (local dev)
        return

    if x_api_key and secrets.compare_digest(x_api_key, APP_API_KEY):
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


@app.get("/health", tags=["system"])
def health() -> dict:
    """Health check endpoint with knowledge base status."""
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        logger.info(f"Health check: OK - {count} chunks in knowledge base")
        return {
            "status": "ok",
            "knowledge_base": "ready",
            "chunks_indexed": count
        }
    except Exception as e:
        logger.warning(f"Health check: Knowledge base not ready - {str(e)}")
        return {
            "status": "degraded",
            "knowledge_base": "not_ready",
            "error": str(e)
        }


@app.post("/chat", response_model=ChatResponse, tags=["advisor"], dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest, http_request: Request):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request from user_id={request.user_id}, session_id={request.session_id}")

    try:
        session_id = ensure_session(request.session_id, request.user_id)
        add_message(session_id, "user", request.message)
        logger.debug(f"[{request_id}] Message saved to session {session_id}")

        matches = retriever.search(request.message)
        if not matches:
            logger.warning(f"[{request_id}] No matches found in knowledge base")
            raise HTTPException(status_code=503, detail="Knowledge base is not available")

        context = "\n\n".join(
            f"[المصدر: {item['metadata']['title']}]\n{item['content']}" for item in matches
        )
        logger.debug(f"[{request_id}] Retrieved {len(matches)} matches from knowledge base")

        try:
            response_text = answer(request.message, context)
            logger.debug(f"[{request_id}] Generated response from LLM")
        except RuntimeError as error:
            logger.error(f"[{request_id}] LLM error: {str(error)}")
            raise HTTPException(status_code=503, detail=str(error)) from error

        sources: list[dict] = []
        seen: set[str] = set()
        for item in matches:
            metadata = item["metadata"]
            document_id = metadata["document_id"]
            if document_id in seen:
                continue
            seen.add(document_id)
            sources.append(
                {
                    "document_id": document_id,
                    "title": metadata["title"],
                    "category": metadata["category"],
                    "business_type": metadata["business_type"],
                }
            )

        add_message(session_id, "assistant", response_text, sources)
        logger.info(f"[{request_id}] Chat completed successfully for session {session_id}")

        return {
            "session_id": session_id,
            "answer": response_text,
            "sources": sources,
            "disclaimer": DISCLAIMER,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@app.get("/sessions/{session_id}/messages", tags=["advisor"], dependencies=[Depends(verify_api_key)])
def session_messages(session_id: str) -> dict:
    logger.info(f"Fetching messages for session {session_id}")
    messages = get_messages(session_id)
    logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
    return {"session_id": session_id, "messages": messages}


@app.get("/", tags=["system"])
def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "ShopSpace AI Business Advisor",
        "version": "1.0.0",
        "description": "Arabic RAG API powered by Qwen and the ShopSpace knowledge base",
        "endpoints": {
            "chat": "POST /chat - Ask a question to the AI advisor",
            "messages": "GET /sessions/{session_id}/messages - Get conversation history",
            "health": "GET /health - Health check",
            "docs": "GET /docs - Swagger UI documentation",
        }
    }
