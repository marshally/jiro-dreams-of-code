"""Status subcommand module for viewing active sessions and progress."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.db.database import get_database
from jiro.db.repository import PromptRepository, SessionRepository, TaskExecutionRepository

console = Console()


def _get_database():
    """Get the database connection for the current project."""
    project_root = Path.cwd()
    jiro_dir = project_root / ".jiro-dreams-of-code"
    db_path = jiro_dir / "jiro.db"
    return get_database(db_path)


def _format_session_json(session, task_executions, total_tokens):
    """Convert session data to JSON-serializable dictionary."""
    # Calculate progress - count completed vs. total tasks
    completed_count = sum(1 for te in task_executions if te.status in ["success", "failed"])
    total_count = len(task_executions)
    progress_percent = (completed_count / total_count * 100) if total_count > 0 else 0

    # Find current task (first running one)
    current_task = None
    for te in task_executions:
        if te.status == "running":
            current_task = te.task_id
            break

    return {
        "id": session.id,
        "branch_name": session.branch_name,
        "status": session.status,
        "epic_id": session.epic_id,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "preflight_passed_at": (
            session.preflight_passed_at.isoformat() if session.preflight_passed_at else None
        ),
        "current_task": current_task,
        "tasks_completed": completed_count,
        "tasks_total": total_count,
        "progress_percent": progress_percent,
        "tokens_used": total_tokens,
    }


def _display_session_table(sessions, task_repo, prompt_repo):
    """Display sessions in a Rich table format."""
    if not sessions:
        console.print("[yellow]No active sessions[/yellow]")
        return

    # Create a table
    table = Table(title="Active Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Branch", style="white")
    table.add_column("Status", style="green")
    table.add_column("Epic", style="blue")
    table.add_column("Tasks", style="magenta")
    table.add_column("Started", style="yellow")

    for session in sessions:
        # Get task executions for this session
        task_executions = task_repo.get_by_session(session.id)

        # Calculate progress
        completed = sum(1 for te in task_executions if te.status in ["success", "failed"])
        total = len(task_executions)
        progress_str = f"{completed}/{total}"

        # Format started time
        started_str = session.started_at.strftime("%H:%M:%S") if session.started_at else "-"

        epic_display = session.epic_id if session.epic_id else "-"

        table.add_row(
            session.id,
            session.branch_name,
            session.status,
            epic_display,
            progress_str,
            started_str,
        )

    console.print(table)

    # Display current task info for each session
    console.print()
    for session in sessions:
        task_executions = task_repo.get_by_session(session.id)

        # Find current (running) task
        current_task = None
        for te in task_executions:
            if te.status == "running":
                current_task = te
                break

        if current_task:
            total_tokens = prompt_repo.get_total_tokens(session.id)
            console.print(f"\n[bold]Current Task in {session.id}:[/bold]")
            console.print(f"  Task: {current_task.task_id}")
            console.print(f"  Phase: {current_task.phase}")
            console.print(f"  Status: {current_task.status}")
            console.print(f"  Tokens Used: {total_tokens:,}")


def status(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show status of all active sessions for this project.

    Displays running sessions, current task, progress, and context usage.

    Examples:
        jiro status
        jiro status --json
    """
    try:
        # Get database connection and repositories
        db = _get_database()
        session_repo = SessionRepository(db)
        task_repo = TaskExecutionRepository(db)
        prompt_repo = PromptRepository(db)

        # Get all active sessions
        sessions = session_repo.get_active()

        if json_output:
            # Build JSON output
            sessions_data = []
            for session in sessions:
                task_executions = task_repo.get_by_session(session.id)
                total_tokens = prompt_repo.get_total_tokens(session.id)
                session_json = _format_session_json(session, task_executions, total_tokens)
                sessions_data.append(session_json)

            output = {
                "count": len(sessions_data),
                "sessions": sessions_data,
            }
            # Use plain print to avoid Rich wrapping
            print(json.dumps(output))
        elif toon:
            console.print("[yellow]TOON format not implemented yet[/yellow]")
        else:
            # Display as Rich formatted output
            _display_session_table(sessions, task_repo, prompt_repo)

    except FileNotFoundError:
        console.print("[red]Error: Database not found. Run 'jiro init' first.[/red]")
        raise typer.Exit(code=1) from None
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error getting status: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
