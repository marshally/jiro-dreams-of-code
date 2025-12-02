"""Web command implementation for starting the FastAPI server."""

from typing import Annotated

import typer
import uvicorn
from rich.console import Console

app = typer.Typer(
    name="web",
    help="Start the Jiro web server",
    no_args_is_help=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def web(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to run server on")] = 8000,
    daemon: Annotated[bool, typer.Option("--daemon", "-d", help="Run in background")] = False,
) -> None:
    """
    Start the Jiro web server.

    Launches FastAPI server with HTMX frontend for spec refinement,
    task monitoring, and execution status.

    Examples:
        jiro web              # Run in foreground
        jiro web --daemon     # Run in background
        jiro web --port 9000  # Use custom port
    """
    console.print(f"[cyan]Starting Jiro web server on http://localhost:{port}[/cyan]")
    if daemon:
        console.print("[yellow]Running in background mode[/yellow]")

    # Run the FastAPI app using uvicorn
    uvicorn.run(
        "jiro.web.app:app",
        host="0.0.0.0",
        port=port,
        reload=not daemon,  # Enable reload in development mode, disable in daemon mode
    )
