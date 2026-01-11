"""Unit tests for meeting_ref CRUD operations."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import meeting as crud
from app.db.models import MeetingRef, Project, Organization
from app.services.meeting_notes import MeetingNotesService
from app.api.schemas.meeting_ref import MeetingRefCreate


@pytest_asyncio.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a test project."""
    project = Project(name="Test Project", description="Test project description")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(name="Test Organization")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def notes_service() -> MeetingNotesService:
    """Create a test notes service."""
    return MeetingNotesService()

class TestCreateMeetingRef:
    """Tests for create_meeting_ref function."""
    
    @pytest.mark.asyncio
    async def test_create_meeting_ref_minimal(self, db_session: AsyncSession):
        """Test creating a meeting ref with only required fields."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-2026-01-10-test",
            file_ref="docs/meetings/mtg-2026-01-10-test.md",
        )
        
        assert meeting_ref.id is not None
        assert meeting_ref.meeting_id == "mtg-2026-01-10-test"
        assert meeting_ref.file_ref == "docs/meetings/mtg-2026-01-10-test.md"
        assert meeting_ref.project_id is None
        assert meeting_ref.org_id is None
        assert meeting_ref.presents is None
        assert meeting_ref.created_at is not None
        assert meeting_ref.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_meeting_ref_with_project(
        self, db_session: AsyncSession, project: Project
    ):
        """Test creating a meeting ref linked to a project."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-project",
            file_ref="docs/meetings/mtg-project.md",
            project_id=project.id,
        )
        
        assert meeting_ref.project_id == project.id
    
    @pytest.mark.asyncio
    async def test_create_meeting_ref_with_organization(
        self, db_session: AsyncSession, organization: Organization
    ):
        """Test creating a meeting ref linked to an organization."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-org",
            file_ref="docs/meetings/mtg-org.md",
            org_id=organization.id,
        )
        
        assert meeting_ref.org_id == organization.id
    
    @pytest.mark.asyncio
    async def test_create_meeting_ref_with_presents(self, db_session: AsyncSession):
        """Test creating a meeting ref with attendees."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-presents",
            file_ref="docs/meetings/mtg-presents.md",
            presents="John Doe, Jane Smith, Bob Wilson",
        )
        
        assert meeting_ref.presents == "John Doe, Jane Smith, Bob Wilson"
    
    @pytest.mark.asyncio
    async def test_create_meeting_ref_full(
        self, db_session: AsyncSession, project: Project, organization: Organization
    ):
        """Test creating a meeting ref with all fields."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-full",
            file_ref="docs/meetings/org/project/mtg-full.md",
            project_id=project.id,
            org_id=organization.id,
            presents="Alice; Bob; Carol",
        )
        
        assert meeting_ref.meeting_id == "mtg-full"
        assert meeting_ref.file_ref == "docs/meetings/org/project/mtg-full.md"
        assert meeting_ref.project_id == project.id
        assert meeting_ref.org_id == organization.id
        assert meeting_ref.presents == "Alice; Bob; Carol"


class TestGetMeetingRef:
    """Tests for get_meeting_ref function."""
    
    @pytest.mark.asyncio
    async def test_get_meeting_ref_exists(self, db_session: AsyncSession):
        """Test getting an existing meeting ref by ID."""
        created = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-get-test",
            file_ref="docs/meetings/mtg-get-test.md",
        )
        
        retrieved = await crud.get_meeting_ref(db=db_session, meeting_ref_id=created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.meeting_id == "mtg-get-test"
    
    @pytest.mark.asyncio
    async def test_get_meeting_ref_not_found(self, db_session: AsyncSession):
        """Test getting a non-existent meeting ref."""
        retrieved = await crud.get_meeting_ref(db=db_session, meeting_ref_id=9999)
        
        assert retrieved is None


class TestGetMeetingRefByMeetingId:
    """Tests for get_meeting_ref_by_meeting_id function."""
    
    @pytest.mark.asyncio
    async def test_get_by_meeting_id_exists(self, db_session: AsyncSession):
        """Test getting a meeting ref by meeting_id."""
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-unique-id",
            file_ref="docs/meetings/mtg-unique-id.md",
        )
        
        retrieved = await crud.get_meeting_ref_by_meeting_id(
            db=db_session, meeting_id="mtg-unique-id"
        )
        
        assert retrieved is not None
        assert retrieved.meeting_id == "mtg-unique-id"
    
    @pytest.mark.asyncio
    async def test_get_by_meeting_id_not_found(self, db_session: AsyncSession):
        """Test getting a meeting ref with non-existent meeting_id."""
        retrieved = await crud.get_meeting_ref_by_meeting_id(
            db=db_session, meeting_id="non-existent-id"
        )
        
        assert retrieved is None


class TestGetMeetingRefs:
    """Tests for get_meeting_refs function."""
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_empty(self, db_session: AsyncSession):
        """Test getting meeting refs when none exist."""
        refs, total = await crud.get_meeting_refs(db=db_session)
        
        assert refs == []
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_multiple(self, db_session: AsyncSession):
        """Test getting multiple meeting refs."""
        for i in range(3):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-list-{i}",
                file_ref=f"docs/meetings/mtg-list-{i}.md",
            )
        
        refs, total = await crud.get_meeting_refs(db=db_session)
        
        assert len(refs) == 3
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_pagination(self, db_session: AsyncSession):
        """Test pagination of meeting refs."""
        for i in range(5):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-page-{i}",
                file_ref=f"docs/meetings/mtg-page-{i}.md",
            )
        
        refs, total = await crud.get_meeting_refs(db=db_session, skip=2, limit=2)
        
        assert len(refs) == 2
        assert total == 5
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_filter_by_project(
        self, db_session: AsyncSession, project: Project
    ):
        """Test filtering meeting refs by project."""
        # Create 2 with project, 1 without
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-with-project-1",
            file_ref="docs/mtg-with-project-1.md",
            project_id=project.id,
        )
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-with-project-2",
            file_ref="docs/mtg-with-project-2.md",
            project_id=project.id,
        )
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-without-project",
            file_ref="docs/mtg-without-project.md",
        )
        
        refs, total = await crud.get_meeting_refs(db=db_session, project_id=project.id)
        
        assert len(refs) == 2
        assert total == 2
        for ref in refs:
            assert ref.project_id == project.id
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_filter_by_organization(
        self, db_session: AsyncSession, organization: Organization
    ):
        """Test filtering meeting refs by organization."""
        # Create 2 with org, 1 without
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-with-org-1",
            file_ref="docs/mtg-with-org-1.md",
            org_id=organization.id,
        )
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-with-org-2",
            file_ref="docs/mtg-with-org-2.md",
            org_id=organization.id,
        )
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-without-org",
            file_ref="docs/mtg-without-org.md",
        )
        
        refs, total = await crud.get_meeting_refs(db=db_session, org_id=organization.id)
        
        assert len(refs) == 2
        assert total == 2
        for ref in refs:
            assert ref.org_id == organization.id
    
    @pytest.mark.asyncio
    async def test_get_meeting_refs_ordered_by_created_desc(self, db_session: AsyncSession):
        """Test that meeting refs are ordered by created_at descending."""
        for i in range(3):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-order-{i}",
                file_ref=f"docs/mtg-order-{i}.md",
            )
        
        refs, _ = await crud.get_meeting_refs(db=db_session)
        
        # Most recent first (highest id = most recent in this test)
        for i in range(len(refs) - 1):
            assert refs[i].created_at >= refs[i + 1].created_at


class TestUpdateMeetingRef:
    """Tests for update_meeting_ref function."""
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_project(
        self, db_session: AsyncSession, project: Project
    ):
        """Test updating the project_id of a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-update-project",
            file_ref="docs/mtg-update-project.md",
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            project_id=project.id,
            update_project_id=True,
        )
        
        assert updated is not None
        assert updated.project_id == project.id
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_organization(
        self, db_session: AsyncSession, organization: Organization
    ):
        """Test updating the org_id of a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-update-org",
            file_ref="docs/mtg-update-org.md",
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            org_id=organization.id,
            update_org_id=True,
        )
        
        assert updated is not None
        assert updated.org_id == organization.id
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_presents(self, db_session: AsyncSession):
        """Test updating the presents field of a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-update-presents",
            file_ref="docs/mtg-update-presents.md",
            presents="Original Attendee",
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            presents="New Attendee 1, New Attendee 2",
            update_presents=True,
        )
        
        assert updated is not None
        assert updated.presents == "New Attendee 1, New Attendee 2"
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_clear_project(
        self, db_session: AsyncSession, project: Project
    ):
        """Test clearing the project_id of a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-clear-project",
            file_ref="docs/mtg-clear-project.md",
            project_id=project.id,
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            project_id=None,
            update_project_id=True,
        )
        
        assert updated is not None
        assert updated.project_id is None
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_clear_presents(self, db_session: AsyncSession):
        """Test clearing the presents field of a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-clear-presents",
            file_ref="docs/mtg-clear-presents.md",
            presents="Some Attendee",
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            presents=None,
            update_presents=True,
        )
        
        assert updated is not None
        assert updated.presents is None
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_no_change_without_flag(
        self, db_session: AsyncSession, project: Project
    ):
        """Test that fields are not updated without the update flag."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-no-change",
            file_ref="docs/mtg-no-change.md",
            presents="Original",
        )
        
        # Pass new values but don't set update flags
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            project_id=project.id,
            presents="New Value",
            update_project_id=False,
            update_presents=False,
        )
        
        assert updated is not None
        assert updated.project_id is None  # Not changed
        assert updated.presents == "Original"  # Not changed
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_not_found(self, db_session: AsyncSession):
        """Test updating a non-existent meeting ref."""
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=9999,
            presents="Test",
            update_presents=True,
        )
        
        assert updated is None
    
    @pytest.mark.asyncio
    async def test_update_meeting_ref_multiple_fields(
        self, db_session: AsyncSession, project: Project, organization: Organization
    ):
        """Test updating multiple fields at once."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-multi-update",
            file_ref="docs/mtg-multi-update.md",
        )
        
        updated = await crud.update_meeting_ref(
            db=db_session,
            meeting_ref_id=meeting_ref.id,
            project_id=project.id,
            org_id=organization.id,
            presents="Multiple, Updates",
            update_project_id=True,
            update_org_id=True,
            update_presents=True,
        )
        
        assert updated is not None
        assert updated.project_id == project.id
        assert updated.org_id == organization.id
        assert updated.presents == "Multiple, Updates"


