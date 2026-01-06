# RAG System

The Retrieval-Augmented Generation (RAG) system enables semantic search across the knowledge base using vector embeddings. The core implementation resides in the `agent_core` library, with the backend API providing HTTP endpoints.

## Architecture

Classical RAG architecture supported by the Code.

![](./images/docu_mgt.drawio.png)

## Module Structure

The RAG service is implemented in `agent_core/services/rag/`:

```
agent_core/
└── services/
    └── rag/
        ├── __init__.py           # Public exports
        ├── service.py            # RAGService, SearchResult, IndexingResult
        ├── document_loader.py    # DocumentLoader, LoadedDocument
        └── text_splitter.py      # RecursiveTextSplitter, TextChunk
```

## Components

### Document Loader

Loads document content from various sources (`agent_core/services/rag/document_loader.py`):

```python
from agent_core.services.rag.document_loader import DocumentLoader, LoadedDocument

loader = DocumentLoader(timeout=30.0)
documents = await loader.load(uri, document_type)
```

Supported sources:

| Type | Description | Example URI |
| ---- | ----------- | ----------- |
| markdown | Local or remote markdown files | `file:///path/to/doc.md` or `https://...` |
| website | Web page content (HTML parsed to markdown) | `https://example.com/page` |
| folder | Directory of markdown files | `/path/to/docs/` |

The loader returns a list of `LoadedDocument` objects containing:

```python
class LoadedDocument(BaseModel):
    content: str           # Extracted text content
    document_id: str       # Unique document identifier
    content_hash: str      # SHA256 hash for change detection
    source_uri: str        # Original source URI
    title: Optional[str]   # Extracted title
```

#### Frontmatter Support

Markdown files can include YAML frontmatter for metadata:

```markdown
---
title: Configuration Guide
document_id: config-guide-v1
source_url: https://docs.example.com/config
---

# Configuration Guide

Content here...
```

### Text Splitter

Splits documents into chunks for embedding (`agent_core/services/rag/text_splitter.py`):

```python
from agent_core.services.rag.text_splitter import RecursiveTextSplitter, TextChunk

splitter = RecursiveTextSplitter(
    chunk_size=1000,       # Target chunk size in characters
    chunk_overlap=200      # Overlap between chunks
)

chunks: list[TextChunk] = splitter.split_text(content, metadata)
```

The recursive splitter attempts to split on natural boundaries:

1. Paragraphs (`\n\n`)
2. Lines (`\n`)
3. Sentences (`. `)
4. Words (` `)
5. Characters (fallback)

Each chunk is a `TextChunk` object:

```python
class TextChunk(BaseModel):
    content: str        # Chunk text
    start_index: int    # Character offset in original content
    chunk_index: int    # Position in the document
    metadata: dict      # Inherited metadata
```

### Embedding Model

Uses sentence-transformers for local embedding generation:

- Model: `all-MiniLM-L6-v2`
- Runs entirely locally (no external API calls)
- Produces 384-dimensional vectors
- Optimized for semantic similarity

### Vector Store

ChromaDB provides persistent vector storage.

Configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma` | ChromaDB storage path |
| `CHROMA_COLLECTION_NAME` | `knowledge_base` | Vector collection name |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `OVERLAP` | `200` | Chunk overlap |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |

Features:

- Cosine similarity for search (configured via `hnsw:space`)
- Metadata filtering by category, tags, knowledge_id
- Persistent storage across restarts
- Automatic collection management

## Code Integration

### Using RAGService Directly

```python
from agent_core.services.rag.service import RAGService, get_rag_service

# Singleton access (recommended for applications)
rag = get_rag_service()

# Or manual initialization with custom settings
rag = RAGService(
    persist_directory="./data/chroma",
    collection_name="knowledge_base",
    chunk_size=1000,
    chunk_overlap=200,
    embedding_model="all-MiniLM-L6-v2"
)
```

### Indexing Documents

```python
from agent_core.services.rag.service import get_rag_service, IndexingResult

rag = get_rag_service()

