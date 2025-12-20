"""BeadsTracker implementation using bd CLI."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from jiro.core.paths import get_jiro_dir
from jiro.trackers.interface import Task, TaskStatus, TaskType


class BeadsTracker:
    """Issue tracker implementation using bd CLI.

    This implementation shells out to the bd (beads) CLI tool to manage issues.
    It parses JSON output and converts it to Task objects.
    """

    def __init__(
        self,
        project_root: Path,
        stealth: bool = False,
        project_name: str | None = None,
    ):
        """Initialize the BeadsTracker.

        Args:
            project_root: The root directory of the project.
            stealth: If True, use ~/.jiro-dreams-of-code/$PROJECT/.beads instead of local.
            project_name: Required in stealth mode. The project name for the directory.
        """
        self.project_root = Path(project_root)
        self.stealth = stealth
        self.project_name = project_name or self.project_root.name

        # Determine the beads directory based on mode
        # In both modes, beads lives inside the jiro directory
        jiro_dir = get_jiro_dir(self.project_root, stealth=stealth, project_name=self.project_name)
        self.beads_dir = jiro_dir / ".beads"

    def _run_bd_command(self, *args: str) -> str:
        """Run a bd CLI command and return JSON output.

        Args:
            *args: Arguments to pass to bd command.

        Returns:
            JSON output from the command.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        cmd = ["bd"] + list(args) + ["--json"]
        result = subprocess.run(
            cmd,
            cwd=self.beads_dir,
            capture_output=True,
            text=False,
            check=True,
        )
        return result.stdout.decode()

    def _parse_task(self, data: dict) -> Task:
        """Parse a task from bd JSON output.

        Args:
            data: Dictionary from bd JSON output.

        Returns:
            Task object.
        """
        # Parse timestamps
        created_at = self._parse_datetime(data.get("created_at"))
        updated_at = self._parse_datetime(data.get("updated_at"))
        closed_at = self._parse_datetime(data.get("closed_at"))

        return Task(
            id=data["id"],
            title=data["title"],
            task_type=data.get("issue_type", "task"),
            status=data.get("status", "open"),
            created_at=created_at or datetime.now(),
            description=data.get("description"),
            epic_id=data.get("epic_id"),
            priority=data.get("priority"),
            updated_at=updated_at,
            closed_at=closed_at,
            labels=data.get("labels"),
        )

    def _parse_datetime(self, timestamp: str | None) -> datetime | None:
        """Parse an ISO 8601 timestamp string.

        Args:
            timestamp: ISO 8601 timestamp string.

        Returns:
            Parsed datetime or None.
        """
        if not timestamp:
            return None
        # Handle both RFC3339 and ISO 8601 formats
        try:
            # Try RFC3339 format with Z suffix
            if timestamp.endswith("Z"):
                return datetime.fromisoformat(timestamp[:-1] + "+00:00")
            # Try standard ISO format
            return datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            return None

    def create_task(
        self,
        title: str,
        description: str | None = None,
        task_type: TaskType = "task",
        priority: int | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title.
            description: Optional task description.
            task_type: Type of task (bug, feature, task, epic, chore).
            priority: Optional priority (0-4, 0 is highest).
            epic_id: Optional parent epic ID.
            labels: Optional list of labels.

        Returns:
            The created task.
        """
        args = ["create", title]

        if description:
            args.extend(["-d", description])

        if task_type:
            args.extend(["-t", task_type])

        if priority is not None:
            args.extend(["-p", str(priority)])

        if epic_id:
            args.extend(["--parent", epic_id])

        if labels:
            args.extend(["-l", ",".join(labels)])

        output = self._run_bd_command(*args)
        tasks = json.loads(output)

        if not tasks:
            raise ValueError("No task returned from create")

        return self._parse_task(tasks[0])

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            The task.

        Raises:
            KeyError: If task not found.
        """
        output = self._run_bd_command("show", task_id)
        tasks = json.loads(output)

        if not tasks:
            raise KeyError(f"Task {task_id} not found")

        return self._parse_task(tasks[0])

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        epic_id: str | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            status: Filter by status.
            epic_id: Filter by parent epic.

        Returns:
            List of matching tasks.
        """
        args = ["list"]

        if status:
            args.extend(["-s", status])

        if epic_id:
            args.extend(["--parent", epic_id])

        output = self._run_bd_command(*args)
        tasks_data = json.loads(output)

        return [self._parse_task(task_data) for task_data in tasks_data]

    def update_task(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        labels: list[str] | None = None,
    ) -> Task:
        """Update a task.

        Args:
            task_id: The task identifier.
            status: New status.
            title: New title.
            description: New description.
            priority: New priority.
            labels: New labels.

        Returns:
            The updated task.
        """
        args = ["update", task_id]

        if status:
            args.extend(["-s", status])

        if title:
            args.extend(["--title", title])

        if description:
            args.extend(["-d", description])

        if priority is not None:
            args.extend(["-p", str(priority)])

        if labels:
            args.extend(["-l", ",".join(labels)])

        output = self._run_bd_command(*args)
        tasks = json.loads(output)

        if not tasks:
            raise ValueError("No task returned from update")

        return self._parse_task(tasks[0])

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None:
        """Get the next task ready to be worked on.

        A task is ready if it has no unresolved blocking dependencies.

        Args:
            epic_id: Optional epic filter.

        Returns:
            The next ready task, or None if no tasks are ready.
        """
        args = ["ready"]

        if epic_id:
            args.extend(["--parent", epic_id])

        output = self._run_bd_command(*args)
        tasks = json.loads(output)

        if not tasks:
            return None

        return self._parse_task(tasks[0])

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Add a dependency between tasks.

        Args:
            task_id: The task that depends on another.
            depends_on_id: The task being depended upon.
        """
        self._run_bd_command("dep", task_id, depends_on_id)

    def close_task(self, task_id: str, reason: str | None = None) -> None:
        """Close a task.

        Args:
            task_id: The task to close.
            reason: Optional reason for closing.
        """
        args = ["close", task_id]

        if reason:
            args.extend(["-r", reason])

        self._run_bd_command(*args)
