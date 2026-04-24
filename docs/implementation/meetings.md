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

### Meeting-Creation Flow

#### Frontend (MeetingCreate.vue)
* User fills meeting_id, optional org / project, attendees (presents in the form), and markdown content.
* Create runs handleCreate, which builds a payload and calls the Pinia store
* Store (meetingRefStore.js): createItem → meetingRefsApi.create(meetingRef).
* HTTP (api.js): POST /meeting-refs/ with the JSON body (no file_ref from the client; the server chooses the path).

#### API layer (FastAPI)
* Router: app/api/meeting_refs.py, mounted at /api in main.py → POST /api/meeting-refs/.
* Handler: create_meeting_ref injects:
  * db → get_db
  * notes_service → MeetingNotesService / get_meeting_notes_service

Flow inside the handler:

* Conflict check: crud.get_meeting_ref_by_meeting_id — if meeting_id exists → 409.
* Optional FK resolution: if org_id / project_id are set, load org/project to get names for the folder layout (and 404 if missing).
* Filesystem write first: notes_service.save_note(...) with meeting_id, content, and optional org_name / project_name.
* DB insert: crud.create_meeting_ref with the returned file_ref string plus metadata.

#### Filesystem (MeetingNotesService)
* Root: settings.notes_root, default docs/meetings (see app/core/config.py and config.yaml), resolved relative to the process working directory unless configured as absolute.
* Relative path (_build_file_path → save_note):
  * Folders: sanitized org name, else general / sanitized project name, else general.
  * File name: {YYYY-MM-DD}-{sanitized_meeting_id}.md (date defaults to “now”).
* I/O: mkdir -p on the parent directory, then write_text for the markdown.

on disk you get: {notes_root}/{org_or_general}/{project_or_general}/{date}-{meeting_id}.md,

#### Database (crud.create_meeting_ref)
* `app/db/crud/meeting.py` builds a Meeting row: meeting_id, file_ref (relative path under notes_root), project_id, org_id, attendees, then add → commit → refresh.
* The body of the note is not in SQLite; only metadata and file_ref are persisted, as the doc states.

## Database Model

[See schemas/meeting_ref.py](https://github.com/jbcodeforce/MyAIAssistant/blob/640ee852e3bdd9183f0e841134eba01130774a95/backend/app/api/schemas/meeting_ref.py#L14-L28)

## API Endpoints

[See app/api/metrics.py](https://github.com/jbcodeforce/MyAIAssistant/blob/main/backend/app/api/metrics.py)

* POST /api/meeting-refs/
* List Meeting Notes: GET /api/meeting-refs/?org_id=1&project_id=5
* Get Meeting Note: GET /api/meeting-refs/{id}
* Get Meeting Content: GET /api/meeting-refs/{id}/content
* Update Meeting Note: PUT /api/meeting-refs/{id}
* Delete Meeting Note: DELETE /api/meeting-refs/{id}   -> Deletes both the database record and the associated markdown file.
* Search by Meeting ID: GET /api/meeting-refs/search/by-meeting-id?meeting_id=mtg-2026-01-05-kickoff

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
└── general/
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

