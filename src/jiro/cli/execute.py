"""Execute command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from jiro.config.loader import load_config
from jiro.core.paths import get_database_path
from jiro.core.session import HaltError, SessionOrchestrator
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import SessionRepository, TaskExecutionRepository

app = typer.Typer(
    name="execute",
    help="Execute tasks with preflight and postflight checks",
    no_args_is_help=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def execute(
    epic: Annotated[
        str | None, typer.Option("--epic", help="Limit execution to a specific epic")
    ] = None,
) -> None:
    """
    Execute tasks with preflight and postflight checks.

    Runs session preflight, iteratively executes tasks, and runs
    session postflight. Agents work with strict TDD discipline.

    Examples:
        jiro execute
        jiro execute --epic JIRO-42
    """
    project_root = Path.cwd()
    project_name = project_root.name

    # Load config
    config = load_config(project_root, project_name)

    # Initialize database and repositories
    db_path = get_database_path(project_root, stealth=False, project_name=project_name)
    db = get_database(db_path)
    ensure_schema(db)
    session_repo = SessionRepository(db)
    task_repo = TaskExecutionRepository(db)

    # Create orchestrator and run session
    orchestrator = SessionOrchestrator(config, session_repo, task_repo)

    console.print("[cyan]Starting execution session...[/cyan]")
    if epic:
        console.print(f"[dim]Filtering by epic: {epic}[/dim]")

    try:
        result = orchestrator.run(epic_id=epic)

        if result.status == "completed":
            console.print("[green]Session completed successfully[/green]")
            console.print(f"  Tasks completed: {result.tasks_completed}")
        elif result.status == "halted":
            console.print("[red]Session halted[/red]")
            console.print(f"  Error: {result.error}")
            console.print(f"  Tasks completed: {result.tasks_completed}")
            console.print(f"  Tasks failed: {result.tasks_failed}")
            raise typer.Exit(5)
        elif result.status == "failed":
            console.print("[red]Session failed[/red]")
            console.print(f"  Error: {result.error}")
            raise typer.Exit(1)

    except HaltError as e:
        console.print(f"[red]Session halted: {e.reason}[/red]")
        raise typer.Exit(5) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1) from e
