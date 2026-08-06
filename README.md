# ShopSpace AI Business Advisor

Arabic RAG service for ShopSpace tenants. Retrieves information from the ShopSpace knowledge base, then uses `Qwen/Qwen2.5-7B-Instruct` through Hugging Face to produce a grounded Arabic response with source attribution.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Frontend / Backend                                  │
│ (sends questions to /chat endpoint)                 │
└────────────────┬────────────────────────────────────┘
                 │ HTTP POST /chat
                 ▼
┌─────────────────────────────────────────────────────┐
│ FastAPI Server (app/main.py)                        │
│ ├─ CORS enabled for frontend integration            │
│ ├─ API Key validation                               │
│ └─ Request logging                                  │
└────────────────┬────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         ▼                ▼
    ┌─────────┐      ┌──────────┐
    │ Retrieve│      │LLM Engine│
    │(RAG)    │      │(Qwen)    │
    └────┬────┘      └─────┬────┘
         │                 │
         ▼                 ▼
    ┌──────────────┐  ┌─────────────┐
    │Vector Store  │  │HuggingFace  │
    │(Chroma)      │  │Inference API│
    └──────────────┘  └─────────────┘
         ▲
         │
    ┌────┴──────────────┐
    │ Knowledge Base    │
    ├─ general_guides/  │
    └─ business_guides/ │
    └────────────────── ┘
```

## Project Structure

```
ai-advisor/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI application & endpoints
│   ├── config.py            # Configuration from environment
│   ├── database.py          # SQLite session/message storage
│   ├── ingest.py            # Knowledge base ingestion into Chroma
│   ├── llm.py               # Qwen LLM integration
│   └── rag.py               # Retriever (vector search)
├── .env.example             # Environment template
├── Dockerfile               # Docker image for HF Spaces
├── requirements.txt         # Python dependencies
├── DEPLOYMENT.md            # Deployment guide
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

## Knowledge Base

- **`general_guides/`**: 7 guides about location selection, rental, licenses, contracts, checklists, FAQs, and Alexandria areas
- **`business_guides/`**: 19 business-specific setup guides

Each guide has YAML frontmatter for metadata:
```yaml
---
title: "Guide Title"
category: "location" | "legal" | "financial" | "operations"
business_type: "cafe" | "restaurant" | "retail" | "office" | "general"
language: "ar"
version: "1.0"
last_reviewed: "2024-01-15"
---
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | FastAPI | REST API with automatic documentation |
| **Server** | Uvicorn | ASGI server with WebSocket support |
| **LLM** | Qwen 2.5-7B-Instruct | Arabic language model via HuggingFace |
| **Vector Store** | Chroma | Persistent vector embeddings for retrieval |
| **Embeddings** | Sentence-Transformers | Multilingual-e5-small for semantic search |
| **Database** | SQLite | Session and message persistence |
| **Deployment** | Docker | Containerized for HuggingFace Spaces |

## Core Modules

### `main.py` - FastAPI Application
- **`POST /chat`**: Main endpoint for questions
  - Validates API key if configured
  - Manages sessions (UUID-based)
  - Stores user messages and AI responses
  - Logs all requests with unique IDs
  
- **`GET /sessions/{session_id}/messages`**: Retrieve conversation history
  
- **`GET /health`**: Health check with knowledge base status
  
- **`GET /`**: API information endpoint

### `rag.py` - Retriever (Vector Search)
```python
from app.rag import retriever

matches = retriever.search("عايز أفتح كافيه", limit=5)
# Returns: [{"content": "...", "metadata": {...}, "distance": 0.15}, ...]
```

- Lazy-loads embedding model on first use
- Caches model and collection for performance
- Returns matched chunks with similarity scores

### `ingest.py` - Knowledge Base Ingestion
```bash
python -m app.ingest  # Builds vector store from guides
```

- Parses YAML frontmatter from markdown files
- Splits documents into overlapping chunks
- Generates embeddings using multilingual-e5-small
- Stores in persistent Chroma collection
- Indexes metadata for filtering

### LLM Responses

The LLM is configured to:
- Return **concise responses** (3-5 sentences maximum)
- Avoid numbered lists and excessive formatting
- Focus on direct answers to user questions
- Maintain accuracy by using only provided context

See `app/llm.py` for prompt configuration.

### `database.py` - Session Management
- SQLite database with 3 tables:
  - `chat_sessions`: Session IDs, user IDs, creation timestamps
  - `chat_messages`: User/assistant messages with sources
  - `knowledge_documents`: Ingested document metadata
- Transaction support with context managers
- JSON serialization for sources

## API Usage

### Example: Ask a Question

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "user_id": "tenant-123",
    "session_id": null,
    "message": "عايز أفتح كافيه، أنسب منطقة فين؟"
  }'
```

