# Naive RAG — IPHAN Technical Challenge

A REST API that implements **Naive RAG** (Retrieval-Augmented Generation) over Markdown documents, using FastAPI, LangChain, Ollama and ChromaDB.

---

## Architecture

```
INGESTION FLOW
──────────────
Markdown file
    │
    ▼
TextLoader  (LangChain)
    │  reads raw text, preserves structure
    ▼
RecursiveCharacterTextSplitter  (LangChain)
    │  splits on headings → paragraphs → sentences
    ▼
OllamaEmbeddings  (nomic-embed-text)
    │  converts each chunk to a dense vector
    ▼
ChromaDB  (persisted locally)
    │  stores vectors + raw text + metadata


QUERY FLOW
──────────
User question
    │
    ▼
OllamaEmbeddings  (same model)
    │  encodes question into vector
    ▼
ChromaDB similarity_search
    │  returns top-13 most similar chunks (k_fetch=13)
    ▼
FlashrankRerank  (cross-encoder)
    │  re-scores and reorders candidates, keeps top-8
    ▼
PromptTemplate
    │  wraps retrieved chunks as numbered context around the question
    ▼
OllamaLLM  (llama3:latest)
    │  generates grounded answer
    ▼
JSON response  { answer, sources: [{ chunk, score, source }] }
```

---

## Chunking Strategy

**Method:** `RecursiveCharacterTextSplitter` with Markdown-aware separators.

The splitter attempts to break text at the following boundaries, in priority order:

| Priority | Separator | Rationale |
|----------|-----------|-----------|
| 1 | `\n## ` | H2 heading — topic boundary |
| 2 | `\n### ` | H3 heading — sub-topic boundary |
| 3 | `\n#### ` | H4 heading |
| 4 | `\n\n` | Paragraph break |
| 5 | `\n` | Line break |
| 6 | ` ` | Word boundary |
| 7 | `""` | Character (last resort) |

**Parameters (configurable via `.env`):**

| Parameter | Default | Reason |
|-----------|---------|--------|
| `CHUNK_SIZE` | 500 | Fits within the context window of small embedding models; large enough to carry a coherent idea |
| `CHUNK_OVERLAP` | 50 | Prevents cutting off context at boundaries without significantly inflating storage |

Prioritizing heading separators ensures semantically coherent chunks that stay within the same section, which improves retrieval precision for structured documents like specifications and reports.

---

## Models

| Role | Model | Notes |
|------|-------|-------|
| Embeddings | `nomic-embed-text` | Fast, high quality, runs locally via Ollama |
| Chat / Generation | `llama3:latest` | 8B parameter model; configurable via `.env` |

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running

1. Pull the required models:

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

2. Ensure Ollama is running:

```bash
ollama serve
```

---

## Setup & Run

```bash
# Clone / enter the project
cd iphan-project

# Create virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) adjust models or chunk size
# edit .env

# Start the API
uvicorn app.main:app --reload
```

> **Note:** On the first request that triggers re-ranking, Flashrank will automatically download a small cross-encoder model (~80 MB). Ensure internet access is available on first run.

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`  
Web interface: `http://localhost:8000`

---

## Endpoints

### `POST /ingest`

Upload a Markdown file to index it.

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@my_document.md"
```

Response:
```json
{ "chunks_stored": 12, "filename": "my_document.md" }
```

Only `.md` files are accepted. Uploading other formats returns HTTP 400.

---

### `POST /chat`

Ask a question over the indexed documents.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the main objective of the document?"}'
```

Response:
```json
{
  "answer": "The main objective is ...",
  "sources": [
    {
      "chunk": "...",
      "score": 0.9241,
      "source": "my_document.md"
    }
  ]
}
```

> **Score note:** After re-ranking, the score is a **relevance score** (higher = more relevant). A score near `1.0` indicates a very strong match between the chunk and the question.

---

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## Bonus Features

### RF-B01 — Re-ranking

After the initial similarity search, a **FlashrankRerank** cross-encoder re-scores each candidate chunk against the question. This two-stage approach compensates for the semantic gap between embedding similarity and actual relevance:

- Stage 1 (recall): ChromaDB fetches the top 13 candidates by vector similarity
- Stage 2 (precision): Flashrank re-scores and reorders them, keeping the top 8

Flashrank uses a lightweight cross-encoder model that runs locally with no GPU or PyTorch dependency.

### RF-B02 — Web Interface

A single-page interface is served at `http://localhost:8000` with:

- Drag-and-drop file upload
- Chat interface with typing animation
- Collapsible source panels with color-coded relevance scores
- List of indexed files in the sidebar

---

## Limitations

- **Only Markdown (`.md`) files** are supported by design.
- The vector store is **not scoped per session** — all ingested documents share the same Chroma collection. Querying always searches across all indexed content.
- Small local models may produce incomplete answers for broad questions that require synthesizing multiple document sections. More specific questions yield more accurate results.
- No authentication or rate limiting is implemented — this is a local development setup.
- ChromaDB stores vectors on disk in `./vector_store`. Deleting this folder clears all indexed documents.

---

## Project Structure

```
iphan-project/
├── app/
│   ├── main.py              # FastAPI app + router registration + web interface
│   ├── core/
│   │   └── config.py        # Settings from .env
│   ├── routes/
│   │   ├── ingest.py        # POST /ingest
│   │   └── chat.py          # POST /chat
│   ├── services/
│   │   ├── ingestion.py     # Load → chunk → embed → store
│   │   └── retrieval.py     # Retrieve → re-rank → prompt → generate
│   └── static/
│       └── index.html       # Single-page web interface
├── .env                     # Default configuration
├── requirements.txt
└── README.md
```
