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
* Root: settings.notes_root, default **docs/notes** (see app/core/config.py and config.yaml), resolved relative to the process working directory unless configured as absolute.
* Relative path (_build_file_path → save_note):
  * Folders: **{org}/meetings/{project}** with sanitized org and project names, or **general/meetings/general** when org/project are missing.
  * File name: {YYYY-MM-DD}-{sanitized_meeting_id}.md (date defaults to “now”).
* I/O: mkdir -p on the parent directory, then write_text for the markdown.

On disk: `{notes_root}/{org}/meetings/{project}/{date}-{meeting_id}.md`.

Organization **Strategy / Notes**: the database stores **`description_path`** (path relative to `notes_root`, e.g. `acme/notes/strategy.md`); the markdown **content** lives only in that file. GET responses still expose `description` as the file body for the UI, plus `description_path` for the reference. See `app/services/organization_notes.py` and `tools/migrate_org_description_to_path.py` for legacy DB migration.

#### Database (crud.create_meeting_ref)
* `app/db/crud/meeting.py` builds a Meeting row: meeting_id, file_ref (relative path under notes_root), project_id, org_id, attendees, then add → commit → refresh.
* The body of the note is not in SQLite; only metadata and file_ref are persisted, as the doc states.

## Database Model

[See schemas/meeting_ref.py](https://github.com/jbcodeforce/MyAIAssistant/blob/640ee852e3bdd9183f0e841134eba01130774a95/backend/app/api/schemas/meeting_ref.py#L14-L28)

## API Endpoints

Meeting references (`app/api/meeting_refs.py`):

* POST /api/meeting-refs/
* List Meeting Notes: GET /api/meeting-refs/?org_id=1&project_id=5
* Get Meeting Note: GET /api/meeting-refs/{id}
* Get Meeting Content: GET /api/meeting-refs/{id}/content
* Update Meeting Note: PUT /api/meeting-refs/{id}
* Delete Meeting Note: DELETE /api/meeting-refs/{id} — deletes the database record and the markdown file
* Search by Meeting ID: GET /api/meeting-refs/search/by-meeting-id?meeting_id=mtg-2026-01-05-kickoff

Meeting metrics (see [Meeting metrics from markdown headings](#meeting-metrics-from-markdown-headings)):

* GET /api/metrics/meetings/created?period=monthly&days=90 — time series from scanned headings
* POST /api/metrics/meetings/refresh — rescan notes without restarting the app

## File Storage Structure

Meeting files and org strategy notes live under `notes_root` (default `{workspace}/docs/notes`):

```
{workspace}/docs/notes/
├── {organization-slug}/
│   ├── notes/
│   │   ├── strategy.md          # organization description (Strategy / Notes)
│   │   └── images/              # images for strategy markdown
│   └── meetings/
│       ├── {project-slug}/
│       │   └── {date}-{meeting-id}.md
│       └── general/
│           └── {date}-{meeting-id}.md
└── general/
    └── meetings/
        └── general/
            └── {date}-{meeting-id}.md
```

## Meeting metrics from markdown headings

Dashboard “Meetings over time” counts **dated Meeting headings** in markdown, not `Meeting.created_at` insert time. Multiple meetings may live in one file (common in org strategy notes).

### Sources scanned

1. Each organization’s `description_path` file (usually `{org}/notes/strategy.md`)
2. Each meeting reference’s `file_ref` under `notes_root`

### Heading rules

Match `##` or `###` headings whose title starts with `Meeting` and includes a parseable date:

```markdown
## Meeting 01/07
### Meeting 3/17
### Meeting Workshop 2/11/2026
```

Supported date forms: `M/D`, `M/D/YY`, `M/D/YYYY` (zero-padded allowed). Bare `M/D` uses the current calendar year, or the previous year if that date would fall more than 30 days in the future.

Ignored (not counted):

* Undated section titles such as `## Meeting notes` or `## Meetings`
* Headings with no parseable date (treated as dirty for the audit test)

### De-duplication

* Every dated heading in a strategy file counts (including two headings on the same day)
* For meeting files, a heading is skipped if strategy already has the same `(org_id, meeting_date)`

### Persistence and refresh

Implementation: `app/services/meeting_heading_metrics.py`.

| Table | Role |
|-------|------|
| `meeting_heading_events` | One row per kept dated heading (`org_id`, `meeting_date`, `source`, `source_path`, `heading_text`, `heading_line`) |
| `meeting_metrics_meta` | Singleton: `last_evaluated_at`, `files_scanned`, `meetings_found` |

Scan runs:

* On app startup (after `init_db`; failures are logged and do not block boot)
* On `POST /api/metrics/meetings/refresh` (Metrics UI “Refresh meetings” button)

API responses for meeting time series include `last_evaluated_at`.

### Frontend

Metrics dashboard (`Metrics.vue`):

* Summary card: meeting count for the selected day window
* Chart title: “Meetings by Month”
* Shows last evaluated timestamp
* Refresh meetings: calls refresh then reloads the dashboard

### Auditing a notes root

CLI report (preferred for cleaning — per-org table, exit 1 when dirty):

```bash
cd backend
uv run python scripts/report_org_meetings.py /path/to/docs/notes
uv run python scripts/report_org_meetings.py /path/to/customers --dirty-only
```

Integration test (same filesystem rules; fails on dirty headings):

```bash
cd backend
MEETING_METRICS_AUDIT_ROOT=/path/to/docs/notes \
  uv run pytest tests/it/test_meeting_heading_audit.py -m integration -s -v
```

Unit coverage for parsing and de-dupe: `tests/ut/test_meeting_heading_metrics.py`.

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
- For multi-meeting strategy notes, use dated headings (`## Meeting MM/DD` or `## Meeting MM/DD/YYYY`) so metrics can count them
- Include attendees for context
- Document action items with task checkboxes
- Add timestamps for key decisions
