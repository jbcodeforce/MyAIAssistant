# Todo Management

The todo management system provides a complete task tracking solution based on the Eisenhower Matrix.

## Eisenhower Matrix

Tasks are classified along two dimensions:

| Quadrant | Urgency | Importance | Action |
| -------- | ------- | ---------- | ------ |
| Q1 - Do First | Urgent | Important | Handle immediately |
| Q2 - Schedule | Not Urgent | Important | Plan and prioritize |
| Q3 - Delegate | Urgent | Not Important | Delegate if possible |
| Q4 - Eliminate | Not Urgent | Not Important | Consider eliminating |

## Database Model

The `Todo` model stores all task information:

```python
class Todo(Base):
    __tablename__ = "todos"

    id: int                    # Primary key
    title: str                 # Required task title
    description: str           # Optional detailed description
    status: str                # Open, Started, Completed, Cancelled
    urgency: str               # Urgent, Not Urgent
    importance: str            # Important, Not Important
    category: str              # Optional grouping category
    created_at: datetime       # Auto-generated timestamp
    updated_at: datetime       # Auto-updated timestamp
    completed_at: datetime     # Set when status becomes Completed
    due_date: datetime         # Optional due date
    source_type: str           # Reference type (meeting, knowledge)
    source_id: int             # ID of source reference
```

## API Endpoints

### Create Todo

```bash
POST /api/v1/todos/
Content-Type: application/json

{
  "title": "Review documentation",
  "description": "Review project documentation for accuracy",
  "status": "Open",
  "urgency": "Urgent",
  "importance": "Important",
  "category": "Documentation"
}
```

### List Todos with Filters

```bash
GET /api/v1/todos/?status=Open&urgency=Urgent&limit=10
```

Query parameters:

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| status | string | Filter by status |
| urgency | string | Filter by urgency level |
| importance | string | Filter by importance level |
| category | string | Filter by category |
| search | string | Substring match in title or description (case-insensitive, max 200 chars) |
| skip | int | Pagination offset |
| limit | int | Maximum results |

### Get Canvas Quadrant

Retrieve todos for a specific matrix quadrant:

```bash
GET /api/v1/todos/canvas/Urgent/Important
```

### Get Unclassified Todos

Todos without urgency or importance classification:

```bash
GET /api/v1/todos/unclassified
```

### Update Todo

```bash
PUT /api/v1/todos/{id}
Content-Type: application/json

{
  "status": "Started"
}
```

When status changes to "Completed", the `completed_at` timestamp is automatically set.

### Delete Todo

```bash
DELETE /api/v1/todos/{id}
```

## Frontend Components

### TodoCanvas

The main dashboard view displays todos in a 2x2 matrix grid. Each quadrant represents one combination of urgency and importance.

```
┌────────────────────┬────────────────────┐
│    DO FIRST        │     SCHEDULE       │
│  Urgent/Important  │ Not Urgent/Import. │
├────────────────────┼────────────────────┤
│    DELEGATE        │    ELIMINATE       │
│  Urgent/Not Imp.   │ Not Urgent/Not Imp.│
└────────────────────┴────────────────────┘
```

### TodoCard

Individual todo cards display:

- Title and description
- Status indicator (color-coded)
- Category badge
- Due date (if set)
- Edit and delete actions

### Drag and Drop

Todos can be dragged between quadrants to update their urgency and importance classification. The drop action triggers an API call to update the todo.

## Task Search (Design)

The dashboard provides a search form to filter tasks by a string in **title** or **description**.

**Backend**

- The list-todos endpoint accepts an optional `search` query parameter (max length 200). When present and non-empty (after stripping whitespace), the API filters todos where the normalized search term appears as a substring in `title` or in `description`. Matching is case-insensitive and works on both PostgreSQL (production) and SQLite (tests) using `func.lower()` and `like()` with a bound pattern. Null descriptions are handled so that only the title is matched when description is missing.

**Frontend**

- The Dashboard header includes a search input, a "Search" button (form submit and Enter), and a "Clear" button shown when a search term is present. Submitting the form or clicking Search calls `fetchTodos` with the same status/limit as the default load plus the `search` param when non-empty. Clear resets the input and reloads without search. The existing `todosApi.list(params)` and `todoStore.fetchTodos(params)` pass the search param through; no API or store changes were required beyond the Dashboard passing the param.

**Data flow**

- User types a term and submits (Search or Enter) -> Dashboard calls `loadTodos()` with `search` in params -> store calls `GET /api/todos/?status=Open,Started&limit=500&search=...` -> backend applies title/description filter -> response populates store -> TodoCanvas and unclassified section show the filtered list. Clearing the search or submitting an empty term reloads without the search param.

**Out of scope**

- Debounced search-as-you-type, separate title vs description filters, and full-text or ranked search are not implemented; substring match is sufficient for the current requirement.

## State Management

The `todoStore` (Pinia) manages:

- Todo list for each quadrant
- Unclassified todos
- Loading states
- CRUD operations via API service

```javascript
// Example usage
const todoStore = useTodoStore()

// Fetch todos for dashboard
await todoStore.fetchCanvasTodos()

// Create new todo
await todoStore.createTodo({
  title: 'New task',
  urgency: 'Urgent',
  importance: 'Important'
})
```

## Testing

The test suite covers:

- CRUD operations via API
- Filtering and pagination
- Quadrant-based retrieval
- Status transitions
- Timestamp auto-updates

Run tests:

```bash
cd backend
uv run pytest tests/ut/test_todos.py -v
```

