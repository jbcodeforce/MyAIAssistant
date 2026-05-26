"""get_todos_by_organization includes todos linked via meeting source (no project/org on todo)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.models import Organization, Todo


@pytest.mark.asyncio
async def test_get_todos_by_organization_includes_meeting_sourced(db_session: AsyncSession):
    org = Organization(name="OrgMeetingTodo")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    meeting = await crud.create_meeting_ref(
        db=db_session,
        meeting_id="mtg-org-todo-unit-test",
        file_ref="/tmp/test-meeting-notes.md",
        org_id=org.id,
    )

    todo = Todo(
        title="From meeting",
        status="Open",
        source_type="meeting",
        source_id=meeting.id,
    )
    db_session.add(todo)
    await db_session.commit()
    await db_session.refresh(todo)

    todos, total = await crud.get_todos_by_organization(
        db=db_session, organization_id=org.id, skip=0, limit=50
    )

    assert total >= 1
    assert any(t.id == todo.id for t in todos)


@pytest.mark.asyncio
async def test_get_todos_by_organization_meeting_source_type_case_insensitive(
    db_session: AsyncSession,
):
    org = Organization(name="OrgMeetingTodoCase")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    meeting = await crud.create_meeting_ref(
        db=db_session,
        meeting_id="mtg-org-todo-case-test",
        file_ref="/tmp/test-meeting-notes-case.md",
        org_id=org.id,
    )

    todo = Todo(
        title="From meeting caps",
        status="Open",
        source_type="Meeting",
        source_id=meeting.id,
    )
    db_session.add(todo)
    await db_session.commit()
    await db_session.refresh(todo)

    todos, total = await crud.get_todos_by_organization(
        db=db_session, organization_id=org.id, skip=0, limit=50
    )

    assert any(t.id == todo.id for t in todos)
