"""Tasks subcommand module for managing and viewing tasks."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.config.loader import load_config
from jiro.trackers.beads import BeadsTracker
from jiro.trackers.interface import Task, TaskStatus

app = typer.Typer(
    name="tasks",
    help="Manage and view tasks in the issue tracker",
    no_args_is_help=True,
)

console = Console()


def _get_tracker():
    """Get a BeadsTracker instance for the current project."""
    project_root = Path.cwd()
    project_name = project_root.name
    _ = load_config(project_root, project_name)
    return BeadsTracker(project_root, stealth=False)


def _format_task_json(task: Task) -> dict:
    """Convert a Task object to a JSON-serializable dictionary."""
    return {
        "id": task.id,
        "title": task.title,
        "task_type": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "epic_id": task.epic_id,
        "description": task.description,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "closed_at": task.closed_at.isoformat() if task.closed_at else None,
        "labels": task.labels or [],
    }


def _group_tasks_by_status(tasks: list[Task]) -> dict[str, list[Task]]:
    """Group tasks by their status."""
    grouped = {}
    for task in tasks:
        if task.status not in grouped:
            grouped[task.status] = []
        grouped[task.status].append(task)
    return grouped


def _display_tasks_table(tasks: list[Task]) -> None:
    """Display tasks in a Rich table format."""
    if not tasks:
        console.print("[yellow]No tasks found[/yellow]")
        return

    # Group tasks by status for better readability
    grouped = _group_tasks_by_status(tasks)

    # Create a table
    table = Table(title="Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Epic", style="blue")

    # Sort status order for display
    status_order = ["open", "in_progress", "blocked", "closed"]
    sorted_statuses = [s for s in status_order if s in grouped] + [
        s for s in grouped if s not in status_order
    ]

    for status in sorted_statuses:
        status_tasks = grouped[status]
        for task in status_tasks:
            epic_display = task.epic_id if task.epic_id else "-"
            priority_display = str(task.priority) if task.priority is not None else "-"
            table.add_row(
                task.id,
                task.title,
                task.task_type,
                task.status,
                priority_display,
                epic_display,
            )

    console.print(table)


@app.command("list")
def tasks_list(
    status: Annotated[
        str | None,
        typer.Option(
            "--status", "-s", help="Filter by status (open, in_progress, closed, blocked)"
        ),
    ] = None,
    epic: Annotated[str | None, typer.Option("--epic", "-e", help="Filter by epic ID")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    List all tasks with optional filters.

    Shows tasks grouped by status.

    Examples:
        jiro tasks list
        jiro tasks list --status pending --epic JIRO-42
        jiro tasks list --json
    """
    try:
        tracker = _get_tracker()

        # Convert status to proper type if provided
        status_filter: TaskStatus | None = None
        if status:
            status_filter = status  # type: ignore

        # List tasks with filters
        tasks = tracker.list_tasks(status=status_filter, epic_id=epic)

        if json_output:
            # Output as JSON
            json_output_data = [_format_task_json(task) for task in tasks]
            console.print(json.dumps(json_output_data))
        elif toon:
            console.print("[yellow]TOON format not implemented yet[/yellow]")
        else:
            # Display as Rich table
            _display_tasks_table(tasks)

    except Exception as e:  # noqa: B904
        console.print(f"[red]Error listing tasks: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@app.command("show")
def tasks_show(
    task_id: Annotated[str, typer.Argument(help="Task ID to show")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show detailed information about a specific task.

    Displays full task details including description, dependencies,
    acceptance criteria, and execution history.

    Examples:
        jiro tasks show JIRO-15
        jiro tasks show JIRO-15 --json
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nTask ID: {task_id}")
    console.print("\nThis command will display full task details")


@app.command("next")
def tasks_next(
    epic: Annotated[str | None, typer.Option("--epic", "-e", help="Filter by epic ID")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show the next task to be executed.

    Displays the next task that is ready to work on (no blockers).

    Examples:
        jiro tasks next
        jiro tasks next --epic JIRO-42
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will show the next ready task")
    if epic:
        console.print(f"  - Filtered by epic: {epic}")
