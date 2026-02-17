"""Knowledge management commands."""

import asyncio
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from ai_assist_cli.services.knowledge_processor import (
    KnowledgeProcessor,
    KnowledgeDocumentSpec,
    ProcessingResult,
    ProcessingAction,
    ProcessingSummary,
)

app = typer.Typer(help="Knowledge base management commands.")
console = Console()


def _run_async(coro):
    """Run an async coroutine in a new event loop."""
    return asyncio.run(coro)


@app.command("process")
def process_knowledge(
    json_file: Path = typer.Argument(
        ...,
        help="Path to JSON file containing document specifications.",
        exists=True,
        readable=True,
    ),
    backend_url: Optional[str] = typer.Option(
        None,
        "--backend-url",
        "-b",
        help="Backend API URL. Defaults to AI_ASSIST_BACKEND_URL env var or http://localhost:8000/api",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Validate JSON and show what would be processed without making API calls.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-indexing even if content unchanged.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output including errors.",
    ),
):
    """Process knowledge documents from a JSON specification file which lists the documents or websites to be processed.
    
    The JSON file should contain an array of document specifications:
    ```json
    [
      {"document_type": "website", "uri": "https://...", "collection": "flink"},
      {"document_type": "folder", "uri": "$HOME/docs", "collection": "python"}
    ]
    ```

    Supported document_type values: website, folder, markdown
    
    The 'collection' field is mapped to 'category' in the backend for filtering.
    Environment variables ($HOME) and ~ are expanded in URIs.
    """
    try:
        # Load and validate specifications
        specs = KnowledgeProcessor.load_specs(json_file)
        
        if not specs:
            console.print("[yellow]No document specifications found in JSON file.[/yellow]")
            raise typer.Exit(0)

        console.print(f"\n[bold]Found {len(specs)} document specification(s)[/bold]\n")

        if dry_run:
            _show_dry_run(specs)
            return

        # Process documents
        processor = KnowledgeProcessor(backend_url=backend_url)
        
        results: list[ProcessingResult] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing documents...", total=len(specs))
            
            def on_progress(current: int, total: int, result: ProcessingResult):
                progress.update(task, completed=current)
                results.append(result)
            
            summary = _run_async(processor.process_all(specs, on_progress, force=force))

        # Show results
        console.print()
        _show_results(summary.results, verbose)
        
        # Show summary
        _show_summary(summary)
        
        if summary.failed > 0:
            raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Backend HTTP error: {e.response.status_code} {e.response.reason_phrase}[/red]")
        if e.response.text:
            console.print(Panel(e.response.text[:1000], title="Response", border_style="red"))
        console.print_exception(show_locals=False)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Backend unreachable: {type(e).__name__}[/red]")
        console.print(f"[dim]{e}[/dim]")
        console.print_exception(show_locals=False)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print_exception(show_locals=False)
        raise typer.Exit(1)


def _show_dry_run(specs: list[KnowledgeDocumentSpec]):
    """Display what would be processed in dry-run mode."""
    table = Table(title="Documents to Process (Dry Run)")
    table.add_column("Type", style="cyan")
    table.add_column("URI", style="dim", max_width=60)
    table.add_column("Collection", style="green")
    table.add_column("Title", style="yellow")

    for spec in specs:
        title = spec.title or KnowledgeProcessor.generate_title(spec)
        # Truncate long URIs
        uri_display = spec.uri if len(spec.uri) <= 60 else spec.uri[:57] + "..."
        table.add_row(
            spec.document_type,
            uri_display,
            spec.collection,
            title,
        )

    console.print(table)
    console.print("\n[dim]Use without --dry-run to process these documents.[/dim]")


def _show_results(results: list[ProcessingResult], verbose: bool):
    """Display processing results."""
    table = Table(title="Processing Results")
    table.add_column("Status", justify="center")
    table.add_column("Action", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Title/URI", max_width=50)
    table.add_column("Chunks", justify="right")
    table.add_column("Error", style="red", max_width=50)

    for result in results:
        if result.success:
            if result.action == ProcessingAction.SKIPPED:
                status = "[yellow]SKIP[/yellow]"
            else:
                status = "[green]OK[/green]"
            title = result.knowledge.title if result.knowledge else result.spec.uri
            chunks = str(result.indexing.chunks_indexed) if result.indexing else "-"
        else:
            status = "[red]FAIL[/red]"
            title = result.spec.uri
            chunks = "-"
        
        # Truncate long titles
        title_display = title if len(title) <= 50 else title[:47] + "..."
        
        # Format action
        action_display = result.action if result.action else "-"
        
        error_display = (result.error[:50] + "..." if result.error and len(result.error) > 50 else result.error or "")
        row = [status, action_display, result.spec.document_type, title_display, chunks, error_display]
        table.add_row(*row)

    console.print(table)

    if verbose:
        for result in results:
            if not result.success and result.error_detail:
                uri_short = result.spec.uri[:40] + ("..." if len(result.spec.uri) > 40 else "")
                console.print(Panel(result.error_detail, title=f"[red]Details: {uri_short}[/red]", border_style="red"))


def _show_summary(summary: ProcessingSummary):
    """Display processing summary."""
    lines = []
    lines.append(f"Total: {summary.total}")
    lines.append(f"Created: {summary.created}")
    lines.append(f"Updated: {summary.updated}")
    lines.append(f"Skipped: {summary.skipped}")
    lines.append(f"Failed: {summary.failed}")
    
    if summary.failed == 0:
        panel = Panel(
            "\n".join(lines),
            title="[green]Summary - All Successful[/green]",
            border_style="green",
        )
    else:
        panel = Panel(
            "\n".join(lines),
            title="[yellow]Summary[/yellow]",
            border_style="yellow",
        )
    
    console.print(panel)


@app.command("stats")
def show_stats(
    backend_url: Optional[str] = typer.Option(
        None,
        "--backend-url",
        "-b",
        help="Backend API URL. Defaults to AI_ASSIST_BACKEND_URL env var or http://localhost:8000/api",
    ),
):
    """Show RAG vector store statistics."""
    try:
        processor = KnowledgeProcessor(backend_url=backend_url)
        stats = _run_async(processor.get_stats())
        
        console.print("\n[bold blue]RAG Vector Store Statistics[/bold blue]\n")
        
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Chunks", str(stats.get("total_chunks", 0)))
        table.add_row("Unique Documents", str(stats.get("unique_knowledge_items", 0)))
        table.add_row("Collection Name", stats.get("collection_name", "-"))
        table.add_row("Embedding Model", stats.get("embedding_model", "-"))
        
        console.print(table)
        
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Backend HTTP error: {e.response.status_code} {e.response.reason_phrase}[/red]")
        if e.response.text:
            console.print(f"[dim]{e.response.text[:500]}[/dim]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Backend unreachable: {type(e).__name__}[/red]")
        console.print(f"[dim]{e}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error fetching stats: {e}[/red]")
        console.print_exception(show_locals=False)
        raise typer.Exit(1)

