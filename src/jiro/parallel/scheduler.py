"""Task scheduling system for parallel task execution.

This module provides functionality for scheduling tasks to run in parallel
using git worktrees, with resource limits and execution tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from jiro.parallel.worktree import WorktreeManager


class TaskStatus(Enum):
    """Status of a task in the scheduling system."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskHandle:
    """Handle to track a queued task.

    Attributes:
        task_id: Unique identifier for the task.
        status: Current status of the task.
        queued_at: Timestamp when the task was queued.
    """

    task_id: str
    status: TaskStatus
    queued_at: datetime


@dataclass
class ExecutingTask:
    """Information about a currently executing task.

    Attributes:
        task_id: Unique identifier for the task.
        worktree_path: Path to the worktree where task is executing.
        started_at: Timestamp when the task started executing.
    """

    task_id: str
    worktree_path: Path
    started_at: datetime


class TaskScheduler:
    """Manages scheduling and execution of tasks with resource limits.

    Coordinates task dispatch to available worktrees, tracks execution
    progress, and enforces resource limits (max concurrent tasks).
    """

    def __init__(self, worktree_manager: WorktreeManager, max_parallel: int = 4) -> None:
        """Initialize the TaskScheduler.

        Args:
            worktree_manager: WorktreeManager instance for worktree operations.
            max_parallel: Maximum number of tasks to run in parallel. Defaults to 4.
        """
        self.worktree_manager = worktree_manager
        self.max_parallel_tasks = max_parallel

        # Queue of pending tasks
        self.pending_queue: list[TaskHandle] = []

        # Map of task_id to executing task info
        self.executing_tasks: dict[str, ExecutingTask] = {}

        # Map of task_id to final status
        self.completed_tasks: dict[str, TaskStatus] = {}

    def queue_task(self, task_id: str) -> TaskHandle:
        """Queue a task for execution.

        Args:
            task_id: Unique identifier for the task.

        Returns:
            TaskHandle for tracking the queued task.
        """
        handle = TaskHandle(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            queued_at=datetime.now(),
        )
        self.pending_queue.append(handle)
        return handle

    def dispatch_next(self) -> ExecutingTask | None:
        """Dispatch the next available task to a worktree.

        Creates a new worktree and starts executing the next task in the queue,
        if a slot is available (respecting max_parallel limit).

        Returns:
            ExecutingTask if a task was dispatched, None if no tasks available
            or slots are full.
        """
        # Check if we have room for more tasks
        if len(self.executing_tasks) >= self.max_parallel_tasks:
            return None

        # Check if there are pending tasks
        if not self.pending_queue:
            return None

        # Get the next task from the queue
        handle = self.pending_queue.pop(0)

        # Create a worktree for this task
        worktree_path = self.worktree_manager.create_worktree(handle.task_id)

        # Create executing task record
        executing_task = ExecutingTask(
            task_id=handle.task_id,
            worktree_path=worktree_path,
            started_at=datetime.now(),
        )

        # Track the executing task
        self.executing_tasks[handle.task_id] = executing_task

        return executing_task

    def complete_task(self, task_id: str, success: bool = True) -> bool:
        """Mark a task as completed and clean up resources.

        Args:
            task_id: ID of the task to complete.
            success: Whether the task completed successfully. Defaults to True.

        Returns:
            True if task was found and cleaned up, False otherwise.
        """
        if task_id not in self.executing_tasks:
            return False

        # Get the executing task info
        executing_task = self.executing_tasks[task_id]

        # Clean up the worktree
        self.worktree_manager.cleanup_worktree(executing_task.worktree_path)

        # Determine final status
        final_status = TaskStatus.COMPLETED if success else TaskStatus.FAILED

        # Remove from executing and add to completed
        del self.executing_tasks[task_id]
        self.completed_tasks[task_id] = final_status

        return True

    def get_status(self, task_id: str) -> TaskStatus:
        """Get the current status of a task.

        Args:
            task_id: ID of the task to query.

        Returns:
            TaskStatus for the task.

        Raises:
            ValueError: If task ID is not found.
        """
        # Check if task is queued
        for handle in self.pending_queue:
            if handle.task_id == task_id:
                return TaskStatus.QUEUED

        # Check if task is executing
        if task_id in self.executing_tasks:
            return TaskStatus.RUNNING

        # Check if task is completed
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]

        # Task not found
        raise ValueError(f"Task not found: {task_id}")

    def get_running_tasks(self) -> list[ExecutingTask]:
        """Get list of currently executing tasks.

        Returns:
            List of ExecutingTask objects for all running tasks.
        """
        return list(self.executing_tasks.values())

    def get_max_parallel_tasks(self) -> int:
        """Get the maximum number of parallel tasks allowed.

        Returns:
            Maximum number of concurrent tasks.
        """
        return self.max_parallel_tasks
