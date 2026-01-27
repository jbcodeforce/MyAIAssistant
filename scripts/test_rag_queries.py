#!/usr/bin/env python3
"""Test script for RAG queries on environment engineering content.

This script tests the RAG system with sample queries related to water treatment
and air quality topics.
"""

import os
import sys
from typing import Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Default backend URL
DEFAULT_BACKEND_URL = os.getenv("AI_ASSIST_BACKEND_URL", "http://localhost:8000/api")


class RAGTester:
    """Test RAG queries against the backend API."""

    def __init__(self, backend_url: str = DEFAULT_BACKEND_URL):
        """Initialize the tester.
        
        Args:
            backend_url: Backend API base URL
        """
        self.backend_url = backend_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def get_stats(self) -> dict:
        """Get RAG vector store statistics."""
        try:
            response = self.client.get(f"{self.backend_url}/rag/stats")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching stats: {e}[/red]")
            return {}

    def search(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> dict:
        """Perform a semantic search query.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            category: Optional category filter
            
        Returns:
            Search response dictionary
        """
        try:
            # Use POST endpoint for more control
            payload = {
                "query": query,
                "n_results": n_results
            }
            if category:
                payload["category"] = category

            response = self.client.post(
                f"{self.backend_url}/rag/search",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            console.print(f"[red]Error performing search: {e}[/red]")
            if hasattr(e, "response") and e.response is not None:
                console.print(f"[red]Response: {e.response.text}[/red]")
            return {"query": query, "results": [], "total_results": 0}

    def display_stats(self):
        """Display RAG statistics."""
        stats = self.get_stats()
        if not stats:
            console.print("[yellow]Could not fetch statistics. Is the backend running?[/yellow]")
            return

        table = Table(title="RAG Vector Store Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Total Chunks", str(stats.get("total_chunks", 0)))
        table.add_row("Unique Documents", str(stats.get("unique_knowledge_items", 0)))
        table.add_row("Collection Name", stats.get("collection_name", "-"))
        table.add_row("Embedding Model", stats.get("embedding_model", "-"))

        console.print()
        console.print(table)
        console.print()

    def display_search_results(self, search_response: dict):
        """Display search results in a formatted table.
        
        Args:
            search_response: Search response dictionary
        """
        query = search_response.get("query", "")
        results = search_response.get("results", [])
        total = search_response.get("total_results", 0)

        if total == 0:
            console.print(f"[yellow]No results found for query: '{query}'[/yellow]")
            return

        table = Table(
            title=f"Search Results: '{query}'",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Score", justify="right", style="cyan", width=8)
        table.add_column("Title", style="yellow", max_width=40)
        table.add_column("Category", style="green", width=20)
        table.add_column("Content Preview", style="dim", max_width=60)

        for result in results:
            score = result.get("score", 0.0)
            title = result.get("title", "Unknown")
            uri = result.get("uri", "")
            content = result.get("content", "")
            
            # Extract category from URI or use default
            category = "N/A"
            if "water" in uri.lower() or "drinking" in uri.lower():
                category = "water_treatment"
            elif "air" in uri.lower():
                category = "air_quality"
            
            # Truncate content for display
            content_preview = content[:150] + "..." if len(content) > 150 else content

            table.add_row(
                f"{score:.3f}",
                title,
                category,
                content_preview
            )

        console.print()
        console.print(table)
        console.print(f"[dim]Total results: {total}[/dim]")
        console.print()

    def run_test_queries(self):
        """Run a series of test queries."""
        test_queries = [
            {
                "query": "How does water treatment work?",
                "category": None,
                "description": "General water treatment query"
            },
            {
                "query": "What are drinking water standards?",
                "category": "water_treatment",
                "description": "Water treatment category filter"
            },
            {
                "query": "What are PM2.5 air quality standards?",
                "category": "air_quality",
                "description": "Air quality specific query"
            },
            {
                "query": "What are the criteria air pollutants?",
                "category": None,
                "description": "General air quality query"
            },
            {
                "query": "How is indoor air quality monitored?",
                "category": "air_quality",
                "description": "Indoor air quality query"
            },
            {
                "query": "What contaminants are regulated in drinking water?",
                "category": "water_treatment",
                "description": "Water contaminants query"
            }
        ]

        console.print(Panel.fit(
            "[bold cyan]Environment Engineering RAG Test Queries[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        for i, test in enumerate(test_queries, 1):
            console.print(f"[bold]Test {i}/{len(test_queries)}:[/bold] {test['description']}")
            console.print(f"[dim]Query: '{test['query']}'[/dim]")
            if test['category']:
                console.print(f"[dim]Category filter: {test['category']}[/dim]")
            
            results = self.search(
                query=test['query'],
                n_results=5,
                category=test['category']
            )
            
            self.display_search_results(results)
            console.print("[dim]" + "─" * 80 + "[/dim]")
            console.print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test RAG queries on environment engineering content"
    )
    parser.add_argument(
        "--backend-url",
        default=DEFAULT_BACKEND_URL,
        help=f"Backend API URL (default: {DEFAULT_BACKEND_URL})"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show RAG statistics only"
    )
    parser.add_argument(
        "--query",
        help="Run a single query"
    )
    parser.add_argument(
        "--category",
        help="Filter by category (water_treatment or air_quality)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Number of results (default: 5)"
    )

    args = parser.parse_args()

    tester = RAGTester(backend_url=args.backend_url)

    # Check if backend is accessible
    try:
        stats = tester.get_stats()
        if not stats:
            console.print("[red]Error: Could not connect to backend. Is it running?[/red]")
            console.print(f"[dim]Backend URL: {args.backend_url}[/dim]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error connecting to backend: {e}[/red]")
        console.print(f"[dim]Backend URL: {args.backend_url}[/dim]")
        sys.exit(1)

    if args.stats:
        tester.display_stats()
    elif args.query:
        results = tester.search(
            query=args.query,
            n_results=args.n,
            category=args.category
        )
        tester.display_search_results(results)
    else:
        tester.display_stats()
        tester.run_test_queries()


if __name__ == "__main__":
    main()
