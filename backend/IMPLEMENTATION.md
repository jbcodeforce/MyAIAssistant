# Backend Todos Component Implementation

This document describes the implementation of the backend todos component for MyAIAssistant.

## Overview

The backend todos component provides a complete RESTful API for managing todo items with support for the Urgent/Important matrix classification system.

## Components Implemented

### 1. Database Models (`app/db/models.py`)

SQLAlchemy ORM model for Todo items with the following fields:

- `id`: Primary key
- `title`: Todo title (required)
- `description`: Detailed description (optional)
- `status`: Current status (Open, Started, Completed, Cancelled)
- `urgency`: Urgency level (Urgent, Not Urgent)
- `importance`: Importance level (Important, Not Important)
- `category`: Grouping category (optional)
- `created_at`: Creation timestamp (auto-generated)
- `updated_at`: Last update timestamp (auto-updated)
- `completed_at`: Completion timestamp (set when status changes to Completed)
- `due_date`: Optional due date
- `source_type`: Reference to source (e.g., meeting, knowledge)
- `source_id`: ID of the source reference

### 2. Pydantic Schemas (`app/schemas/todo.py`)

Request and response models for API validation:

- `TodoBase`: Base schema with common fields
- `TodoCreate`: Schema for creating new todos
- `TodoUpdate`: Schema for updating existing todos (all fields optional)
- `TodoResponse`: Schema for todo responses
- `TodoListResponse`: Schema for paginated list responses

### 3. Database Configuration (`app/db/database.py`, `app/core/config.py`)

- Async SQLAlchemy engine setup with SQLite
- Session management with dependency injection
- Configuration management with Pydantic Settings
- Environment variable support via `.env` file

### 4. CRUD Operations (`app/db/crud.py`)

Complete set of database operations:

- `create_todo`: Create a new todo
- `get_todo`: Retrieve a single todo by ID
- `get_todos`: List todos with filtering and pagination
- `update_todo`: Update a todo (auto-sets completed_at when status changes to Completed)
- `delete_todo`: Delete a todo
- `get_todos_by_urgency_importance`: Get todos for a specific quadrant
- `get_unclassified_todos`: Get todos without urgency/importance classification

### 5. API Endpoints (`app/api/todos.py`)

RESTful API endpoints:

- `POST /api/v1/todos/`: Create a new todo
- `GET /api/v1/todos/`: List todos with optional filters (status, urgency, importance, category)
- `GET /api/v1/todos/unclassified`: List unclassified todos
- `GET /api/v1/todos/canvas/{urgency}/{importance}`: List todos by quadrant for canvas view
- `GET /api/v1/todos/{id}`: Get a specific todo
- `PUT /api/v1/todos/{id}`: Update a todo
- `DELETE /api/v1/todos/{id}`: Delete a todo

### 6. FastAPI Application (`app/main.py`)

Main application setup:

- FastAPI app initialization with lifespan management
- CORS middleware configuration
- Router registration
- Database initialization on startup
- Health check endpoint

### 7. Test Suite (`tests/`)

Comprehensive test coverage:

- Test fixtures for database and HTTP client
- In-memory SQLite database for testing
- Tests for all CRUD operations
- Tests for filtering and pagination
- Tests for quadrant-based retrieval
- Tests for unclassified todos

## API Usage Examples

### Create a Todo

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

### List Todos with Filters

```bash
curl "http://localhost:8000/api/v1/todos/?status=Open&urgency=Urgent&limit=10"
```

### Get Todos for Canvas Quadrant

```bash
curl "http://localhost:8000/api/v1/todos/canvas/Urgent/Important"
```

### Update a Todo

```bash
curl -X PUT http://localhost:8000/api/v1/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Started"}'
```

### Delete a Todo

```bash
curl -X DELETE http://localhost:8000/api/v1/todos/1
```

## Database Schema

```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'Open',
    urgency VARCHAR(50),
    importance VARCHAR(50),
    category VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    due_date DATETIME,
    source_type VARCHAR(50),
    source_id INTEGER
);
```

## Next Steps

To use this backend:

1. Install dependencies: `uv sync` or `pip install -e .`
2. Create `.env` file from `.env.example`
3. Run the server: `uvicorn app.main:app --reload`
4. Access API docs at `http://localhost:8000/docs`
5. Run tests: `pytest`

## Integration Points

This backend is ready to integrate with:

- Frontend Vue.js application for UI
- Knowledge management system (via source_type/source_id fields)
- Meeting notes system (for todo extraction)
- AI services for semantic search and todo extraction