# Index a single document
result: IndexingResult = await rag.index_knowledge(
    knowledge_id=123,
    title="OAuth Guide",
    uri="/path/to/document.md",
    document_type="markdown",  # or "website" or "folder"
    category="security",
    tags="auth,oauth,security"
)

print(f"Success: {result.success}")
print(f"Chunks indexed: {result.chunks_indexed}")
print(f"Content hash: {result.content_hash}")
if result.error:
    print(f"Error: {result.error}")
```

#### IndexingResult Model

```python
class IndexingResult(BaseModel):
    success: bool
    chunks_indexed: int
    content_hash: str
    error: Optional[str] = None
```

### Searching

```python
from agent_core.services.rag.service import get_rag_service, SearchResult

rag = get_rag_service()

results: list[SearchResult] = await rag.search(
    query="How to implement OAuth?",
    n_results=5,
    category="security",           # Optional filter
    knowledge_ids=[1, 3, 7]        # Optional: search within specific documents
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Title: {result.title}")
    print(f"Content: {result.content[:200]}...")
```

#### SearchResult Model

```python
class SearchResult(BaseModel):
    content: str
    knowledge_id: int
    title: str
    uri: str
    score: float
    chunk_index: int
```

### Removing from Index

```python
rag = get_rag_service()

success = await rag.remove_knowledge(knowledge_id=123)
```

### Getting Collection Statistics

```python
rag = get_rag_service()

stats = rag.get_collection_stats()
# Returns: {
#   "total_chunks": 150,
#   "unique_knowledge_items": 12,
#   "collection_name": "knowledge_base",
#   "embedding_model": "all-MiniLM-L6-v2"
# }
```

## Using RAGAgent for AI Responses

The `RAGAgent` combines RAG search with LLM generation:

```python
from agent_core.agents.rag_agent import RAGAgent
from agent_core import LLMConfig

# Configure LLM
config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-api-key"
)

# Create RAG agent
agent = RAGAgent(
    llm_config=config,
    n_results=5  # Number of context chunks to retrieve
)

# Execute query with RAG
response = await agent.execute(
    query="How do I configure database connections?",
    conversation_history=[
        {"role": "user", "content": "previous message"},
        {"role": "assistant", "content": "previous response"}
    ],
    context={"entities": {"topic": "database", "keywords": ["config", "connection"]}}
)

print(response.message)           # LLM-generated response
print(response.context_used)      # Retrieved documents with scores
print(response.agent_type)        # "rag"
```

### AgentResponse Structure

```python
@dataclass
class AgentResponse:
    message: str                      # LLM response text
    context_used: list[dict] = []     # RAG context with title, uri, score, snippet
    model: str = ""                   # Model used
    provider: str = ""                # Provider used
    agent_type: str = ""              # "rag"
    metadata: dict = {}               # search_query, results_count
```

## FastAPI Integration

The backend exposes RAG functionality via dependency injection:

```python
from fastapi import APIRouter, Depends
from agent_core.services.rag.service import get_rag_service, RAGService

router = APIRouter()

def get_rag() -> RAGService:
    """Dependency to get the RAG service."""
    return get_rag_service()

@router.post("/search")
async def search(
    query: str,
    rag: RAGService = Depends(get_rag)
):
    results = await rag.search(query)
    return {"results": results}
```

## API Endpoints

### Index Knowledge Item

```bash
POST /api/v1/rag/index/{knowledge_id}
```

Response:

```json
{
  "success": true,
  "knowledge_id": 1,
  "chunks_indexed": 15,
  "content_hash": "abc123..."
}
```

### Index All Items

```bash
POST /api/v1/rag/index-all?status=active
```

Indexes all knowledge items matching the filter. Returns summary with per-item results.

### Remove from Index

```bash
DELETE /api/v1/rag/index/{knowledge_id}
```

Removes all chunks for a knowledge item from the vector store.

### Semantic Search (POST)

```bash
POST /api/v1/rag/search
Content-Type: application/json

