# Some how to

## enlarge text area to fit panel width

Modify css like in Meeting.vue

```css
.content-view {
  width: 100%;
}

.meeting-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
  max-width: 100%;
}

```

## Modify content of a table in SQLlite

* In VSCode or Cursor: Open your .sqlite or .db file.
* Locate the SQLite Explorer section in your sidebar and click a table to display its data.
* Right-click your table in the SQLite Explorer and select New Query.
* Write an UPDATE statement using this syntax
  ```sql
  update meetings set file_ref = 'highmark/general/2026-04-24-weekly-meeting.md' where meeting_id = 'Weekly meeting';
  ```
* Highlight the query, right-click, and select Run Query to apply the change