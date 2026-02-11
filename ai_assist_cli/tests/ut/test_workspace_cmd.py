"""Unit tests for workspace command (status, clean, list)."""

import pytest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_assist_cli.cli import app

runner = CliRunner()


@pytest.fixture
def uninitialized_workspace(tmp_path):
    """Directory with no workspace marker."""
    return tmp_path


@pytest.fixture
def initialized_workspace(tmp_path):
    """Directory with workspace marker and expected subdirs so status can run."""
    marker = tmp_path / ".ai_assist_workspace"
    marker.write_text('{"name": "test-ws"}', encoding="utf-8")
    for dir_name in ["data/chroma", "data/db", "prompts", "tools", "history", "summaries", "notes"]:
        (tmp_path / dir_name).mkdir(parents=True)
    return tmp_path


def test_workspace_status_uninitialized(uninitialized_workspace):
    """status with no workspace marker exits 1 and prints error."""
    result = runner.invoke(
        app,
        ["workspace", "status", str(uninitialized_workspace)],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "No workspace found" in result.output
    assert "ai_assist init" in result.output


def test_workspace_status_initialized(initialized_workspace):
    """status with workspace marker exits 0 and shows name and directories."""
    result = runner.invoke(
        app,
        ["workspace", "status", str(initialized_workspace)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Workspace Status" in result.output
    assert "test-ws" in result.output
    assert "Directories" in result.output


def test_workspace_status_defaults_to_cwd(initialized_workspace):
    """status with no path uses cwd; when cwd is initialized, exits 0."""
    with patch("ai_assist_cli.commands.workspace.Path.cwd", return_value=initialized_workspace):
        result = runner.invoke(
            app,
            ["workspace", "status"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "test-ws" in result.output


def test_workspace_clean_uninitialized(uninitialized_workspace):
    """clean with no workspace marker exits 1."""
    result = runner.invoke(
        app,
        ["workspace", "clean", str(uninitialized_workspace), "--yes"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "No workspace found" in result.output


def test_workspace_clean_yes_initialized(initialized_workspace):
    """clean with --yes on initialized workspace exits 0 and reports cleaned count."""
    result = runner.invoke(
        app,
        ["workspace", "clean", str(initialized_workspace), "--yes"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Cleaned" in result.output


def test_workspace_clean_without_yes_abort(initialized_workspace):
    """clean without --yes and user declines exits with abort."""
    with patch("ai_assist_cli.commands.workspace.typer.confirm", return_value=False):
        result = runner.invoke(
            app,
            ["workspace", "clean", str(initialized_workspace)],
            catch_exceptions=True,
        )
    assert result.exit_code != 0
    assert "Cancelled" in result.output


def test_workspace_clean_without_yes_confirm(initialized_workspace):
    """clean without --yes and user confirms exits 0."""
    with patch("ai_assist_cli.commands.workspace.typer.confirm", return_value=True):
        result = runner.invoke(
            app,
            ["workspace", "clean", str(initialized_workspace)],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "Cleaned" in result.output


def test_workspace_list_empty():
    """list with no registered workspaces prints message."""
    with patch(
        "ai_assist_cli.commands.workspace.WorkspaceManager.list_known_workspaces",
        return_value=[],
    ):
        result = runner.invoke(
            app,
            ["workspace", "list"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "No workspaces registered" in result.output
    assert "ai_assist init" in result.output


def test_workspace_list_with_workspaces():
    """list with registered workspaces prints table with name and path."""
    workspaces = [
        {"name": "ws-a", "path": "/path/a", "valid": True},
        {"name": "ws-b", "path": "/path/b", "valid": False},
    ]
    with patch(
        "ai_assist_cli.commands.workspace.WorkspaceManager.list_known_workspaces",
        return_value=workspaces,
    ):
        result = runner.invoke(
            app,
            ["workspace", "list"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "Known Workspaces" in result.output
    assert "ws-a" in result.output
    assert "ws-b" in result.output
    assert "/path/a" in result.output
    assert "/path/b" in result.output
    assert "OK" in result.output
    assert "Invalid" in result.output
