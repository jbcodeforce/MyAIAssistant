# Assets

The assets system provides management of reusable resources developed within projects or tasks. Assets can be code repositories, documents, templates, or any other resources that can be referenced and reused.

## Concepts

### What is an Asset?

An asset is a reusable resource that can be developed during project work or task completion. Assets are typically:

- **Code Repositories**: GitHub repos, code libraries, or scripts
- **Documents**: Templates, guides, or reference materials
- **Tools**: Utilities, automation scripts, or helper applications
- **Resources**: Any reusable material with a URL reference

### Asset Organization

Assets support optional links to:

- **Projects**: Assets developed for or used in specific projects
- **Tasks (Todos)**: Assets created during task execution

This linking enables tracking which assets were produced from which work.

## Database Model

```python
class Asset(Base):
    __tablename__ = "assets"

    id: int                    # Primary key
    name: str                  # Asset name
    description: str           # Short description
    reference_url: str         # URL to the asset resource
    project_id: int            # Optional project link
    todo_id: int               # Optional task link
    created_at: datetime       # Record creation time
    updated_at: datetime       # Last update time
```

## API Endpoints

### Create Asset

```bash
POST /api/assets/
Content-Type: application/json

{
  "name": "Flink SQL Helper Library",
  "description": "Reusable SQL templates for Flink jobs",
  "reference_url": "https://github.com/org/flink-sql-helpers",
  "project_id": 1
}
```

### List Assets

```bash
GET /api/assets/?project_id=1&todo_id=5
```

Query parameters:

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| project_id | int | Filter by project ID |
| todo_id | int | Filter by task ID |
| skip | int | Pagination offset |
| limit | int | Maximum results (max 500) |

### Get Asset

```bash
GET /api/assets/{id}
```

### Update Asset

```bash
PUT /api/assets/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "reference_url": "https://new-url.com/resource",
  "project_id": 2,
  "todo_id": null
}
```

### Delete Asset

```bash
DELETE /api/assets/{id}
```

## Frontend View

The Assets view provides:

- Table listing with name, description, project, task, URL, and creation date
- Filters by project and task
- Create modal with form fields
- Edit modal for updating asset details
- Clickable reference URLs that open in new tab
- Delete confirmation

## Use Cases

### Code Library Asset

Track reusable code libraries developed during projects:

```json
{
  "name": "Python Data Utilities",
  "description": "Common data transformation functions",
  "reference_url": "https://github.com/team/python-data-utils",
  "project_id": 3
}
```

### Document Template Asset

Track document templates created for repeated use:

```json
{
  "name": "Customer Onboarding Template",
  "description": "Standard onboarding document structure",
  "reference_url": "https://docs.google.com/document/d/abc123",
  "todo_id": 15
}
```

### Reference Documentation Asset

Track useful external documentation:

```json
{
  "name": "Apache Flink SQL Reference",
  "description": "Official Flink SQL documentation",
  "reference_url": "https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/sql/overview/"
}
```

## Best Practices

### Naming Conventions

- Use clear, descriptive names
- Include technology or domain prefix when helpful
- Keep names concise but meaningful

Examples:

- "Flink CDC Connector Config"
- "Customer API Integration Script"
- "Weekly Report Template"

### Description Guidelines

- Keep descriptions brief (1-2 sentences)
- Focus on what the asset does or provides
- Mention key technologies or use cases

### Reference URLs

- Use stable, permanent URLs when possible
- For GitHub, link to the repository root or specific release
- For documents, ensure proper sharing permissions

### Linking Strategy

- Link to projects for project-specific assets
- Link to tasks when the asset was a deliverable
- Leave unlinked for general-purpose assets

## Integration with Projects

Assets linked to projects appear in the project context, enabling:

- Tracking of project deliverables
- Discovery of reusable resources
- Documentation of project outputs

## Integration with Tasks

Assets linked to tasks enable:

- Recording of task outputs
- Reference materials for task completion
- Building a library of work products

