"""Tasks subcommand module for managing and viewing tasks."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.config.loader import load_config
from jiro.formatters.toon import ToonFormatter
from jiro.trackers.beads import BeadsTracker
from jiro.trackers.interface import Task, TaskStatus

app = typer.Typer(
    name="tasks",
    help="Manage and view tasks in the issue tracker",
    no_args_is_help=True,
)

console = Console()


def _get_tracker() -> BeadsTracker:
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
    grouped: dict[str, list[Task]] = {}
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

    # Sort status order for display
    status_order = ["open", "in_progress", "blocked", "closed"]
    sorted_statuses = [s for s in status_order if s in grouped] + [
        s for s in grouped if s not in status_order
    ]

    for status in sorted_statuses:
        status_tasks = grouped[status]
        for task in status_tasks:
            priority_display = str(task.priority) if task.priority is not None else "-"
            table.add_row(
                task.id,
                task.title,
                task.task_type,
                task.status,
                priority_display,
            )

    console.print(table)


def _display_task_detail(task: Task) -> None:
    """Display detailed information about a single task."""
    # Create a table for the task details
    table = Table(title=f"Task: {task.id}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    # Add basic information
    table.add_row("ID", task.id)
    table.add_row("Title", task.title)
    table.add_row("Description", task.description or "-")
    table.add_row("Type", task.task_type)
    table.add_row("Status", task.status)
    table.add_row("Priority", str(task.priority) if task.priority is not None else "-")

    # Add epic info if present
    if task.epic_id:
        table.add_row("Epic", task.epic_id)

    # Add timestamps
    if task.created_at:
        table.add_row("Created", task.created_at.isoformat())
    if task.updated_at:
        table.add_row("Updated", task.updated_at.isoformat())
    if task.closed_at:
        table.add_row("Closed", task.closed_at.isoformat())

    # Add labels if present
    if task.labels:
        table.add_row("Labels", ", ".join(task.labels))

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
            # Output as TOON format
            formatter = ToonFormatter()
            print(formatter.format_tasks(tasks))
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
    try:
        tracker = _get_tracker()

        # Get the task
        task = tracker.get_task(task_id)

        if json_output:
            # Output as JSON
            json_output_data = _format_task_json(task)
            console.print(json.dumps(json_output_data))
        elif toon:
            # Output as TOON format
            formatter = ToonFormatter()
            print(formatter.format_task(task))
        else:
            # Display as Rich formatted output
            _display_task_detail(task)

    except KeyError as e:
        console.print(f"[red]Error: Task not found - {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error showing task: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


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
        jiro tasks next --json
    """
    try:
        tracker = _get_tracker()

        # Get the next ready task, optionally filtered by epic
        task = tracker.get_next_ready_task(epic_id=epic)

        if task is None:
            if json_output:
                # Output null for no task (use plain print to avoid Rich wrapping)
                print("null")
            else:
                console.print("[yellow]No ready tasks found[/yellow]")
            return

        if json_output:
            # Output as JSON (use plain print to avoid Rich wrapping)
            json_output_data = _format_task_json(task)
            print(json.dumps(json_output_data))
        elif toon:
            # Output as TOON format
            formatter = ToonFormatter()
            print(formatter.format_task(task))
        else:
            # Display as Rich formatted output
            _display_task_detail(task)

    except Exception as e:  # noqa: B904
        console.print(f"[red]Error getting next task: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
