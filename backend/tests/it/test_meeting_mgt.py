"""Unit tests for meeting_ref CRUD operations."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import meeting as crud
from app.db.models import Meeting, Project, Organization
from app.services.meeting_notes import MeetingNotesService
from app.api.schemas.meeting_ref import MeetingRefCreate


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
            meeting_ref_create = MeetingRefCreate(
                meeting_id="mtg-real-scenario",
                project_id=project.id,
                org_id=organization.id,
                attendees=None,
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
        
            assert extracted_info.attendees is None
            assert extracted_info.created_at is not None
            assert extracted_info.updated_at is not None
        except FileNotFoundError:
            file_content = ""
            assert False

       

       