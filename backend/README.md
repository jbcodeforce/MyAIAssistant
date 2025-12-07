# MyAIAssistant Backend

FastAPI backend for MyAIAssistant application.

## Features

- RESTful API for Todo management
- Async SQLAlchemy ORM with SQLite database
- Pydantic models for request/response validation
- CRUD operations for Todos with filtering and pagination
- Support for Urgent/Important matrix classification
- Comprehensive test suite with pytest

## Setup

### Prerequisites

#### For Local Development
- Python 3.12 or higher
- uv package manager (recommended) or pip

#### For Docker Deployment
- Docker 20.10 or higher
- Docker Compose 2.0 or higher (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Build and run
docker build -t myaiassistant-backend .
docker run -p 8000:8000 myaiassistant-backend

# Or use docker-compose (from project root)
cd ..
docker-compose up -d backend
```

See [DOCKER.md](DOCKER.md) for comprehensive Docker deployment guide.

#### Option 2: Local Development

1. Install dependencies:

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

2. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

3. The database will be automatically initialized on first run.

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

## API Endpoints

### Todos

- `POST /api/v1/todos/` - Create a new todo
- `GET /api/v1/todos/` - List todos with optional filters
- `GET /api/v1/todos/{id}` - Get a specific todo
- `PUT /api/v1/todos/{id}` - Update a todo
- `DELETE /api/v1/todos/{id}` - Delete a todo
- `GET /api/v1/todos/unclassified` - List unclassified todos
- `GET /api/v1/todos/canvas/{urgency}/{importance}` - List todos by quadrant

### Health Check

- `GET /health` - Health check endpoint

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Configuration
│   ├── db/            # Database models and CRUD
│   └── schemas/       # Pydantic schemas
├── tests/             # Test suite
└── pyproject.toml     # Dependencies
```