{
  "query": "How to configure the database connection?",
  "n_results": 5,
  "category": "Engineering"
}
```

Response:

```json
{
  "query": "How to configure the database connection?",
  "results": [
    {
      "content": "Database configuration is managed via environment...",
      "knowledge_id": 3,
      "title": "Configuration Guide",
      "uri": "/docs/config.md",
      "score": 0.87,
      "chunk_index": 2
    }
  ],
  "total_results": 5
}
```

### Semantic Search (GET)

Convenience endpoint for simple searches:

```bash
GET /api/v1/rag/search?q=database+configuration&n=5&category=Engineering
```

### Collection Statistics

```bash
GET /api/v1/rag/stats
```

Response:

```json
{
  "total_chunks": 150,
  "unique_knowledge_items": 12,
  "collection_name": "knowledge_base",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

## Search Filtering

### By Category

```json
{
  "query": "authentication",
  "category": "Engineering/Security"
}
```

### By Tags

```json
{
  "query": "deployment steps",
  "tags": ["docker", "production"]
}
```

### By Knowledge IDs

Search within specific documents:

```json
{
  "query": "error handling",
  "knowledge_ids": [1, 3, 7]
}
```

## Chunk Metadata

Each stored chunk includes metadata:

| Field | Description |
| ----- | ----------- |
| knowledge_id | Source knowledge item ID |
| title | Document title |
| uri | Source URI |
| document_type | markdown, folder, or website |
| category | Document category |
| tags | Associated tags |
| chunk_index | Position in document |
| start_index | Character offset |
| indexed_at | Indexing timestamp |
| fetched_at | Content fetch timestamp |

## Scoring

Search results include a similarity score (0-1):

- **0.9+**: Highly relevant match
- **0.7-0.9**: Good match
- **0.5-0.7**: Partial match
- **<0.5**: Weak match

The score represents cosine similarity between query and chunk embeddings.

## Storage Location

ChromaDB data persists in:

```
backend/data/chroma/
├── chroma.sqlite3         # Metadata database
└── {collection-uuid}/     # Vector data
    ├── data_level0.bin
    ├── header.bin
    ├── length.bin
    └── link_lists.bin
```

## Knowledge Status Integration

Indexing automatically updates the knowledge item:

| Action | Status Change | Fields Updated |
| ------ | ------------- | -------------- |
| Index success | `pending` → `active` | `content_hash`, `last_fetched_at`, `indexed_at` |
| Index failure | `pending` → `error` | `status` only |
| Re-index | Unchanged | `content_hash`, `last_fetched_at`, `indexed_at` |

## Testing

The RAG system includes comprehensive tests (`tests/ut/test_rag.py`):

```bash
# Run RAG tests
uv run pytest tests/ut/test_rag.py -v
```

### Test Coverage

- Empty collection queries
- Indexing with valid markdown files
- Search after indexing
- Category filtering
- Index removal
- Bulk indexing (`index-all`)
- Status and hash updates
- Error handling for invalid files

### Test Example

```python
@pytest.mark.asyncio
async def test_rag_search_after_indexing(client, sample_markdown_file):
    # Create and index a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Search Test Document",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "category": "SearchTest"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    await client.post(f"/api/rag/index/{knowledge_id}")
    
    # Search for content
    search_response = await client.get("/api/rag/search?q=Python+programming&n=3")
    assert search_response.json()["total_results"] > 0
```

## Performance Considerations

### Chunk Size

- Smaller chunks: More precise retrieval, more storage
- Larger chunks: More context per result, less precision

Default (1000 chars) balances these tradeoffs.

### Batch Indexing

For initial setup, use `index-all` endpoint to process documents in batch rather than individual calls.

### Embedding Cache

Embeddings are computed once during indexing. Queries compute embeddings on-demand (fast for short queries).

## Error Handling

The RAG service handles errors gracefully:

```json
{
  "success": false,
  "knowledge_id": 1,
  "chunks_indexed": 0,
  "content_hash": "",
  "error": "File not found: /nonexistent/path/file.md"
}
```

Common errors:

| Error | Cause | Resolution |
| ----- | ----- | ---------- |
| File not found | Invalid file path in URI | Verify the `uri` field points to an existing file |
| No content to index | Empty document | Add content to the document |
| ChromaDB error | Storage issue | Check disk space and permissions |
