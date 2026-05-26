"""CLI tests for org report (dry-run, missing workspace)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_assist_cli.cli import app

runner = CliRunner()


@pytest.fixture
def initialized_workspace(tmp_path: Path) -> Path:
    marker = tmp_path / ".ai_assist_workspace"
    marker.write_text('{"name": "test-ws"}', encoding="utf-8")
    (tmp_path / "notes").mkdir(parents=True)
    (tmp_path / "data").mkdir(parents=True)
    return tmp_path


def test_org_report_dry_run(initialized_workspace: Path) -> None:
    result = runner.invoke(
        app,
        [
            "org",
            "report",
            str(initialized_workspace),
            "--dry-run",
            "--skip-db",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Dry run OK" in result.output
    assert "notes" in result.output


def test_org_report_no_workspace(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["org", "report", str(tmp_path)],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "No workspace found" in result.output
