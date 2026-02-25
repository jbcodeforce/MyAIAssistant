# Database Operations

The CRUD layer uses session-per-request and injected session per table CRUD operation.

All DB work is done in a single request by using the same AsyncSession. Commit/rollback is controlled at the request level (e.g. after the handler runs). 

For example, in backend/app/db/crud/todo.py, update_todo and delete_todo call get_todo(db, todo_id) with the same db. That keeps everything in one transaction and on the same session/cache. If each function created its own session, those would be separate transactions and you’d lose that consistency and reuse.

The caller (FastAPI with get_db, or a script/job that uses get_session_maker()) owns “create session → use it → commit/rollback → close.” CRUD is just “given a session, do these reads/writes.” That keeps CRUD independent of how and where it’s used (HTTP, CLI, background task) and makes it easy to test by passing in a test session.

Tests can override get_db and inject a session (e.g. from a test DB or a transaction that gets rolled back). CRUD code doesn’t need to know; it just receives a session. If CRUD created sessions internally, you’d have to override or mock the session factory inside the CRUD module instead of at the app boundary.