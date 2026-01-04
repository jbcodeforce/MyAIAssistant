"""Main CLI entry point for AI Assist."""

import typer
from rich.console import Console

from ai_assist_cli.commands import init, config, workspace, global_cmd

app = typer.Typer(
    name="ai_assist",
    help="CLI tool to manage AI Assistant workspaces.",
    no_args_is_help=True,
)

console = Console()

# Register subcommand groups
app.add_typer(workspace.app, name="workspace", help="Workspace management commands")
app.add_typer(config.app, name="config", help="Configuration management commands")
app.add_typer(global_cmd.app, name="global", help="Global resources management")

# Register top-level init command with explicit name
app.command(name="init")(init.init_command)


@app.callback()
def main_callback():
    """AI Assist CLI - Manage your AI Assistant workspaces."""
    pass


if __name__ == "__main__":
    app()

