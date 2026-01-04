"""Global configuration and resource management commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from ai_assist_cli.services.workspace import WorkspaceManager

app = typer.Typer(help="Global configuration and resource management.")
console = Console()


@app.command("status")
def status():
    """Show global AI Assist home status."""
    global_home = WorkspaceManager.get_global_home()
    
    if not WorkspaceManager.is_global_initialized():
        console.print(f"[yellow]Global home not initialized at {global_home}[/yellow]")
        console.print("Run [cyan]ai_assist init[/cyan] to initialize.")
        return
    
    console.print(f"\n[bold blue]Global AI Assist Home[/bold blue]")
    console.print(f"[dim]Location: {global_home}[/dim]\n")
    
    config = WorkspaceManager.load_global_config()
    
    # Configuration table
    table = Table(title="Global Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Version", config.get("version", "N/A"))
    table.add_row("Default LLM Provider", config.get("default_llm_provider", "Not set"))
    table.add_row("Default LLM Model", config.get("default_llm_model", "Not set"))
    table.add_row("Default Embedding Model", config.get("default_embedding_model", "Not set"))
    
    console.print(table)
    console.print()
    
    # Directory status
    dirs_table = Table(title="Global Directories")
    dirs_table.add_column("Directory", style="cyan")
    dirs_table.add_column("Status", style="green")
    dirs_table.add_column("Items", justify="right")
    
    for dir_name in WorkspaceManager.GLOBAL_DIRS:
        dir_path = global_home / dir_name
        exists = dir_path.exists()
        item_count = len(list(dir_path.iterdir())) if exists else 0
        dirs_table.add_row(
            dir_name,
            "[green]OK[/green]" if exists else "[red]Missing[/red]",
            str(item_count),
        )
    
    console.print(dirs_table)


@app.command("config")
def show_config():
    """Display global configuration file."""
    global_home = WorkspaceManager.get_global_home()
    config_file = global_home / "config.yaml"
    
    if not config_file.exists():
        console.print("[red]Global configuration not found.[/red]")
        console.print("Run [cyan]ai_assist init[/cyan] to initialize.")
        raise typer.Exit(1)
    
    content = config_file.read_text()
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command("prompts")
def list_prompts():
    """List available global prompts."""
    global_home = WorkspaceManager.get_global_home()
    prompts_dir = global_home / "prompts"
    
    if not prompts_dir.exists():
        console.print("[yellow]No global prompts directory found.[/yellow]")
        return
    
    console.print(f"\n[bold blue]Global Prompts[/bold blue]")
    console.print(f"[dim]Location: {prompts_dir}[/dim]\n")
    
    prompts = list(prompts_dir.glob("*.md"))
    if not prompts:
        console.print("[yellow]No prompts found.[/yellow]")
        return
    
    table = Table()
    table.add_column("Prompt", style="cyan")
    table.add_column("Size", justify="right")
    
    for prompt in sorted(prompts):
        size = prompt.stat().st_size
        table.add_row(prompt.name, f"{size} bytes")
    
    console.print(table)


@app.command("agents")
def list_agents():
    """List available global agents."""
    global_home = WorkspaceManager.get_global_home()
    agents_dir = global_home / "agents"
    
    if not agents_dir.exists():
        console.print("[yellow]No global agents directory found.[/yellow]")
        return
    
    console.print(f"\n[bold blue]Global Agents[/bold blue]")
    console.print(f"[dim]Location: {agents_dir}[/dim]\n")
    
    agents = list(agents_dir.glob("*.yaml"))
    if not agents:
        console.print("[yellow]No agents found.[/yellow]")
        return
    
    import yaml
    
    table = Table()
    table.add_column("Agent", style="cyan")
    table.add_column("Description", style="dim")
    table.add_column("Prompt", style="green")
    
    for agent_file in sorted(agents):
        with open(agent_file) as f:
            agent = yaml.safe_load(f) or {}
        table.add_row(
            agent.get("name", agent_file.stem),
            agent.get("description", ""),
            agent.get("system_prompt", ""),
        )
    
    console.print(table)


@app.command("tools")
def list_tools():
    """List available global tools."""
    global_home = WorkspaceManager.get_global_home()
    tools_dir = global_home / "tools"
    
    if not tools_dir.exists():
        console.print("[yellow]No global tools directory found.[/yellow]")
        return
    
    console.print(f"\n[bold blue]Global Tools[/bold blue]")
    console.print(f"[dim]Location: {tools_dir}[/dim]\n")
    
    tools = list(tools_dir.glob("*.py")) + list(tools_dir.glob("*.yaml"))
    if not tools:
        console.print("[yellow]No tools found.[/yellow]")
        console.print("Add tool definitions to [cyan]~/.ai_assist/tools/[/cyan]")
        return
    
    table = Table()
    table.add_column("Tool", style="cyan")
    table.add_column("Type", style="green")
    
    for tool in sorted(tools):
        table.add_row(tool.stem, tool.suffix[1:])
    
    console.print(table)


@app.command("tree")
def show_tree():
    """Show the global directory structure."""
    global_home = WorkspaceManager.get_global_home()
    
    if not global_home.exists():
        console.print("[yellow]Global home not initialized.[/yellow]")
        return
    
    console.print(f"\n[bold blue]Global Directory Structure[/bold blue]\n")
    
    tree = Tree(f"[bold]{global_home}[/bold]")
    
    def add_to_tree(parent_tree, path: Path, max_depth: int = 2, current_depth: int = 0):
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return
        
        for item in items:
            if item.name.startswith("."):
                continue
            if item.is_dir():
                branch = parent_tree.add(f"[cyan]{item.name}/[/cyan]")
                add_to_tree(branch, item, max_depth, current_depth + 1)
            else:
                parent_tree.add(f"[green]{item.name}[/green]")
    
    add_to_tree(tree, global_home)
    console.print(tree)

