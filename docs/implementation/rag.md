# RAG System

The Retrieval-Augmented Generation (RAG) system enables semantic search across the knowledge base using vector embeddings.

## Architecture

Classical RAG architecture supported by the Code.

![](./images/docu_mgt.drawio.png)

## Components

### Document Loader

Loads document content from various sources (`app/rag/document_loader.py`):

```python
class DocumentLoader:
    async def load(uri: str, document_type: str) -> LoadedDocument:
        # Returns content and metadata including content_hash
```

Supported sources:

| Type | Description | Example URI |
| ---- | ----------- | ----------- |
| markdown | Local markdown files | `file:///path/to/doc.md` |
| website | Web page content | `https://example.com/page` |

The loader returns a `LoadedDocument` containing:

- `content`: The extracted text content
- `content_hash`: MD5 hash for change detection
- `metadata`: Source information

### Text Splitter

Splits documents into chunks for embedding (`app/rag/text_splitter.py`):

```python
class RecursiveTextSplitter:
    def __init__(
        chunk_size: int = 1000,      # Target chunk size in characters
        chunk_overlap: int = 200      # Overlap between chunks
    )
```

The recursive splitter attempts to split on natural boundaries:

1. Paragraphs (`\n\n`)
2. Lines (`\n`)
3. Sentences (`. `)
4. Words (` `)

Each chunk includes metadata:

- `chunk_index`: Position in the document
- `start_index`: Character offset in original content

### Embedding Model

Uses sentence-transformers for local embedding generation:

- Model: `all-MiniLM-L6-v2`
- Runs entirely locally (no external API calls)
- Produces 384-dimensional vectors
- Optimized for semantic similarity

### Vector Store

ChromaDB provides persistent vector storage (`app/rag/service.py`):

```python
RAGService(
    persist_directory="./data/chroma",
    collection_name="knowledge_base",
    chunk_size=1000,
    chunk_overlap=200,
    embedding_model="all-MiniLM-L6-v2"
)
```

Features:

- Cosine similarity for search (configured via `hnsw:space`)
- Metadata filtering by category, tags, knowledge_id
- Persistent storage across restarts
- Automatic collection management

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
| document_type | markdown or website |
| category | Document category |
| tags | Associated tags |
| chunk_index | Position in document |
| start_index | Character offset |
| indexed_at | Indexing timestamp |

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
| Index success | `pending` → `active` | `content_hash`, `last_fetched_at` |
| Index failure | `pending` → `error` | `status` only |
| Re-index | Unchanged | `content_hash`, `last_fetched_at` |

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
  "content_hash": null,
  "error": "File not found: /nonexistent/path/file.md"
}
```

Common errors:

| Error | Cause | Resolution |
| ----- | ----- | ---------- |
| File not found | Invalid file path in URI | Verify the `uri` field points to an existing file |
| No content to index | Empty document | Add content to the document |
| ChromaDB error | Storage issue | Check disk space and permissions |

