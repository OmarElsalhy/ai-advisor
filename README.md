# ShopSpace AI Business Advisor

AI-powered RAG service for ShopSpace tenants in Alexandria. Retrieves relevant information from the ShopSpace knowledge base, then uses `Qwen/Qwen2.5-7B-Instruct` through Hugging Face to produce grounded responses with source attribution.

The system supports **both Arabic and English**, automatically detects the user's language, retrieves matching knowledge-base content, and responds in the same language.

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│ Frontend / Backend                                  │
│ (sends questions to /chat endpoint)                 │
└────────────────┬────────────────────────────────────┘
                 │ HTTP POST /chat
                 ▼
┌─────────────────────────────────────────────────────┐
│ FastAPI Server (app/main.py)                        │
│ ├─ Language Detection                               │
│ ├─ Greeting Handling                                │
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
    └──────┬───────┘  └─────────────┘
           │
     ┌─────┴──────────────┐
     │ Knowledge Base     │
     ├─ Arabic guides     │
     └─ English guides    │
     └────────────────────┘
```

## Project Structure

```text
ai-advisor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & endpoints
│   ├── config.py            # Configuration from environment
│   ├── database.py          # SQLite session/message storage
│   ├── ingest.py            # Knowledge base ingestion into Chroma
│   ├── llm.py               # Qwen LLM integration
│   ├── rag.py               # Language-aware vector retrieval
│   └── lang.py              # Arabic/English detection
├── general_guides/
│   ├── *_ar.md              # Arabic general guides
│   └── *_en.md              # English general guides
├── business_guides/
│   ├── *_ar.md              # Arabic business guides
│   └── *_en.md              # English business guides
├── .env.example
├── Dockerfile
├── requirements.txt
├── DEPLOYMENT.md
├── README.md
└── .gitignore
```

## Knowledge Base

* **`general_guides/`**: General guides covering location selection, rental, licenses, contracts, checklists, FAQs, and Alexandria areas.
* **`business_guides/`**: Business-specific setup guides for different business types.

Each guide is available in **Arabic and English** and uses YAML frontmatter for metadata:

```yaml
---
title: "Guide Title"
category: "location"
business_type: "cafe"
language: "en"
version: "1.0"
last_reviewed: "2024-01-15"
---
```

The `language` field is used to match retrieved content with the user's language.

## Technology Stack

| Component         | Technology            | Purpose                               |
| ----------------- | --------------------- | ------------------------------------- |
| **Web Framework** | FastAPI               | REST API with automatic documentation |
| **Server**        | Uvicorn               | ASGI server                           |
| **LLM**           | Qwen 2.5-7B-Instruct  | Response generation                   |
| **Vector Store**  | Chroma                | Persistent vector embeddings          |
| **Embeddings**    | Sentence-Transformers | Multilingual semantic search          |
| **Database**      | SQLite                | Session and message persistence       |
| **Deployment**    | Docker                | Containerized deployment              |

## Core Modules

### `main.py` - FastAPI Application

* **`POST /chat`**: Main endpoint for questions

  * Detects Arabic or English
  * Handles simple greetings directly
  * Retrieves relevant knowledge
  * Generates the response
  * Returns source attribution

* **`GET /sessions/{session_id}/messages`**: Retrieve conversation history

* **`GET /health`**: Health check with knowledge base status

* **`GET /`**: API information endpoint

### `lang.py` - Language Detection

Provides lightweight Arabic/English detection and greeting handling.

```python
language = detect_language(question)
```

Returns:

```text
ar
```

or:

```text
en
```

### `rag.py` - Retriever

Retrieves semantically relevant chunks while preferring content in the same language as the user's question.

```python
matches = retriever.search(
    "What are the best areas in Alexandria for a café?",
    limit=5
)
```

### `ingest.py` - Knowledge Base Ingestion

```bash
python -m app.ingest
```

* Parses YAML frontmatter
* Splits Markdown documents into chunks
* Generates multilingual embeddings
* Stores vectors and metadata in Chroma
* Stores document metadata in SQLite

### `llm.py` - LLM Integration

The LLM uses separate Arabic and English prompts and templates to ensure responses match the user's language and remain grounded in the retrieved context.

## API Usage

### Example

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "user_id": "tenant-123",
    "session_id": null,
    "message": "What are the best areas in Alexandria for a café?"
  }'
```

### Response

```json
{
  "session_id": "example-session-id",
  "answer": "When choosing a location for your café in Alexandria, consider your target customers, foot traffic, competition, and rental budget.",
  "sources": [
    {
      "document_id": "example-document-id",
      "title": "Alexandria Areas Guide",
      "category": "location",
      "business_type": "cafe"
    }
  ],
  "disclaimer": "The information provided is general guidance and is not professional legal or financial advice."
}
```

## Configuration

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx

HF_MODEL=Qwen/Qwen2.5-7B-Instruct
APP_API_KEY=
TOP_K=5
CHUNK_SIZE=900
CHUNK_OVERLAP=150
```

## Local Development

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your `HF_TOKEN` to `.env`.

### Build Knowledge Base

Run this after adding or modifying knowledge-base documents:

```powershell
python -m app.ingest
```

### Run Server

```powershell
uvicorn app.main:app --reload --port 8000
```

### Access Documentation

Visit:

```text
http://localhost:8000/docs
```

for the interactive Swagger UI.

## Deployment

See `DEPLOYMENT.md` for deployment instructions.

Required secrets:

```text
HF_TOKEN
APP_API_KEY
```

## Troubleshooting

### "Knowledge base is not available"

Run:

```powershell
python -m app.ingest
```

Then check:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

Make sure `general_guides/` and `business_guides/` contain the Markdown knowledge-base files.

### "HF_TOKEN is not configured"

Set `HF_TOKEN` in `.env` or your deployment secrets.

### Slow responses

The first request may take longer while the embedding model is loaded. Subsequent requests should be faster.

## License

Part of the ShopSpace AI Business Advisory System.
