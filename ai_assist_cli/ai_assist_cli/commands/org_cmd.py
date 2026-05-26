"""Organization-wide challenges report via Agno agent."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from ai_assist_cli.agents.org_challenges_agent import (
    ChallengeReport,
    build_org_challenges_agent,
)
from ai_assist_cli.services.db_url import (
    database_file_exists,
    resolve_database_url_for_tools,
)
from ai_assist_cli.services.workspace import WorkspaceManager

app = typer.Typer(help="Organization-wide challenges and issues report.")
console = Console()


def _run_async(coro):
    return asyncio.run(coro)


def _extract_json_object(text: str) -> str | None:
    """Best-effort extract JSON object from model text."""
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


def _parse_challenge_report(raw: object) -> ChallengeReport:
    """Normalize agent output to ChallengeReport."""
    if isinstance(raw, ChallengeReport):
        return raw
    if isinstance(raw, dict):
        return ChallengeReport.model_validate(raw)
    if hasattr(raw, "model_dump") and callable(getattr(raw, "model_dump")):
        return ChallengeReport.model_validate(raw.model_dump())
    if isinstance(raw, str):
        try:
            return ChallengeReport.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError, ValueError):
            blob = _extract_json_object(raw)
            if blob:
                return ChallengeReport.model_validate_json(blob)
    raise ValueError(f"Unparseable agent output: {type(raw)!r}")


async def _run_report_async(
    workspace: Path,
    notes_root: Path,
    database_url: str | None,
    skip_db: bool,
) -> ChallengeReport:
    agent = build_org_challenges_agent(
        notes_root=notes_root,
        database_url=database_url,
        skip_db=skip_db,
    )
    run = await agent.arun(
        "Produce the consolidated ChallengeReport for this workspace. "
        "Use SQL tools and workspace markdown tools as needed. "
        "Return structured output only.",
    )
    content = run.content
    try:
        return _parse_challenge_report(content)
    except (ValidationError, ValueError, json.JSONDecodeError) as e:
        console.print(f"[yellow]Structured parse failed ({e}); retrying as text.[/yellow]")
        return _parse_challenge_report(str(content))


@app.command("report")
def report_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Workspace root. Defaults to current directory.",
    ),
    database_url: Optional[str] = typer.Option(
        None,
        "--database-url",
        help="Override database URL (sync SQLAlchemy URL or sqlite+aiosqlite—normalized).",
    ),
    notes_root: Optional[Path] = typer.Option(
        None,
        "--notes-root",
        help="Root folder for markdown notes (default: <workspace>/notes).",
    ),
    skip_db: bool = typer.Option(
        False,
        "--skip-db",
        help="Do not attach SQL tools; only scan markdown under notes root.",
    ),
    json_out: bool = typer.Option(
        False,
        "--json",
        help="Print JSON instead of a Rich table.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate paths and exit without calling the LLM.",
    ),
):
    """Summarize challenges, next steps, and issues per account from DB + notes."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)

    nroot = (notes_root if notes_root is not None else workspace_path / "notes").resolve()
    if not nroot.is_dir():
        console.print(f"[yellow]Notes root does not exist yet: {nroot} (creating may be optional)[/yellow]")

    resolved_db = resolve_database_url_for_tools(
        workspace_path,
        explicit_url=database_url,
        skip_db=skip_db,
    )

    if not skip_db and resolved_db and not database_file_exists(resolved_db):
        console.print(
            f"[red]Database file not found for URL.[/red]\n"
            f"  Resolved: {resolved_db}\n"
            f"  Use --skip-db to report from notes only, or create the DB / fix DATABASE_URL."
        )
        raise typer.Exit(1)

    if dry_run:
        console.print("[green]Dry run OK[/green]")
        console.print(f"  workspace: {workspace_path}")
        console.print(f"  notes_root: {nroot}")
        console.print(f"  database: {resolved_db if not skip_db else '(skipped)'}")
        return

    report = _run_async(_run_report_async(workspace_path, nroot, resolved_db, skip_db))

    if json_out:
        console.print_json(data=report.model_dump())
        return

    table = Table(title="Org challenges / next steps / issues")
    table.add_column("Account", style="cyan")
    table.add_column("Kind", style="magenta")
    table.add_column("Summary", style="white")
    table.add_column("Source", style="dim")

    for row in report.rows:
        table.add_row(row.account, row.kind, row.summary, row.source)

    console.print(table)
