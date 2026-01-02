# MyAIAssistant Backend

FastAPI backend for the MyAIAssistant application.

## Quick Start

Set environment variable for the config.yaml

```bash
# Install dependencies
uv sync

# Start PostgreSQL (using Docker)
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=myaiassistant \
  postgres:16-alpine

# Run development server
uv run uvicorn app.main:app --reload
```

API available at `http://localhost:8000` with docs at `/docs`.

## Docker

```bash
docker build -t myaiassistant-backend .
docker run -p 8000:8000 myaiassistant-backend
```

## API Endpoints

| Module | Path | Description |
| ------ | ---- | ----------- |
| Todos | `/api/v1/todos` | Task management |
| Knowledge | `/api/v1/knowledge` | Knowledge items |
| RAG | `/api/v1/rag` | Indexing and search |

## Configuration

The backend loads configuration from multiple sources (highest priority first):
1. Environment variables
2. `.env` file
3. User config file (via `CONFIG_FILE` env var)
4. Default `app/config.yaml`

### Running with Custom Config

To use different database and vector store locations:

```bash
# Create your config file (copy from config.example.yaml)
cp config.example.yaml /path/to/my_config.yaml

# Edit with your PostgreSQL connection string
# database_url: "postgresql+asyncpg://user:password@localhost:5432/mydb"
# chroma_persist_directory: "/data/myapp/vectorstore"

# Run with custom config
CONFIG_FILE=/path/to/my_config.yaml uv run uvicorn app.main:app --reload

# Verify config is loaded correctly
curl http://localhost:8000/debug/config
```

### Key Configuration Options

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `database_url` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/myaiassistant` |
| `chroma_persist_directory` | ChromaDB storage path | `./data/chroma` |
| `chroma_collection_name` | Vector store collection name | `knowledge_base` |

Note: For Docker Compose deployments, use `postgres` as the hostname (the service name).

## Testing

Tests use an in-memory SQLite database for isolation:

```bash
uv sync --all-extras  # Install dev dependencies including aiosqlite
uv run pytest
```

## Documentation

See [full documentation](../docs/) for detailed implementation guides.
