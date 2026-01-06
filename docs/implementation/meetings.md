# Meeting Notes

The meeting notes system provides centralized management of meeting documentation with links to organizations and projects. Meeting content is stored as markdown files while metadata is tracked in the database.

## Concepts

### Meeting References

A meeting reference is a database record that links to a markdown file containing meeting notes. Each meeting has:

- **Meeting ID**: Unique identifier (e.g., `mtg-2026-01-05-kickoff`)
- **Organization Link**: Optional association with an organization
- **Project Link**: Optional association with a project
- **File Reference**: Path to the markdown file containing the notes

### Content Storage

Meeting notes content is stored in markdown files on the filesystem. The database stores only the reference path, enabling:

- Version control of meeting content via git
- Large document support without database bloat
- Direct editing with any text editor

## Database Model

```python
class MeetingRef(Base):
    __tablename__ = "meeting_refs"

    id: int                    # Primary key
    meeting_id: str            # Unique meeting identifier
    project_id: int            # Optional project link
    org_id: int                # Optional organization link
    file_ref: str              # Path to markdown file
    created_at: datetime       # Record creation time
    updated_at: datetime       # Last update time
```

## API Endpoints

### Create Meeting Note

```bash
POST /api/meeting-refs/
Content-Type: application/json

{
  "meeting_id": "mtg-2026-01-05-kickoff",
  "org_id": 1,
  "project_id": 5,
  "content": "# Meeting Title\n\n## Attendees\n- Person 1\n\n## Notes\n..."
}
```

The content is automatically written to a markdown file and the file path is stored in `file_ref`.

### List Meeting Notes

```bash
GET /api/meeting-refs/?org_id=1&project_id=5
```

Query parameters:

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| org_id | int | Filter by organization ID |
| project_id | int | Filter by project ID |
| skip | int | Pagination offset |
| limit | int | Maximum results (max 500) |

### Get Meeting Note

```bash
GET /api/meeting-refs/{id}
```

### Get Meeting Content

```bash
GET /api/meeting-refs/{id}/content
```

Returns the markdown content of the meeting file:

```json
{
  "content": "# Meeting Title\n\n## Attendees\n..."
}
```

### Update Meeting Note

```bash
PUT /api/meeting-refs/{id}
Content-Type: application/json

{
  "org_id": 2,
  "project_id": null,
  "content": "# Updated Meeting Notes\n..."
}
```

### Delete Meeting Note

```bash
DELETE /api/meeting-refs/{id}
```

Deletes both the database record and the associated markdown file.

### Search by Meeting ID

```bash
GET /api/meeting-refs/search/by-meeting-id?meeting_id=mtg-2026-01-05-kickoff
```

## File Storage Structure

Meeting files are stored in a structured directory hierarchy:

```
{workspace}/docs/meetings/
├── {organization-slug}/
│   ├── {project-slug}/
│   │   ├── {date}-{meeting-id}.md
│   │   └── {date}-{meeting-id}.md
│   └── general/
│       └── {date}-{meeting-id}.md
└── unassigned/
    └── {date}-{meeting-id}.md
```

## Frontend View

The Meetings view provides:

- Table listing with meeting ID, organization, project, file path, and date
- Filters by organization and project
- Create modal with markdown editor and live preview
- View modal for reading meeting content
- Edit modal for updating content and associations
- Delete confirmation

## Meeting Note Template

The default template for new meeting notes:

```markdown
# Meeting Title

## Attendees
- Name 1
- Name 2

## Agenda
1. Topic 1
2. Topic 2

## Notes
...

## Action Items
- [ ] Action 1
- [ ] Action 2
```

## Best Practices

### Meeting ID Convention

Use a consistent naming convention for meeting IDs:

- Format: `{type}-{date}-{description}`
- Examples:
  - `mtg-2026-01-05-weekly-standup`
  - `review-2026-01-05-q1-planning`
  - `onsite-2026-01-05-customer-kickoff`

### Organization

- Always link meetings to the relevant organization
- Link to projects when the meeting is project-specific
- Use descriptive meeting IDs for easy identification

### Content Structure

- Use consistent heading structure
- Include attendees for context
- Document action items with task checkboxes
- Add timestamps for key decisions

