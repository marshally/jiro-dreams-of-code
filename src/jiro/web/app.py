"""FastAPI web application for jiro-dreams-of-code."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

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
