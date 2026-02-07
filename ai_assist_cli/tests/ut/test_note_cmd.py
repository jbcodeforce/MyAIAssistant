"""Tests for note parse command."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_assist_cli.cli import app
data_dir = Path(__file__).parent.parent / "data"

runner = CliRunner()


def _make_mock_response():
    """Build a fixed IndexParserResponse without calling the LLM."""
    from agent_core.agents.note_parser_agent import (
        NoteParserResponse,
        OrganizationExtract,
        PersonExtract,
        ProjectExtract,
        MeetingExtract,
        StepExtract,
    )
    return NoteParserResponse(
        message="",
        organization=OrganizationExtract(name="Acme", description="A company."),
        persons=[PersonExtract(name="John", role="Engineer", context=None)],
        project=ProjectExtract(
            name="Acme engagement",
            description=None,
            past_steps=[],
            next_steps=[StepExtract(what="Follow up", who="John")],
        ),
        meetings=[MeetingExtract(title="Discovery", content="Notes from discovery.")],
        parse_error=None,
        agent_type="note_parser",
    )


@pytest.fixture
def sample_note_file(tmp_path):
    """A minimal customer note markdown file."""
    path = tmp_path / "index.md"
    path.write_text(
        "# Acme\n\n## Team\n* John: Engineer\n\n## Context\nA company.\n",
        encoding="utf-8",
    )
    return path


def test_note_parse_dry_run_shows_extracted_data(sample_note_file):
    """With --dry-run, parse runs without backend and shows extracted org, persons, project, meetings."""
    mock_response = _make_mock_response()

    async def mock_parse_note_async(content):
        return mock_response

    def mock_run_async(coro):
        if asyncio.iscoroutine(coro):
            return asyncio.run(coro)
        return coro

    with patch("ai_assist_cli.commands.note_cmd._parse_note", side_effect=mock_parse_note_async), patch(
        "ai_assist_cli.commands.note_cmd._run_async", side_effect=mock_run_async
    ):
        result = runner.invoke(
            app,
            ["note", "parse", str(sample_note_file), "--dry-run"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "Acme" in result.output
    assert "John" in result.output
    assert "Discovery" in result.output
    assert "Extracted Data" in result.output or "Dry Run" in result.output


def test_note_parse_empty_file_exits_zero(tmp_path):
    """Parse with an empty file exits 0 and prints a message."""
    empty = tmp_path / "empty.md"
    empty.write_text("", encoding="utf-8")
    with patch(
        "ai_assist_cli.commands.note_cmd._parse_note",
        side_effect=lambda content: _mock_parse_note(content),
    ):
        result = runner.invoke(
            app,
            ["note", "parse", str(empty), "--dry-run"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "empty" in result.output.lower()



def test_note_parse_notes_1():
    """Parse with a missing file path exits with code 1."""
    result = runner.invoke(
        app,
        ["note", "parse", str(data_dir / "notes_1.md"), "--dry-run"],
        catch_exceptions=False,
    )
    assert result.exit_code != 0