"""Customer note commands: parse markdown and create org/project/persons/meetings."""

import asyncio
import re
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.base_agent import AgentInput

from ai_assist_cli.services.api_client import BackendClient

app = typer.Typer(help="Customer note commands.")
console = Console()


def _run_async(coro):
    """Run an async coroutine in a new event loop."""
    return asyncio.run(coro)


def _slug(text: str) -> str:
    """Convert text to a URL-safe slug (lowercase, spaces and non-alphanumeric to hyphens)."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-") or "note"


async def _parse_note(content: str):
    """Run NoteParserAgent on markdown content; return NoteParserResponse."""
    factory = AgentFactory(config_dir=None)
    agent = factory.create_agent("NoteParserAgent")
    response = await agent.execute(AgentInput(query=content))
    return response


def _show_dry_run(response):
    """Display extracted organization, persons, project, meetings (no API calls)."""
    table = Table(title="Extracted Data (Dry Run)")
    table.add_column("Type", style="cyan")
    table.add_column("Details", style="green")

    if response.organization:
        table.add_row(
            "Organization",
            f"{response.organization.name}\n{response.organization.description or ''}",
        )
    if response.persons:
        rows = [f"{p.name}" + (f" — {p.role or p.context or ''}" if (p.role or p.context) else "") for p in response.persons]
        table.add_row("Persons", "\n".join(rows))
    if response.project:
        proj = response.project
        table.add_row(
            "Project",
            f"{proj.name or '(from org)'}\n{proj.description or ''}\n"
            f"Past steps: {len(proj.past_steps)}, Next steps: {len(proj.next_steps)}",
        )
    if response.meetings:
        table.add_row("Meetings", "\n".join(m.title for m in response.meetings))

    console.print(table)
    if response.parse_error:
        console.print(f"[yellow]Parse warning: {response.parse_error}[/yellow]")


async def _create_entities(response, backend_url: Optional[str], verbose: bool):
    """Create organization, project, persons, meeting refs via backend API."""
    client = BackendClient(base_url=backend_url)
    org_name = response.organization.name if response.organization else "Unknown"
    org_id = None
    project_id = None

    if response.organization:
        org = response.organization
        created = await client.create_organization(
            name=org.name,
            description=org.description,
        )
        org_id = created.id
        if verbose:
            console.print(f"[green]Created organization: {created.name} (id={org_id})[/green]")

    if response.project and org_id is not None:
        proj = response.project
        project_name = proj.name or f"{org_name} engagement"
        past = [{"what": s.what, "who": s.who} for s in proj.past_steps]
        next_s = [{"what": s.what, "who": s.who} for s in proj.next_steps]
        created = await client.create_project(
            name=project_name,
            organization_id=org_id,
            description=proj.description,
            status="Draft",
            past_steps=past if past else None,
            next_steps=next_s if next_s else None,
        )
        project_id = created.id
        if verbose:
            console.print(f"[green]Created project: {created.name} (id={project_id})[/green]")

    persons_created = 0
    if response.persons and org_id is not None:
        for p in response.persons:
            await client.create_person(
                name=p.name,
                organization_id=org_id,
                project_id=project_id,
                role=p.role,
                context=p.context,
            )
            persons_created += 1
        if verbose:
            console.print(f"[green]Created {persons_created} person(s)[/green]")

    meetings_created = 0
    if response.meetings and org_id is not None and project_id is not None:
        org_slug = _slug(org_name)
        for m in response.meetings:
            meeting_id = f"{org_slug}-{_slug(m.title)}"
            await client.create_meeting_ref(
                meeting_id=meeting_id,
                content=m.content,
                org_id=org_id,
                project_id=project_id,
            )
            meetings_created += 1
        if verbose:
            console.print(f"[green]Created {meetings_created} meeting ref(s)[/green]")

    return org_id, project_id, persons_created, meetings_created


@app.command("parse")
def parse_note(
    file_path: Path = typer.Argument(
        ...,
        help="Path to customer note markdown file (e.g. index.md).",
        exists=True,
        readable=True,
    ),
    backend_url: Optional[str] = typer.Option(
        None,
        "--backend-url",
        "-b",
        help="Backend API URL. Defaults to AI_ASSIST_BACKEND_URL or http://localhost:8000/api",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Only parse and show extracted data; do not call the backend.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
):
    """Parse a customer note markdown file and create organization, project, persons, and meeting refs.

    The file should follow a structure like: H1 = org name, ## Team / ## <Org> = people,
    ## Products/Context/Technology stack = context, ## Past steps/Next steps = steps,
    ## Discovery call/Questions = meeting sections. Uses an LLM to extract structured
    data and optionally creates entities via the backend API.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    if not content.strip():
        console.print("[yellow]File is empty.[/yellow]")
        raise typer.Exit(0)

    console.print("[dim]Parsing note with NoteParserAgent...[/dim]")
    response = _run_async(_parse_note(content))

    if response.parse_error and not response.organization and not response.persons:
        console.print(f"[red]Parse failed: {response.parse_error}[/red]")
        raise typer.Exit(1)

    if dry_run:
        _show_dry_run(response)
        return

    # Check backend reachability
    client = BackendClient(base_url=backend_url)
    if not _run_async(client.health_check()):
        console.print("[red]Backend is not reachable. Start the backend or set --backend-url.[/red]")
        raise typer.Exit(1)

    org_id, project_id, persons_created, meetings_created = _run_async(
        _create_entities(response, backend_url, verbose)
    )

    lines = [
        f"Organization: id={org_id}",
        f"Project: id={project_id}",
        f"Persons created: {persons_created}",
        f"Meeting refs created: {meetings_created}",
    ]
    console.print(Panel("\n".join(lines), title="[green]Summary[/green]", border_style="green"))