class TestDeleteMeetingRef:
    """Tests for delete_meeting_ref function."""
    
    @pytest.mark.asyncio
    async def test_delete_meeting_ref_success(self, db_session: AsyncSession):
        """Test successfully deleting a meeting ref."""
        meeting_ref = await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-delete",
            file_ref="docs/mtg-delete.md",
        )
        
        result = await crud.delete_meeting_ref(db=db_session, meeting_ref_id=meeting_ref.id)
        
        assert result is True
        
        # Verify it's deleted
        retrieved = await crud.get_meeting_ref(db=db_session, meeting_ref_id=meeting_ref.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_delete_meeting_ref_not_found(self, db_session: AsyncSession):
        """Test deleting a non-existent meeting ref."""
        result = await crud.delete_meeting_ref(db=db_session, meeting_ref_id=9999)
        
        assert result is False


class TestGetMeetingRefsByProject:
    """Tests for get_meeting_refs_by_project function."""
    
    @pytest.mark.asyncio
    async def test_get_by_project(self, db_session: AsyncSession, project: Project):
        """Test getting meeting refs by project."""
        # Create meeting refs for the project
        for i in range(3):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-proj-{i}",
                file_ref=f"docs/mtg-proj-{i}.md",
                project_id=project.id,
            )
        # Create one without project
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-no-proj",
            file_ref="docs/mtg-no-proj.md",
        )
        
        refs, total = await crud.get_meeting_refs_by_project(
            db=db_session, project_id=project.id
        )
        
        assert len(refs) == 3
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_get_by_project_with_pagination(
        self, db_session: AsyncSession, project: Project
    ):
        """Test getting meeting refs by project with pagination."""
        for i in range(5):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-proj-page-{i}",
                file_ref=f"docs/mtg-proj-page-{i}.md",
                project_id=project.id,
            )
        
        refs, total = await crud.get_meeting_refs_by_project(
            db=db_session, project_id=project.id, skip=1, limit=2
        )
        
        assert len(refs) == 2
        assert total == 5


