import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.db.crud import organization as org_crud
from app.db.errors import DuplicateOrganizationError


@pytest.mark.asyncio
async def test_create_organization_rejects_duplicate_name_case_insensitive(db_session: AsyncSession):
    await org_crud.create_organization(
        db_session, OrganizationCreate(name="ResMed")
    )
    with pytest.raises(DuplicateOrganizationError, match="resmed"):
        await org_crud.create_organization(
            db_session, OrganizationCreate(name="resmed")
        )


@pytest.mark.asyncio
async def test_update_organization_rejects_rename_to_existing_name(db_session: AsyncSession):
    await org_crud.create_organization(
        db_session, OrganizationCreate(name="Alpha Corp")
    )
    beta = await org_crud.create_organization(
        db_session, OrganizationCreate(name="Beta Corp")
    )
    with pytest.raises(DuplicateOrganizationError, match="alpha corp"):
        await org_crud.update_organization(
            db_session,
            beta.id,
            OrganizationUpdate(name="alpha corp"),
        )


@pytest.mark.asyncio
async def test_find_organization_by_name_is_case_insensitive(db_session: AsyncSession):
    created = await org_crud.create_organization(
        db_session, OrganizationCreate(name="Case Org")
    )
    found = await org_crud.find_organization_by_name(db_session, "case org")
    assert found is not None
    assert found.id == created.id
