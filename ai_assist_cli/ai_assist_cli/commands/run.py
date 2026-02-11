"""Run command - Start backend and frontend services."""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from ai_assist_cli.services.workspace import WorkspaceManager

console = Console()

# Global process references for cleanup
backend_process: Optional[subprocess.Popen] = None
frontend_process: Optional[subprocess.Popen] = None


def find_workspace(start_path: Path) -> Optional[Path]:
    """Find workspace by walking up directory tree looking for workspace marker."""
    current = start_path.resolve()
    while current != current.parent:
        manager = WorkspaceManager(current)
        if manager.is_initialized():
            return current
        current = current.parent
    return None


def find_project_root(workspace_path: Path) -> Optional[Path]:
    """Find project root containing backend/ and frontend/ directories."""
    current = workspace_path.resolve()
    while current != current.parent:
        backend_dir = current / "backend"
        frontend_dir = current / "frontend"
        if backend_dir.exists() and frontend_dir.exists():
            return current
        current = current.parent
    return None


def check_command(command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def wait_for_service(url: str, timeout: int = 30, service_name: str = "Service") -> bool:
    """Wait for a service to become available."""
    import urllib.request
    import urllib.error

    console.print(f"  [yellow]Waiting for {service_name} to start...[/yellow]")
    for i in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            console.print(f"  [green]{service_name} is ready![/green]")
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    console.print(f"  [red]{service_name} failed to start within {timeout} seconds[/red]")
    return False


def cleanup_processes():
    """Cleanup function to kill running processes."""
    global backend_process, frontend_process
    
    if backend_process:
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
            console.print("[green]Backend stopped[/green]")
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                backend_process.kill()
            except ProcessLookupError:
                pass
    
    if frontend_process:
        try:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
            console.print("[green]Frontend stopped[/green]")
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                frontend_process.kill()
            except ProcessLookupError:
                pass


def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM signals."""
    console.print("\n[yellow]Shutting down services...[/yellow]")
    cleanup_processes()
    sys.exit(0)


def run_dev_mode(workspace_path: Path, project_root: Path):
    """Run services in development mode."""
    global backend_process, frontend_process
    
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    env = os.environ.copy()
    
    # Check requirements
    console.print("[yellow]Checking requirements...[/yellow]")
    if not check_command("uv"):
        console.print("[red]Error: 'uv' is not installed[/red]")
        console.print("Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        raise typer.Exit(1)
    
    if not check_command("node"):
        console.print("[red]Error: 'node' is not installed[/red]")
        raise typer.Exit(1)
    
    if not check_command("npm"):
        console.print("[red]Error: 'npm' is not installed[/red]")
        raise typer.Exit(1)
    
    # Start backend
    console.print("\n[green]Starting Backend...[/green]")
    console.print(f"  Port: 8000")
    
    backend_cmd = [
        "uv", "run", "--project", str(backend_dir),
        "uvicorn", "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--app-dir", str(backend_dir),
    ]
    
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(workspace_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    console.print(f"  PID: {backend_process.pid}")
    
    if not wait_for_service("http://localhost:8000/health", service_name="Backend"):
        cleanup_processes()
        raise typer.Exit(1)
    
    # Start frontend
    console.print("\n[green]Starting Frontend...[/green]")
    console.print(f"  Port: 3000")
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        console.print("  [yellow]Installing dependencies...[/yellow]")
        install_process = subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_dir),
            check=True,
        )
    
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    console.print(f"  PID: {frontend_process.pid}")
    
    if not wait_for_service("http://localhost:3000", service_name="Frontend"):
        cleanup_processes()
        raise typer.Exit(1)
    
    # Display success message
    console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print("[bold green]Development environment is running![/bold green]")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print("")
    console.print("  [yellow]Frontend:[/yellow]  http://localhost:3000")
    console.print("  [yellow]Backend:[/yellow]   http://localhost:8000")
    console.print("  [yellow]API Docs:[/yellow]  http://localhost:8000/docs")
    console.print("  [yellow]Config:[/yellow]    http://localhost:8000/debug/config")
    console.print("")
    console.print("  Press [red]Ctrl+C[/red] to stop all services")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    
    # Wait for processes
    try:
        backend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


def run_docker_mode(workspace_path: Path, project_root: Path):
    """Run services using Docker Compose."""
    
    # Check if Docker is available
    if not check_command("docker"):
        console.print("[red]Error: 'docker' is not installed[/red]")
        raise typer.Exit(1)
    
    # Check for docker-compose or docker compose
    has_docker_compose = check_command("docker-compose")
    has_docker_compose_v2 = check_command("docker")  # docker compose is a subcommand
    
    if not (has_docker_compose or has_docker_compose_v2):
        console.print("[red]Error: 'docker-compose' is not available[/red]")
        raise typer.Exit(1)
    
    # Find docker-compose.yml
    docker_compose_file = project_root / "docker-compose.yml"
    if not docker_compose_file.exists():
        console.print(f"[red]Error: docker-compose.yml not found at {docker_compose_file}[/red]")
        raise typer.Exit(1)
    
    # Ensure workspace data directory exists
    data_dir = workspace_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create docker-compose override file
    console.print("\n[green]Starting services with Docker Compose...[/green]")
    console.print(f"  Workspace: {workspace_path}")
    console.print(f"  Data directory: {data_dir}")
    console.print(f"  Project root: {project_root}")
    
    # Read the original docker-compose.yml
    try:
        with open(docker_compose_file) as f:
            compose_config = yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[red]Error reading docker-compose.yml: {e}[/red]")
        raise typer.Exit(1)
    
    # Override volumes for backend service
    if "services" not in compose_config:
        compose_config["services"] = {}
    
    if "backend" not in compose_config["services"]:
        console.print("[red]Error: 'backend' service not found in docker-compose.yml[/red]")
        raise typer.Exit(1)
    
    backend_service = compose_config["services"]["backend"]
    
    # Update volumes to mount workspace data
    data_abs_path = str(data_dir.resolve())
    volumes = [f"{data_abs_path}:/app/data"]
    backend_service["volumes"] = volumes
    
    # Write temporary override file
    override_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, dir=str(project_root)) as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
            override_file = f.name
        
        # Prepare docker-compose command
        # Use both original and override files
        if has_docker_compose:
            cmd = ["docker-compose", "-f", str(docker_compose_file), "-f", override_file, "up"]
            down_cmd = ["docker-compose", "-f", str(docker_compose_file), "-f", override_file, "down"]
        else:
            cmd = ["docker", "compose", "-f", str(docker_compose_file), "-f", override_file, "up"]
            down_cmd = ["docker", "compose", "-f", str(docker_compose_file), "-f", override_file, "down"]
        
        console.print(f"\n[yellow]Running: {' '.join(cmd)}[/yellow]\n")
        
        # Run docker-compose
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
        )
        
        # Wait for process
        try:
            process.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down services...[/yellow]")
            # Send SIGTERM to docker-compose
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Stop containers
            try:
                subprocess.run(down_cmd, cwd=str(project_root), check=False, timeout=30)
            except subprocess.TimeoutExpired:
                console.print("[yellow]Warning: docker-compose down timed out[/yellow]")
    except Exception as e:
        console.print(f"[red]Error running Docker Compose: {e}[/red]")
        raise typer.Exit(1)
    finally:
        # Clean up temporary file
        if override_file:
            try:
                os.unlink(override_file)
            except OSError:
                pass


def run_command(
    workspace_path: Optional[Path] = typer.Argument(
        None,
        help="Path to workspace. Defaults to current directory (auto-detected).",
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        "-d",
        help="Run in development mode (uses uv and npm instead of Docker).",
    ),
):
    """Start backend and frontend services.
    
    By default, uses Docker Compose to start services with pre-built images.
    Use --dev flag to run services directly using uv and npm (development mode).
    
    The command will auto-detect the workspace by looking for the workspace marker
    in the current directory or parent directories. You can also specify a workspace path.
    """
    # Detect workspace
    if workspace_path:
        workspace_path = workspace_path.resolve()
    else:
        workspace_path = find_workspace(Path.cwd())
        if not workspace_path:
            console.print("[red]No workspace found. Run from a workspace directory or specify a path.[/red]")
            console.print("Run [cyan]ai_assist init[/cyan] to create a workspace.")
            raise typer.Exit(1)
    
    # Validate workspace
    manager = WorkspaceManager(workspace_path)
    if not manager.is_initialized():
        console.print(f"[red]Workspace not initialized at {workspace_path}[/red]")
        console.print("Run [cyan]ai_assist init[/cyan] to initialize the workspace.")
        raise typer.Exit(1)
    
    # Find project root
    project_root = find_project_root(workspace_path)
    if not project_root:
        console.print("[red]Could not find project root (backend/ and frontend/ directories)[/red]")
        raise typer.Exit(1)
    
    # Register signal handlers for dev mode
    if dev:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Display configuration
    console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print(f"[bold blue]  MyAIAssistant {'Development' if dev else 'Production'} Mode[/bold blue]")
    console.print(f"[bold blue]  Workspace: {workspace_path.name}[/bold blue]")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    
    console.print("\n[yellow]Configuration:[/yellow]")
    console.print(f"  Project Root:  {project_root}")
    console.print(f"  Workspace:     {workspace_path}")
    
    # Run in appropriate mode
    if dev:
        run_dev_mode(workspace_path, project_root)
    else:
        run_docker_mode(workspace_path, project_root)