### Response Structure

```json
{
  "answer": "بناءً على المعلومات المتاحة في قاعدة بيانات ShopSpace، أنسب المناطق لفتح كافيه هي سموحة وكليوباترا بسبب القرب من الجامعات والحركة المرورية العالية."
}
```

**Note:** The API returns only the `answer` field by default for simplicity. Session history and source tracking are maintained server-side for future reference.

## Configuration

Edit `.env` to customize behavior:

```env
# Required
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx

# Optional (defaults shown)
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
APP_API_KEY=                          # Leave empty for local dev
TOP_K=5                               # Chunks to retrieve
CHUNK_SIZE=900                        # Characters per chunk
CHUNK_OVERLAP=150                     # Overlap for context
```

## Local Development

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your HF_TOKEN
```

### Build Knowledge Base

```powershell
python -m app.ingest
# Outputs: {"documents": 26, "chunks": 250}
```

### Run Server

```powershell
uvicorn app.main:app --reload --port 8000
```

### Access Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI

## Deployment

See `docs/DEPLOYMENT.md` for detailed instructions on deploying to HuggingFace Spaces.

### Quick Deployment
1. Create Docker Space on HuggingFace
2. Set Dockerfile to `ai-advisor/Dockerfile`
3. Add Space secrets: `HF_TOKEN`, `APP_API_KEY`
4. Space will build and deploy automatically
5. Access at `https://<username>-<space-name>.hf.space`

## Logging

The application logs important events:

```
2024-01-15 12:34:56 - app.main - INFO - [abc-def-123] Chat request from user_id=tenant-123
2024-01-15 12:34:57 - app.rag - INFO - Found 5 matches for question
2024-01-15 12:34:58 - app.llm - INFO - Calling Qwen LLM for response generation
2024-01-15 12:35:00 - app.main - INFO - [abc-def-123] Chat completed successfully
```

Check these logs to debug issues.

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| **Startup** | 5-10s | Loads embedding model to memory |
| **Retrieval** | 100-200ms | Vector search in Chroma |
| **LLM Response** | 1-5s | Depends on HF queue and response length |
| **Total per request** | 2-6s | End-to-end time after warmup |

## Troubleshooting

### "Knowledge base is not available"
- Run `python -m app.ingest` to build vector store
- Ensure `general_guides/` and `business_guides/` exist
- Check file permissions

### "HF_TOKEN is not configured"
- Set `HF_TOKEN` in `.env` or HF Space secrets
- Ensure token has permission for Qwen model

### OOM (Out of Memory)
- Reduce `TOP_K` (fewer chunks retrieved)
- Reduce `CHUNK_SIZE` (smaller text pieces)
- Use lighter embedding model

### Slow responses
- First request warms up embedding model (normal)
- Check HF queue status if LLM is slow
- Monitor Space resources if deployed

## Integration Notes

For backend/frontend integration:

1. **Call the `/chat` endpoint** with user messages
2. **Pass session IDs** for multi-turn conversations
3. **Display the disclaimer** along with response
4. **Show source attributions** from the response
5. **Handle 503 errors** gracefully (knowledge base not ready)

Example integration:
```python
session_id = None  # First message

while True:
    message = input("Your question: ")
    
    response = requests.post(
        f"{api_url}/chat",
        json={
            "user_id": "current_user",
            "session_id": session_id,
            "message": message
        },
        headers={"X-API-Key": api_key}
    ).json()
    
    print(f"Answer: {response['answer']}")
    print(f"Sources: {response['sources']}")
    
    session_id = response['session_id']  # Reuse for follow-ups
```

## License

Part of ShopSpace AI Business Advisory System.
