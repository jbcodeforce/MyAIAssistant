# Knowledge Base

The knowledge base provides centralized storage for document metadata, enabling organization and retrieval of reference materials.

## Concepts

### Knowledge Items

A knowledge item is a metadata record pointing to a document source. The actual document content is stored externally (filesystem or web).

Supported document types:

- **markdown**: Local markdown files on the filesystem
- **website**: URLs to web pages for reference

### Organization

Knowledge items support:

- **Categories**: Hierarchical grouping (e.g., "Engineering/Backend")
- **Tags**: Comma-separated labels for cross-cutting concerns
- **Status**: Lifecycle state tracking

## Database Model

```python
class Knowledge(Base):
    __tablename__ = "knowledge"

    id: int                    # Primary key
    title: str                 # Display title
    description: str           # Optional description
    uri: str                   # Path or URL to document
    document_type: str         # markdown, website
    category: str              # Optional category
    tags: str                  # Comma-separated tags
    status: str                # active, pending, error, archived
    content_hash: str          # Hash of indexed content
    last_fetched_at: datetime  # Last content fetch time
    created_at: datetime       # Record creation time
    updated_at: datetime       # Last update time
```

## API Endpoints

### Create Knowledge Item

```bash
POST /api/v1/knowledge/
Content-Type: application/json

{
  "title": "FastAPI Documentation",
  "description": "Official FastAPI framework documentation",
  "uri": "https://fastapi.tiangolo.com/",
  "document_type": "website",
  "category": "Engineering/Frameworks",
  "tags": "python,api,web"
}
```

For local markdown files:

```bash
{
  "title": "Project README",
  "uri": "/path/to/project/README.md",
  "document_type": "markdown",
  "category": "Documentation"
}
```

### List Knowledge Items

```bash
GET /api/v1/knowledge/?category=Engineering&status=active
```

Query parameters:

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| document_type | string | Filter by type (markdown, website) |
| status | string | Filter by status |
| category | string | Filter by category |
| tag | string | Filter by tag (partial match) |
| skip | int | Pagination offset |
| limit | int | Maximum results (max 500) |

### Get Knowledge Item

```bash
GET /api/v1/knowledge/{id}
```

### Update Knowledge Item

```bash
PUT /api/v1/knowledge/{id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "archived"
}
```

### Delete Knowledge Item

```bash
DELETE /api/v1/knowledge/{id}
```

## Status Lifecycle

```
pending ──▶ active ──▶ archived
    │          │
    └──────────┴──▶ error
```

| Status | Description |
| ------ | ----------- |
| pending | Newly created, not yet indexed |
| active | Successfully indexed and searchable |
| error | Indexing failed (check logs) |
| archived | No longer active, excluded from search |

## Integration with RAG

Knowledge items serve as the source for RAG indexing:

1. Create knowledge item with URI
2. Call RAG index endpoint to process document
3. Status updates to "active" on success
4. Content hash tracks document version

```bash
# Index a specific knowledge item
POST /api/v1/rag/index/{knowledge_id}

# Index all pending items
POST /api/v1/rag/index-all?status=pending
```

## Content Hash

The `content_hash` field stores an MD5 hash of the indexed document content. This enables:

- Detecting document changes
- Skipping re-indexing of unchanged documents
- Version tracking

## Best Practices

### File Organization

For markdown documents, use a consistent directory structure:

```
/knowledge/
├── engineering/
│   ├── backend/
│   │   ├── api-design.md
│   │   └── database-schema.md
│   └── frontend/
│       └── component-guide.md
├── processes/
│   ├── code-review.md
│   └── deployment.md
└── meetings/
    └── 2024-01-15-planning.md
```

### Tagging Strategy

Use consistent tags across knowledge items:

- Technology tags: `python`, `vue`, `docker`
- Topic tags: `architecture`, `security`, `performance`
- Team tags: `backend`, `frontend`, `devops`

### Category Hierarchy

Use forward-slash notation for hierarchy:

- `Engineering/Backend`
- `Engineering/Frontend`
- `Processes/Development`
- `Meetings/Weekly`

