"""Configuration management commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from ai_assist_cli.services.workspace import WorkspaceManager

app = typer.Typer(help="Configuration management commands.")
console = Console()


@app.command("show")
def show(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to workspace. Defaults to current directory.",
    ),
):
    """Display current workspace configuration."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)
    
    config_file = workspace_path / "config.yaml"
    if config_file.exists():
        content = config_file.read_text()
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        console.print("[red]Configuration file not found.[/red]")


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Configuration key (e.g., llm_provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to workspace. Defaults to current directory.",
    ),
):
    """Set a configuration value."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)
    
    manager.set_config(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@app.command("get")
def get_value(
    key: str = typer.Argument(..., help="Configuration key to retrieve"),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to workspace. Defaults to current directory.",
    ),
):
    """Get a configuration value."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)
    
    config = manager.load_config()
    value = config.get(key)
    
    if value is None:
        console.print(f"[yellow]Key '{key}' not found in configuration.[/yellow]")
    else:
        console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")


@app.command("edit")
def edit(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to workspace. Defaults to current directory.",
    ),
):
    """Open configuration file in default editor."""
    workspace_path = (path or Path.cwd()).resolve()
    manager = WorkspaceManager(workspace_path)
    
    if not manager.is_initialized():
        console.print(f"[red]No workspace found at {workspace_path}[/red]")
        raise typer.Exit(1)
    
    config_file = workspace_path / "config.yaml"
    typer.launch(str(config_file))

