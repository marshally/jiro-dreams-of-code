"""Issue tracker protocol interface."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

TaskType = Literal["bug", "feature", "task", "epic", "chore"]
TaskStatus = Literal["open", "in_progress", "blocked", "closed"]


@dataclass
class Task:
    """Represents a task from an issue tracker.

    This is a normalized representation that works across different
    issue tracking backends (beads, GitHub Issues, Jira, etc).
    """

    id: str
    title: str
    task_type: TaskType
    status: TaskStatus
    created_at: datetime
    description: str | None = None
    epic_id: str | None = None
    priority: int | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    labels: list[str] | None = None


@runtime_checkable
class IssueTracker(Protocol):
    """Protocol for issue tracker implementations.

    Defines the interface that all issue trackers must implement.
    This allows jiro to work with different backends (beads, GitHub, etc).
    """

    def create_task(
        self,
        title: str,
        description: str | None = None,
        task_type: TaskType = "task",
        priority: int | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
        design: str | None = None,
        acceptance: list[str] | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title.
            description: Optional task description.
            task_type: Type of task (bug, feature, task, epic, chore).
            priority: Optional priority (1-5, 1 is highest).
            epic_id: Optional parent epic ID.
            labels: Optional list of labels.
            design: Optional design/architecture notes.
            acceptance: Optional list of acceptance criteria.

        Returns:
            The created task.
        """
        ...

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            The task.

        Raises:
            KeyError: If task not found.
        """
        ...

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
        ...

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
        ...

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None:
        """Get the next task ready to be worked on.

        A task is ready if it has no unresolved blocking dependencies.

        Args:
            epic_id: Optional epic filter.

        Returns:
            The next ready task, or None if no tasks are ready.
        """
        ...

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Add a dependency between tasks.

        Args:
            task_id: The task that depends on another.
            depends_on_id: The task being depended upon.
        """
        ...

    def close_task(self, task_id: str, reason: str | None = None) -> None:
        """Close a task.

        Args:
            task_id: The task to close.
            reason: Optional reason for closing.
        """
        ...