class TestGetMeetingRefsByOrganization:
    """Tests for get_meeting_refs_by_organization function."""
    
    @pytest.mark.asyncio
    async def test_get_by_organization(
        self, db_session: AsyncSession, organization: Organization
    ):
        """Test getting meeting refs by organization."""
        # Create meeting refs for the organization
        for i in range(3):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-org-{i}",
                file_ref=f"docs/mtg-org-{i}.md",
                org_id=organization.id,
            )
        # Create one without organization
        await crud.create_meeting_ref(
            db=db_session,
            meeting_id="mtg-no-org",
            file_ref="docs/mtg-no-org.md",
        )
        
        refs, total = await crud.get_meeting_refs_by_organization(
            db=db_session, org_id=organization.id
        )
        
        assert len(refs) == 3
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_get_by_organization_with_pagination(
        self, db_session: AsyncSession, organization: Organization
    ):
        """Test getting meeting refs by organization with pagination."""
        for i in range(5):
            await crud.create_meeting_ref(
                db=db_session,
                meeting_id=f"mtg-org-page-{i}",
                file_ref=f"docs/mtg-org-page-{i}.md",
                org_id=organization.id,
            )
        
        refs, total = await crud.get_meeting_refs_by_organization(
            db=db_session, org_id=organization.id, skip=1, limit=2
        )
        
        assert len(refs) == 2
        assert total == 5


