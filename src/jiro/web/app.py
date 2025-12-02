"""FastAPI web application for jiro-dreams-of-code."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from jiro.core.paths import get_logs_dir
from jiro.db.database import get_database
from jiro.db.repository import PromptRepository, SessionRepository, TaskExecutionRepository
from jiro.trackers.beads import BeadsTracker
from jiro.trackers.interface import Task, TaskStatus

# Initialize FastAPI app
app = FastAPI(title="jiro-dreams-of-code", version="0.1.0")

# Setup Jinja2 template environment
# Use the package's assets/templates directory
assets_dir = Path(__file__).parent.parent / "assets"
templates_dir = assets_dir / "templates"

# Create Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=True,
)


# Mount static files if static directory exists
static_dir = assets_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def get_tracker() -> BeadsTracker:
    """Get the task tracker instance.

    Returns:
        BeadsTracker instance configured for the current project.
    """
    project_root = Path.cwd()
    return BeadsTracker(project_root)


def get_database_connection():
    """Get the database connection for the current project.

    Returns:
        Database connection or None if not found.
    """
    try:
        project_root = Path.cwd()
        jiro_dir = project_root / ".jiro-dreams-of-code"
        db_path = jiro_dir / "jiro.db"
        return get_database(db_path)
    except Exception:
        return None


def get_tasks_grouped_by_status(tasks: list[Task]) -> dict[TaskStatus, list[Task]]:
    """Group tasks by their status.

    Args:
        tasks: List of tasks to group.

    Returns:
        Dictionary mapping status to list of tasks with that status.
    """
    grouped: dict[TaskStatus, list[Task]] = {
        "open": [],
        "in_progress": [],
        "blocked": [],
        "closed": [],
    }

    for task in tasks:
        grouped[task.status].append(task)

    return grouped


def get_tasks_grouped_by_epic(tasks: list[Task]) -> dict[str | None, list[Task]]:
    """Group tasks by their epic.

    Args:
        tasks: List of tasks to group.

    Returns:
        Dictionary mapping epic ID (or None) to list of tasks.
    """
    grouped: dict[str | None, list[Task]] = {}

    for task in tasks:
        epic_id = task.epic_id
        if epic_id not in grouped:
            grouped[epic_id] = []
        grouped[epic_id].append(task)

    return grouped


def _get_all_log_entries(logs_dir: Path) -> list[dict]:
    """Read all log entries from JSONL files in chronological order.

    Args:
        logs_dir: Path to the logs directory.

    Returns:
        List of log entries sorted chronologically.
    """
    entries = []

    # Get all JSONL files sorted by name (date)
    if not logs_dir.exists():
        return entries

    log_files = sorted(logs_dir.glob("*.jsonl"))

    for log_file in log_files:
        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
        except OSError:
            # Skip files that can't be read
            continue

    # Sort by timestamp if available
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=False)

    return entries


@app.get("/health", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Render the home page template."""
    try:
        template = template_env.get_template("index.html")
        return template.render()
    except Exception:
        # Fallback if template doesn't exist
        return "<html><body><h1>Welcome to jiro-dreams-of-code</h1></body></html>"


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_list() -> str:
    """Render the task list page.

    Returns:
        HTML content with task list grouped by status.
    """
    try:
        # Try to get tasks from tracker
        tracker = get_tracker()
        all_tasks = tracker.list_tasks()
        grouped_tasks = get_tasks_grouped_by_status(all_tasks)
    except Exception:
        # Fallback if tracker not available
        grouped_tasks = {
            "open": [],
            "in_progress": [],
            "blocked": [],
            "closed": [],
        }

    template = template_env.get_template("tasks.html")
    return template.render(
        grouped_tasks=grouped_tasks,
        all_tasks=all_tasks if "all_tasks" in locals() else [],
    )


@app.get("/status", response_class=HTMLResponse)
async def status_dashboard() -> str:
    """Render the session status dashboard.

    Returns:
        HTML content with active sessions and their status.
    """
    sessions = []
    session_data = []

    try:
        # Get database connection and repositories
        db = get_database_connection()
        if db:
            session_repo = SessionRepository(db)
            task_repo = TaskExecutionRepository(db)
            prompt_repo = PromptRepository(db)

            # Get all active sessions
            sessions = session_repo.get_active()

            # Build session data with task and progress info
            for session in sessions:
                task_executions = task_repo.get_by_session(session.id)

                # Calculate progress
                completed_count = sum(
                    1 for te in task_executions if te.status in ["success", "failed"]
                )
                total_count = len(task_executions)
                progress_percent = (completed_count / total_count * 100) if total_count > 0 else 0

                # Find current task
                current_task = None
                for te in task_executions:
                    if te.status == "running":
                        current_task = te.task_id
                        break

                # Get token usage
                total_tokens = prompt_repo.get_total_tokens(session.id)

                session_data.append(
                    {
                        "id": session.id,
                        "branch_name": session.branch_name,
                        "status": session.status,
                        "epic_id": session.epic_id,
                        "started_at": session.started_at.isoformat(),
                        "current_task": current_task,
                        "tasks_completed": completed_count,
                        "tasks_total": total_count,
                        "progress_percent": progress_percent,
                        "tokens_used": total_tokens,
                    }
                )
    except Exception:
        # Fallback if database not available
        pass

    template = template_env.get_template("status.html")
    return template.render(
        sessions=session_data,
        has_sessions=len(session_data) > 0,
    )


@app.get("/logs", response_class=HTMLResponse)
async def logs_viewer() -> str:
    """Render the logs viewer page.

    Returns:
        HTML content with recent log entries from JSONL files.
    """
    log_entries = []

    try:
        # Get logs directory
        project_root = Path.cwd()
        logs_dir = get_logs_dir(
            project_root=project_root,
            stealth=True,
            project_name=project_root.name,
        )

        # Get all log entries
        entries = _get_all_log_entries(logs_dir)

        # Apply tail to get last 50 entries
        log_entries = entries[-50:] if entries else []

    except Exception:
        # Fallback if logs not available
        pass

    template = template_env.get_template("logs.html")
    return template.render(
        log_entries=log_entries,
        has_logs=len(log_entries) > 0,
    )
