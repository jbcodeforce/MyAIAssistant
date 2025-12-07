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

## Testing

```bash
uv run pytest
```

## Documentation

See [full documentation](../docs/) for detailed implementation guides.

