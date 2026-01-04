"""Init command - Initialize a new AI Assistant workspace."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from ai_assist_cli.services.workspace import WorkspaceManager

console = Console()


def init_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path where to create the workspace. Defaults to current directory.",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Workspace name. Defaults to directory name.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing workspace configuration.",
    ),
):
    """Initialize a new AI Assistant workspace.
    
    Creates:
    - ~/.ai_assist/: Global directory for cross-workspace resources
      - prompts/: Shared prompt templates
      - agents/: Agent definitions
      - tools/: Shared tool definitions
      - models/: Model configurations
      - cache/: Shared cache
    
    - <workspace>/: Local workspace directory
      - config.yaml: Workspace configuration
      - data/chroma/: Vector database
      - prompts/: Local prompt templates
      - tools/: Local tool definitions
      - history/: Chat history
      - summaries/: Conversation summaries
      - notes/: Documents for RAG
    """
    workspace_path = path or Path.cwd()
    workspace_path = workspace_path.resolve()
    
    if not workspace_path.exists():
        console.print(f"[yellow]Creating directory: {workspace_path}[/yellow]")
        workspace_path.mkdir(parents=True, exist_ok=True)
    
    workspace_name = name or workspace_path.name
    
    manager = WorkspaceManager(workspace_path)
    
    # Check if workspace already exists
    if manager.is_initialized() and not force:
        console.print(
            f"[red]Workspace already initialized at {workspace_path}[/red]"
        )
        console.print("Use --force to reinitialize.")
        raise typer.Exit(1)
    
    # Check if global home was already initialized
    global_was_initialized = manager.is_global_initialized()
    
    console.print(f"\n[bold blue]Initializing workspace:[/bold blue] {workspace_name}")
    console.print(f"[dim]Location: {workspace_path}[/dim]\n")
    
    # Create workspace structure (also initializes global home)
    created_dirs = manager.initialize(workspace_name)
    
    # Show global home status
    global_home = manager.get_global_home()
    if not global_was_initialized:
        console.print(f"[bold green]Global directory created:[/bold green] {global_home}")
        global_tree = Tree(f"[bold]~/.ai_assist[/bold]")
        for dir_name in ["prompts/", "agents/", "tools/", "models/", "cache/"]:
            global_tree.add(f"[magenta]{dir_name}[/magenta]")
        console.print(global_tree)
        console.print()
    else:
        console.print(f"[dim]Global directory: {global_home}[/dim]\n")
    
    # Display workspace structure
    console.print(f"[bold green]Workspace structure:[/bold green]")
    tree = Tree(f"[bold]{workspace_name}[/bold]")
    
    for dir_path in sorted(created_dirs):
        rel_path = dir_path.relative_to(workspace_path)
        parts = rel_path.parts
        
        current = tree
        for part in parts:
            current = current.add(f"[cyan]{part}/[/cyan]")
    
    console.print(tree)
    console.print()
    
    # Show configuration file
    config_file = workspace_path / "config.yaml"
    console.print(
        Panel(
            f"[green]Workspace initialized successfully.[/green]\n\n"
            f"Configuration file: [cyan]{config_file}[/cyan]\n"
            f"Global config: [cyan]{global_home / 'config.yaml'}[/cyan]\n\n"
            f"Next steps:\n"
            f"  1. Edit [cyan]config.yaml[/cyan] to configure your LLM provider\n"
            f"  2. Add documents to [cyan]notes/[/cyan] for RAG indexing\n"
            f"  3. Add shared prompts to [cyan]~/.ai_assist/prompts/[/cyan]\n"
            f"  4. Run [cyan]ai_assist workspace status[/cyan] to check configuration",
            title="Success",
            border_style="green",
        )
    )

