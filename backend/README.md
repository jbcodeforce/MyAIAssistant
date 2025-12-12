# MyAIAssistant Backend

FastAPI backend for the MyAIAssistant application.

## Quick Start

```bash
# Install dependencies
uv sync

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

# Edit with your paths (use absolute paths for clarity)
# database_url: "sqlite+aiosqlite:////data/myapp/assistant.db"
# chroma_persist_directory: "/data/myapp/vectorstore"

# Run with custom config
CONFIG_FILE=/path/to/my_config.yaml uv run uvicorn app.main:app --reload

# Verify config is loaded correctly
curl http://localhost:8000/debug/config
```

### Key Configuration Options

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `database_url` | SQLite connection string | `sqlite+aiosqlite:///./myaiassistant.db` |
| `chroma_persist_directory` | ChromaDB storage path | `./data/chroma` |
| `chroma_collection_name` | Vector store collection name | `knowledge_base` |

Note: Relative paths are resolved from the current working directory when the app starts.

## Testing

```bash
uv run pytest
```

## Documentation

See [full documentation](../docs/) for detailed implementation guides.

