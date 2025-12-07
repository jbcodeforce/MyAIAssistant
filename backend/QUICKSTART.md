# Quick Start Guide

## Installation

1. Install dependencies:

```bash
cd backend
uv sync --extra dev
```

This installs:
- FastAPI and Uvicorn (web framework and server)
- SQLAlchemy and aiosqlite (database)
- Pydantic (data validation)
- pytest and httpx (testing)
- greenlet (required for async SQLAlchemy)

## Running the Server

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

The `--reload` flag enables auto-reload on code changes.

## Accessing the API

### Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

Base URL: `http://localhost:8000/api/v1`

#### Create a Todo

```bash
curl -X POST http://localhost:8000/api/v1/todos/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review documentation",
    "description": "Review project documentation",
    "status": "Open",
    "urgency": "Urgent",
    "importance": "Important",
    "category": "Documentation"
  }'
```

#### List All Todos

```bash
curl http://localhost:8000/api/v1/todos/
```

#### List Todos with Filters

```bash
curl "http://localhost:8000/api/v1/todos/?status=Open&urgency=Urgent"
```

#### Get a Specific Todo

```bash
curl http://localhost:8000/api/v1/todos/1
```

#### Update a Todo

```bash
curl -X PUT http://localhost:8000/api/v1/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Started"}'
```

#### Delete a Todo

```bash
curl -X DELETE http://localhost:8000/api/v1/todos/1
```

#### Get Todos by Quadrant (Canvas View)

```bash
curl http://localhost:8000/api/v1/todos/canvas/Urgent/Important
```

#### List Unclassified Todos

```bash
curl http://localhost:8000/api/v1/todos/unclassified
```

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run tests with verbose output:

```bash
uv run pytest -v
```

Run tests with coverage:

```bash
uv run pytest --cov=app --cov-report=html
```

## Database

The application uses SQLite with an async driver. The database file is created automatically at:

```
backend/myaiassistant.db
```

The database schema is initialized automatically on first run.

## Configuration

Configuration is managed through environment variables. Create a `.env` file:

```bash
cp .env.example .env
```

Available settings:

- `APP_NAME`: Application name (default: "MyAIAssistant Backend")
- `APP_VERSION`: Application version (default: "0.1.0")
- `DATABASE_URL`: Database connection string (default: "sqlite+aiosqlite:///./myaiassistant.db")
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

## Troubleshooting

### Module not found errors

Make sure dependencies are installed:

```bash
uv sync --extra dev
```

### Port already in use

Kill the process using port 8000:

```bash
lsof -ti:8000 | xargs kill -9
```

### Database locked

Stop the server and delete the database file to start fresh:

```bash
rm myaiassistant.db
```

The database will be recreated on next startup.