class TestRealScenario:
    """Use TestProject and TestOrganization to create a real scenario."""
    
    @pytest.mark.asyncio
    async def test_real_scenario(
        self,
        db_session: AsyncSession,
        project: Project,
        organization: Organization,
        notes_service: MeetingNotesService,
    ):
        """Test a real scenario."""
        import aiofiles
        from app.api.meeting_refs import create_meeting_ref, extract_meeting_info
         # Read the content of the meeting ref file
        file_path = "data/docs/mtg-real-scenario.md"
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                file_content = await f.read()
        except FileNotFoundError:
            file_content = None

        meeting_ref_create = MeetingRefCreate(
            meeting_id="mtg-real-scenario",
            file_ref=file_path,
            project_id=project.id,
            org_id=organization.id,
            content=file_content,
        )
        meeting_ref = await create_meeting_ref(
            meeting_ref=meeting_ref_create,
            db=db_session,
            notes_service=notes_service,
        )
        print(meeting_ref)
        
    

        assert meeting_ref is not None
        assert meeting_ref.project_id == project.id
        assert meeting_ref.org_id == organization.id
        assert meeting_ref.meeting_id == "mtg-real-scenario"


        extracted_info = await extract_meeting_info(meeting_ref_id=meeting_ref.id, 
                                                    db=db_session,
                                                    notes_service=notes_service)
        print(extracted_info)
        assert extracted_info is not None
        assert extracted_info.project_id == project.id
        assert extracted_info.org_id == organization.id
        assert extracted_info.meeting_id == "mtg-real-scenario"
       
        assert extracted_info.presents is None
        assert extracted_info.created_at is not None
        assert extracted_info.updated_at is not None