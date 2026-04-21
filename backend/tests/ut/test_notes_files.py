"""Unit tests for notes-files upload and serve API."""

import io
import shutil
import pytest
import pytest_asyncio
import tempfile
from pathlib import Path

from httpx import AsyncClient

import app.api.notes_files as notes_files_module


@pytest_asyncio.fixture
def tmp_notes_root(monkeypatch):
    """Patch notes_root to a temp dir; reset service singleton."""
    tmp = Path(tempfile.mkdtemp(prefix="notes_files_test_"))
    notes_root = tmp / "docs" / "meetings"
    notes_root.mkdir(parents=True)
    stub = type("Stub", (), {"notes_root": str(notes_root)})()
    monkeypatch.setattr("app.core.config.get_settings", lambda: stub)
    notes_files_module._notes_images_service = None
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)
    notes_files_module._notes_images_service = None


@pytest.mark.asyncio
async def test_upload_organization_image(client: AsyncClient, tmp_notes_root):
    """Upload with organization context returns path and context_base."""
    create_resp = await client.post(
        "/api/organizations/",
        json={"name": "Test Org"},
    )
    assert create_resp.status_code == 201
    org_id = create_resp.json()["id"]
    files = {"file": ("pic.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    data = {"context_type": "organization", "organization_id": org_id}
    response = await client.post(
        "/api/notes-files/upload",
        data=data,
        files=files,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "./images/pic.png"
    assert body["context_base"] == "test-org"


@pytest.mark.asyncio
async def test_upload_meeting_image(client: AsyncClient, db_session, tmp_notes_root):
    """Upload with meeting context and file_ref returns path and context_base."""
    files = {"file": ("img.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    data = {"context_type": "meeting", "file_ref": "acme/proj/2026-01-10-mtg.md"}
    response = await client.post(
        "/api/notes-files/upload",
        data=data,
        files=files,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "./images/img.png"
    assert "meetings" in body["context_base"] and "acme" in body["context_base"]


@pytest.mark.asyncio
async def test_upload_rejects_invalid_context(client: AsyncClient):
    """Upload without required context returns 400."""
    files = {"file": ("x.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    response = await client.post(
        "/api/notes-files/upload",
        data={"context_type": "meeting"},
        files=files,
    )
    assert response.status_code == 400
    response2 = await client.post(
        "/api/notes-files/upload",
        data={"context_type": "organization"},
        files=files,
    )
    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_serve_note_file(client: AsyncClient, tmp_notes_root):
    """After uploading, GET serve returns the file."""
    create_resp = await client.post("/api/organizations/", json={"name": "ServeTest"})
    assert create_resp.status_code == 201
    org_id = create_resp.json()["id"]
    files = {"file": ("serve.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    data = {"context_type": "organization", "organization_id": org_id}
    up = await client.post("/api/notes-files/upload", data=data, files=files)
    assert up.status_code == 200
    context_base = up.json()["context_base"]
    get_path = f"{context_base}/images/serve.png"
    resp = await client.get(f"/api/notes-files/{get_path}")
    assert resp.status_code == 200
    assert resp.content == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_serve_blocks_path_traversal(client: AsyncClient):
    """Serve rejects path traversal."""
    resp = await client.get("/api/notes-files/../etc/passwd")
    assert resp.status_code == 404
