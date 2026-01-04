"""Workspace management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ai_assist_cli.services.workspace import WorkspaceManager

app = typer.Typer(help="Workspace management commands.")
console = Console()


@app.command("status")
def status(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to workspace. Defaults to current directory.",
    ),
):
    """Show workspace status and configuration summary."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        console.print("Run [cyan]ai_assist init[/cyan] to create a workspace.")
        raise typer.Exit(1)
    
    config = manager.load_config()
    
    console.print(f"\n[bold blue]Workspace Status[/bold blue]")
    console.print(f"[dim]Location: {workspace_path}[/dim]\n")
    
    # Configuration table
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Name", config.get("name", "N/A"))
    table.add_row("LLM Provider", config.get("llm_provider", "Not configured"))
    table.add_row("LLM Model", config.get("llm_model", "Not configured"))
    table.add_row("ChromaDB Path", str(config.get("chroma_persist_directory", "data/chroma")))
    table.add_row("Database Path", str(config.get("database_path", "data/db/assistant.db")))
    
    console.print(table)
    console.print()
    
    # Directory status
    dirs_table = Table(title="Directories")
    dirs_table.add_column("Directory", style="cyan")
    dirs_table.add_column("Status", style="green")
    dirs_table.add_column("Items", justify="right")
    
    for dir_name in ["data/chroma", "data/db", "prompts", "tools", "history", "summaries", "notes"]:
        dir_path = workspace_path / dir_name
        exists = dir_path.exists()
        item_count = len(list(dir_path.iterdir())) if exists else 0
        dirs_table.add_row(
            dir_name,
            "[green]OK[/green]" if exists else "[red]Missing[/red]",
            str(item_count),
        )
    
    console.print(dirs_table)


@app.command("clean")
def clean(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to workspace. Defaults to current directory.",
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt.",
    ),
):
    """Clean workspace data (history, summaries, cache)."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)
    
    if not confirm:
        confirm = typer.confirm(
            "This will delete history, summaries, and cache. Continue?"
        )
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Abort()
    
    cleaned = manager.clean()
    
    console.print(f"[green]Cleaned {cleaned} items from workspace.[/green]")


@app.command("list")
def list_workspaces():
    """List all known workspaces."""
    workspaces = WorkspaceManager.list_known_workspaces()
    
    if not workspaces:
        console.print("[yellow]No workspaces registered.[/yellow]")
        console.print("Run [cyan]ai_assist init[/cyan] to create a workspace.")
        return
    
    table = Table(title="Known Workspaces")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Status", style="green")
    
    for ws in workspaces:
        table.add_row(
            ws["name"],
            ws["path"],
            "[green]OK[/green]" if ws["valid"] else "[red]Invalid[/red]",
        )
    
    console.print(table)

