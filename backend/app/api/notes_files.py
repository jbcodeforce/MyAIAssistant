"""API for uploading and serving note images (workspace-relative paths)."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.services.notes_images import (
    NotesImagesService,
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes-files", tags=["notes-files"])

_notes_images_service: Optional[NotesImagesService] = None


def get_notes_images_service() -> NotesImagesService:
    global _notes_images_service
    if _notes_images_service is None:
        _notes_images_service = NotesImagesService()
    return _notes_images_service


@router.post("/upload")
async def upload_note_image(
    file: UploadFile = File(...),
    context_type: str = Form(...),
    file_ref: Optional[str] = Form(None),
    organization_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image for use in note markdown. Stores under the workspace docs/ tree.
    context_type: "meeting" | "organization"
    - meeting: file_ref required (e.g. acme/meetings/proj/2026-01-10-mtg.md). Image saved next to that note.
    - organization: organization_id required. Image saved under docs/notes/{org}/notes/images/.
    Returns: { "path": "./images/filename", "context_base": "..." } to insert into markdown.
    """
    service = get_notes_images_service()

    if context_type == "meeting":
        if not file_ref or not file_ref.strip():
            raise HTTPException(status_code=400, detail="file_ref required for meeting context")
        if ".." in file_ref or file_ref.lstrip("/").startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file_ref")
        context_base_arg = file_ref.strip()
    elif context_type == "organization":
        if organization_id is None:
            raise HTTPException(status_code=400, detail="organization_id required for organization context")
        org = await crud.get_organization(db, organization_id=organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        context_base_arg = org.name
    else:
        raise HTTPException(
            status_code=400,
            detail="context_type must be 'meeting' or 'organization'",
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )
    body = await file.read()
    if len(body) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {MAX_FILE_SIZE_BYTES // (1024*1024)} MB)",
        )

    filename = file.filename or "image.png"
    if context_type == "meeting":
        result = service.save_meeting_image(context_base_arg, filename, body)
    else:
        result = service.save_organization_image(context_base_arg, filename, body)

    return {"path": result.path, "context_base": result.context_base}


@router.get("/{path:path}")
async def serve_note_file(path: str):
    """
    Serve a file from the notes/docs workspace by path relative to docs root.
    path is e.g. meetings/acme/proj/images/name.png or my-org/images/name.png.
    """
    service = get_notes_images_service()
    resolved = service.resolve_serve_path(path)
    if not resolved:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        resolved,
        media_type=None,
        filename=resolved.name,
        content_disposition_type="inline",
    )
