"""Verify todo project_id / organization_id persist via CRUD (no HTTP client fixture)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.todo import TodoCreate, TodoUpdate
from app.db import crud
from app.db.models import Organization, Project, Todo


@pytest.mark.asyncio
async def test_update_todo_persists_project_and_organization_ids(db_session: AsyncSession):
    org1 = Organization(name="OrgOnePersist")
    org2 = Organization(name="OrgTwoPersist")
    db_session.add_all([org1, org2])
    await db_session.commit()
    await db_session.refresh(org1)
    await db_session.refresh(org2)

    proj = Project(name="ProjPersist", organization_id=org1.id, status="Active")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    created = await crud.create_todo(
        db_session,
        TodoCreate(title="Task persist FK", status="Open"),
    )
    assert created.project_id is None
    assert created.organization_id is None

    updated = await crud.update_todo(
        db_session,
        created.id,
        TodoUpdate(project_id=proj.id, organization_id=org2.id),
    )
    assert updated is not None
    assert updated.project_id == proj.id
    assert updated.organization_id == org2.id

    result = await db_session.execute(select(Todo).where(Todo.id == created.id))
    loaded = result.scalar_one()
    assert loaded.project_id == proj.id
    assert loaded.organization_id == org2.id
