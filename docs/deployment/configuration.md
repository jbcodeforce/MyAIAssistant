# Configuration Reference

Environment variables and configuration options for MyAIAssistant.

## Backend Configuration

### Environment Variables

Create a `.env` file in the project root or set these environment variables:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `APP_NAME` | MyAIAssistant Backend | Application name |
| `APP_VERSION` | 0.1.0 | Application version |
| `DATABASE_URL` | sqlite+aiosqlite:///./myaiassistant.db | Database connection string |
| `CORS_ORIGINS` | http://localhost:3000,http://localhost | Allowed CORS origins (comma-separated) |

### Example `.env` File

```env
APP_NAME=MyAIAssistant Backend
APP_VERSION=0.1.0
DATABASE_URL=sqlite+aiosqlite:///./myaiassistant.db
CORS_ORIGINS=http://localhost:3000,http://localhost
```

### Database Configuration

#### SQLite (Default)

```env
DATABASE_URL=sqlite+aiosqlite:///./myaiassistant.db
```

#### PostgreSQL (Production)

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myaiassistant
```

### RAG Configuration

The RAG service uses these defaults (configurable in code):

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `persist_directory` | ./data/chroma | ChromaDB storage location |
| `collection_name` | knowledge_base | Vector collection name |
| `chunk_size` | 1000 | Text chunk size in characters |
| `chunk_overlap` | 200 | Overlap between chunks |
| `embedding_model` | all-MiniLM-L6-v2 | Sentence transformer model |

## Frontend Configuration

### Vite Configuration

API proxy settings in `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### Docker Configuration

For Docker deployments, the frontend nginx configuration proxies API requests:

```nginx
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Local Development

### Backend Setup

```bash
cd backend

# Install dependencies
uv sync --extra dev

# Create .env file
cp .env.example .env

# Run development server
uv run uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

## Docker Configuration

### Using Environment Variables

With `docker run`:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./myaiassistant.db \
  -e CORS_ORIGINS=http://localhost \
  myaiassistant-backend
```

With `docker-compose`:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=sqlite:///./myaiassistant.db
      - CORS_ORIGINS=http://localhost
```

With `.env` file:

```yaml
services:
  backend:
    env_file:
      - .env
```

## CORS Configuration

The backend configures CORS middleware:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For development, common origins:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost
```

For production, restrict to your domain:

```env
CORS_ORIGINS=https://yourdomain.com
```

## Logging

The backend uses Python's standard logging:

```python
import logging
logger = logging.getLogger(__name__)
```

Configure log level via environment:

```env
LOG_LEVEL=INFO
```

## Performance Tuning

### Uvicorn Workers

For production, run multiple workers:

```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Database Connection Pool

For PostgreSQL, configure pool size:

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

### ChromaDB Settings

Adjust chunk settings for your use case:

```python
RAGService(
    chunk_size=500,      # Smaller for precise retrieval
    chunk_overlap=100    # Reduce for less redundancy
)
```

## Troubleshooting

### Module not found errors

```bash
uv sync --extra dev
```

### Port already in use

```bash
lsof -ti:8000 | xargs kill -9
```

### Database locked

```bash
rm myaiassistant.db
# Database recreates on startup
```

### CORS errors

Check that `CORS_ORIGINS` includes your frontend URL.

### Docker build failures

```bash
docker-compose build --no-cache
```

