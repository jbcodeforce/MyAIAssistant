"""Unit tests for knowledge command (process, stats) and KnowledgeProcessor."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from ai_assist_cli.cli import app
from ai_assist_cli.services.knowledge_processor import (
    KnowledgeDocumentSpec,
    KnowledgeProcessor,
    ProcessingAction,
    ProcessingResult,
    ProcessingSummary,
)

runner = CliRunner()


# --- load_specs ---


def test_load_specs_file_not_found(tmp_path):
    """load_specs with missing file raises FileNotFoundError with path."""
    path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError) as exc_info:
        KnowledgeProcessor.load_specs(path)
    assert str(path) in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower() or "File not found" in str(exc_info.value)


def test_load_specs_invalid_json(tmp_path):
    """load_specs with invalid JSON raises JSONDecodeError."""
    path = tmp_path / "bad.json"
    path.write_text("{ invalid }", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        KnowledgeProcessor.load_specs(path)


def test_load_specs_not_a_list(tmp_path):
    """load_specs with JSON that is not a list raises ValueError."""
    path = tmp_path / "obj.json"
    path.write_text('{"document_type": "folder", "uri": "/x", "collection": "c"}', encoding="utf-8")
    with pytest.raises(ValueError) as exc_info:
        KnowledgeProcessor.load_specs(path)
    assert "list" in str(exc_info.value).lower()


def test_load_specs_invalid_schema(tmp_path):
    """load_specs with item missing required field raises ValidationError."""
    path = tmp_path / "specs.json"
    path.write_text('[{"uri": "/x", "collection": "c"}]', encoding="utf-8")
    with pytest.raises(ValidationError):
        KnowledgeProcessor.load_specs(path)


def test_load_specs_valid(tmp_path):
    """load_specs with valid JSON returns list of KnowledgeDocumentSpec."""
    path = tmp_path / "specs.json"
    path.write_text(
        '[{"document_type": "folder", "uri": "/tmp/docs", "collection": "test"}]',
        encoding="utf-8",
    )
    specs = KnowledgeProcessor.load_specs(path)
    assert len(specs) == 1
    assert specs[0].document_type == "folder"
    assert specs[0].uri == "/tmp/docs"
    assert specs[0].collection == "test"


# --- process_spec: HTTP and connection errors ---


@pytest.mark.asyncio
async def test_process_spec_http_status_error_clear_message():
    """process_spec on HTTP 500 sets result.error with status and result.error_detail with body."""
    spec = KnowledgeDocumentSpec(
        document_type="folder",
        uri="/tmp/docs",
        collection="test",
    )
    processor = KnowledgeProcessor(backend_url="http://localhost:9999/api")
    response = httpx.Response(500, text='{"detail": "Internal server error"}')
    processor.client.get_knowledge_by_uri = AsyncMock(side_effect=httpx.HTTPStatusError("500", request=httpx.Request("GET", "http://x"), response=response))

    result = await processor.process_spec(spec)

    assert result.success is False
    assert result.action == ProcessingAction.FAILED
    assert "HTTP" in result.error
    assert "500" in result.error
    assert result.error_detail is not None
    assert "Internal" in result.error_detail or "500" in result.error_detail


@pytest.mark.asyncio
async def test_process_spec_request_error_clear_message():
    """process_spec on connection error sets result.error with 'Connection error'."""
    spec = KnowledgeDocumentSpec(
        document_type="folder",
        uri="/tmp/docs",
        collection="test",
    )
    processor = KnowledgeProcessor(backend_url="http://localhost:9999/api")
    processor.client.get_knowledge_by_uri = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    result = await processor.process_spec(spec)

    assert result.success is False
    assert result.action == ProcessingAction.FAILED
    assert "Connection" in result.error
    assert result.error_detail is not None
    assert "refused" in result.error_detail.lower() or "Connection" in result.error_detail


@pytest.mark.asyncio
async def test_process_spec_generic_exception_has_detail():
    """process_spec on generic exception sets result.error and result.error_detail (traceback)."""
    spec = KnowledgeDocumentSpec(
        document_type="folder",
        uri="/tmp/docs",
        collection="test",
    )
    processor = KnowledgeProcessor(backend_url="http://localhost:9999/api")
    processor.client.get_knowledge_by_uri = AsyncMock(side_effect=RuntimeError("something broke"))

    result = await processor.process_spec(spec)

    assert result.success is False
    assert result.action == ProcessingAction.FAILED
    assert "something broke" in result.error
    assert result.error_detail is not None
    assert "Traceback" in result.error_detail or "RuntimeError" in result.error_detail


# --- CLI process ---


def test_knowledge_process_dry_run_valid_file(tmp_path):
    """process with --dry-run and valid JSON exits 0 and shows table."""
    path = tmp_path / "specs.json"
    path.write_text(
        '[{"document_type": "folder", "uri": "/tmp/docs", "collection": "test"}]',
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["knowledge", "process", str(path), "--dry-run"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "document specification" in result.output.lower() or "Documents to Process" in result.output
    assert "folder" in result.output


def test_knowledge_process_missing_file_exits_nonzero():
    """process with missing JSON file exits nonzero (Typer 2 for validation or 1 if load_specs raises)."""
    result = runner.invoke(
        app,
        ["knowledge", "process", "/nonexistent/specs.json"],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Error" in result.output or "error" in result.output or "not found" in result.output.lower() or "Invalid" in result.output


def test_knowledge_process_invalid_json_exits_1(tmp_path):
    """process with invalid JSON exits 1 with validation/error message."""
    path = tmp_path / "bad.json"
    path.write_text("not json", encoding="utf-8")
    result = runner.invoke(
        app,
        ["knowledge", "process", str(path)],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "Error" in result.output or "error" in result.output or "JSON" in result.output or "Validation" in result.output


def test_knowledge_process_failed_results_show_error(tmp_path):
    """process when backend fails shows FAIL and error in table; verbose shows detail."""
    path = tmp_path / "specs.json"
    path.write_text(
        '[{"document_type": "folder", "uri": "/tmp/docs", "collection": "test"}]',
        encoding="utf-8",
    )
    failed_result = ProcessingResult(
        spec=KnowledgeDocumentSpec(document_type="folder", uri="/tmp/docs", collection="test"),
        success=False,
        error="Connection error: ConnectError",
        error_detail="Connection refused",
        action=ProcessingAction.FAILED,
    )
    summary = ProcessingSummary(
        total=1,
        successful=0,
        failed=1,
        skipped=0,
        created=0,
        updated=0,
        results=[failed_result],
    )

    with patch("ai_assist_cli.commands.knowledge.KnowledgeProcessor") as mock_processor_cls:
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_all = AsyncMock(return_value=summary)
        result = runner.invoke(
            app,
            ["knowledge", "process", str(path), "--verbose"],
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "FAIL" in result.output
    assert "Connection" in result.output or "Error" in result.output
    assert "Details" in result.output or "Connection refused" in result.output


def test_knowledge_process_unexpected_exception_shows_traceback(tmp_path):
    """process when an unexpected exception is raised shows traceback in output."""
    path = tmp_path / "specs.json"
    path.write_text(
        '[{"document_type": "folder", "uri": "/tmp/docs", "collection": "test"}]',
        encoding="utf-8",
    )

    with patch("ai_assist_cli.commands.knowledge.KnowledgeProcessor") as mock_processor_cls:
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_all = AsyncMock(side_effect=RuntimeError("backend exploded"))
        result = runner.invoke(
            app,
            ["knowledge", "process", str(path)],
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "Unexpected error" in result.output or "backend exploded" in result.output
    assert "Traceback" in result.output
    assert "RuntimeError" in result.output
