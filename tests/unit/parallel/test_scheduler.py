"""Tests for task scheduling system."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jiro.parallel.scheduler import (
    ExecutingTask,
    TaskHandle,
    TaskScheduler,
    TaskStatus,
)
from jiro.parallel.worktree import WorktreeManager


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    @pytest.mark.unit
    def test_task_status_values(self) -> None:
        """Should have all expected status values."""
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    @pytest.mark.unit
    def test_task_status_enum_members(self) -> None:
        """Should have all required enum members."""
        statuses = {status.name for status in TaskStatus}
        assert "QUEUED" in statuses
        assert "RUNNING" in statuses
        assert "COMPLETED" in statuses
        assert "FAILED" in statuses


class TestTaskHandle:
    """Tests for TaskHandle dataclass."""

    @pytest.mark.unit
    def test_task_handle_creation(self) -> None:
        """Should create TaskHandle with required fields."""
        queued_at = datetime(2025, 1, 1, 12, 0, 0)
        handle = TaskHandle(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            queued_at=queued_at,
        )

        assert handle.task_id == "task-123"
        assert handle.status == TaskStatus.QUEUED
        assert handle.queued_at == queued_at

    @pytest.mark.unit
    def test_task_handle_status_update(self) -> None:
        """Should allow status updates."""
        handle = TaskHandle(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            queued_at=datetime.now(),
        )

        handle.status = TaskStatus.RUNNING
        assert handle.status == TaskStatus.RUNNING


class TestExecutingTask:
    """Tests for ExecutingTask dataclass."""

    @pytest.mark.unit
    def test_executing_task_creation(self, tmp_path: Path) -> None:
        """Should create ExecutingTask with required fields."""
        started_at = datetime(2025, 1, 1, 12, 0, 0)
        worktree_path = tmp_path / "worktree"
        executing_task = ExecutingTask(
            task_id="task-123",
            worktree_path=worktree_path,
            started_at=started_at,
        )

        assert executing_task.task_id == "task-123"
        assert executing_task.worktree_path == worktree_path
        assert executing_task.started_at == started_at

    @pytest.mark.unit
    def test_executing_task_fields(self, tmp_path: Path) -> None:
        """Should have all required fields."""
        task = ExecutingTask(
            task_id="task-1",
            worktree_path=tmp_path / "wt1",
            started_at=datetime.now(),
        )

        assert hasattr(task, "task_id")
        assert hasattr(task, "worktree_path")
        assert hasattr(task, "started_at")


class TestTaskScheduler:
    """Tests for TaskScheduler class."""

    @pytest.fixture
    def mock_worktree_manager(self) -> MagicMock:
        """Provide a mock WorktreeManager."""
        return MagicMock(spec=WorktreeManager)

    @pytest.fixture
    def scheduler(self, mock_worktree_manager: MagicMock) -> TaskScheduler:
        """Provide a TaskScheduler instance."""
        return TaskScheduler(mock_worktree_manager, max_parallel=2)

    @pytest.mark.unit
    def test_scheduler_initialization(self, mock_worktree_manager: MagicMock) -> None:
        """Should initialize with worktree manager and max parallel tasks."""
        scheduler = TaskScheduler(mock_worktree_manager, max_parallel=4)

        assert scheduler.worktree_manager == mock_worktree_manager
        assert scheduler.max_parallel_tasks == 4

    @pytest.mark.unit
    def test_scheduler_default_max_parallel(self, mock_worktree_manager: MagicMock) -> None:
        """Should use default max_parallel of 4."""
        scheduler = TaskScheduler(mock_worktree_manager)

        assert scheduler.max_parallel_tasks == 4

    @pytest.mark.unit
    def test_queue_task_returns_handle(self, scheduler: TaskScheduler) -> None:
        """Should queue task and return handle."""
        task_id = "task-123"

        handle = scheduler.queue_task(task_id)

        assert handle.task_id == task_id
        assert handle.status == TaskStatus.QUEUED
        assert handle.queued_at is not None

    @pytest.mark.unit
    def test_queue_task_adds_to_queue(self, scheduler: TaskScheduler) -> None:
        """Should add task to pending queue."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        # Verify task is in queue by checking pending tasks
        pending = [t for t in scheduler.pending_queue if t.task_id == task_id]
        assert len(pending) == 1

    @pytest.mark.unit
    def test_queue_multiple_tasks(self, scheduler: TaskScheduler) -> None:
        """Should queue multiple tasks in order."""
        task_ids = ["task-1", "task-2", "task-3"]

        handles = [scheduler.queue_task(task_id) for task_id in task_ids]

        assert len(handles) == 3
        assert [h.task_id for h in handles] == task_ids

    @pytest.mark.unit
    def test_dispatch_next_with_available_slot(self, scheduler: TaskScheduler) -> None:
        """Should dispatch task when worktree slot available."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        executing = scheduler.dispatch_next()

        assert executing is not None
        assert executing.task_id == task_id
        assert executing.worktree_path == mock_worktree_path
        scheduler.worktree_manager.create_worktree.assert_called_once()

    @pytest.mark.unit
    def test_dispatch_next_with_no_pending_tasks(self, scheduler: TaskScheduler) -> None:
        """Should return None when no pending tasks."""
        executing = scheduler.dispatch_next()

        assert executing is None

    @pytest.mark.unit
    def test_dispatch_next_respects_max_parallel(self, scheduler: TaskScheduler) -> None:
        """Should not dispatch more than max_parallel tasks."""
        # Queue 5 tasks
        for i in range(5):
            scheduler.queue_task(f"task-{i}")

        mock_worktree_path = Path("/tmp/worktree")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        # Dispatch tasks up to max_parallel
        executing_tasks = []
        for _ in range(3):
            executing = scheduler.dispatch_next()
            if executing:
                executing_tasks.append(executing)

        # Should only dispatch up to max_parallel (2)
        assert len(executing_tasks) == 2

    @pytest.mark.unit
    def test_dispatch_next_removes_from_queue(self, scheduler: TaskScheduler) -> None:
        """Should remove task from pending queue after dispatch."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        executing = scheduler.dispatch_next()

        assert executing is not None
        # Verify task no longer in pending queue
        pending = [t for t in scheduler.pending_queue if t.task_id == task_id]
        assert len(pending) == 0

    @pytest.mark.unit
    def test_complete_task_success(self, scheduler: TaskScheduler) -> None:
        """Should mark task as completed and clean up worktree."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path
        scheduler.worktree_manager.cleanup_worktree.return_value = True

        executing = scheduler.dispatch_next()
        assert executing is not None

        result = scheduler.complete_task(task_id, success=True)

        assert result is True
        scheduler.worktree_manager.cleanup_worktree.assert_called()
        status = scheduler.get_status(task_id)
        assert status == TaskStatus.COMPLETED

    @pytest.mark.unit
    def test_complete_task_failure(self, scheduler: TaskScheduler) -> None:
        """Should mark task as failed and clean up worktree."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path
        scheduler.worktree_manager.cleanup_worktree.return_value = True

        executing = scheduler.dispatch_next()
        assert executing is not None

        result = scheduler.complete_task(task_id, success=False)

        assert result is True
        status = scheduler.get_status(task_id)
        assert status == TaskStatus.FAILED

    @pytest.mark.unit
    def test_complete_task_nonexistent(self, scheduler: TaskScheduler) -> None:
        """Should handle completion of nonexistent task gracefully."""
        result = scheduler.complete_task("nonexistent-task", success=True)

        assert result is False

    @pytest.mark.unit
    def test_get_status_queued(self, scheduler: TaskScheduler) -> None:
        """Should return QUEUED status for queued task."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        status = scheduler.get_status(task_id)

        assert status == TaskStatus.QUEUED

    @pytest.mark.unit
    def test_get_status_running(self, scheduler: TaskScheduler) -> None:
        """Should return RUNNING status for dispatched task."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        executing = scheduler.dispatch_next()
        assert executing is not None

        status = scheduler.get_status(task_id)

        assert status == TaskStatus.RUNNING

    @pytest.mark.unit
    def test_get_status_completed(self, scheduler: TaskScheduler) -> None:
        """Should return COMPLETED status after task completion."""
        task_id = "task-123"
        scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path
        scheduler.worktree_manager.cleanup_worktree.return_value = True

        executing = scheduler.dispatch_next()
        assert executing is not None

        scheduler.complete_task(task_id, success=True)

        status = scheduler.get_status(task_id)

        assert status == TaskStatus.COMPLETED

    @pytest.mark.unit
    def test_get_status_nonexistent(self, scheduler: TaskScheduler) -> None:
        """Should raise exception for nonexistent task."""
        with pytest.raises(ValueError, match="Task not found"):
            scheduler.get_status("nonexistent-task")

    @pytest.mark.unit
    def test_get_running_tasks_empty(self, scheduler: TaskScheduler) -> None:
        """Should return empty list when no tasks running."""
        running = scheduler.get_running_tasks()

        assert running == []

    @pytest.mark.unit
    def test_get_running_tasks_with_executing_tasks(self, scheduler: TaskScheduler) -> None:
        """Should return list of executing tasks."""
        task_ids = ["task-1", "task-2"]
        for task_id in task_ids:
            scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        # Dispatch first task
        executing1 = scheduler.dispatch_next()
        assert executing1 is not None

        running = scheduler.get_running_tasks()

        assert len(running) == 1
        assert running[0].task_id == task_ids[0]

    @pytest.mark.unit
    def test_get_running_tasks_multiple(self, scheduler: TaskScheduler) -> None:
        """Should return multiple running tasks."""
        task_ids = ["task-1", "task-2"]
        for task_id in task_ids:
            scheduler.queue_task(task_id)

        mock_worktree_path = Path("/tmp/worktree")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        # Dispatch both tasks
        executing1 = scheduler.dispatch_next()
        executing2 = scheduler.dispatch_next()

        assert executing1 is not None
        assert executing2 is not None

        running = scheduler.get_running_tasks()

        assert len(running) == 2
        running_ids = [t.task_id for t in running]
        assert all(task_id in running_ids for task_id in task_ids)

    @pytest.mark.unit
    def test_get_max_parallel_tasks(self, scheduler: TaskScheduler) -> None:
        """Should return configured max parallel tasks."""
        assert scheduler.get_max_parallel_tasks() == 2

    @pytest.mark.unit
    def test_get_max_parallel_tasks_default(self, mock_worktree_manager: MagicMock) -> None:
        """Should return default max parallel tasks."""
        scheduler = TaskScheduler(mock_worktree_manager)

        assert scheduler.get_max_parallel_tasks() == 4

    @pytest.mark.unit
    def test_queue_and_dispatch_workflow(self, scheduler: TaskScheduler) -> None:
        """Should handle complete queue and dispatch workflow."""
        # Queue multiple tasks
        handles = []
        for i in range(3):
            handle = scheduler.queue_task(f"task-{i}")
            handles.append(handle)
            assert handle.status == TaskStatus.QUEUED

        # Dispatch tasks up to limit
        mock_worktree_path = Path("/tmp/worktree")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        executing1 = scheduler.dispatch_next()
        assert executing1 is not None
        assert executing1.task_id == "task-0"

        executing2 = scheduler.dispatch_next()
        assert executing2 is not None
        assert executing2.task_id == "task-1"

        # Should not dispatch more than max
        executing3 = scheduler.dispatch_next()
        assert executing3 is None

        # Complete one task
        scheduler.worktree_manager.cleanup_worktree.return_value = True
        scheduler.complete_task("task-0", success=True)

        # Now should be able to dispatch the third task
        executing3 = scheduler.dispatch_next()
        assert executing3 is not None
        assert executing3.task_id == "task-2"

    @pytest.mark.unit
    def test_task_handle_stores_queued_time(self, scheduler: TaskScheduler) -> None:
        """Should store when task was queued."""
        before_queue = datetime.now()
        handle = scheduler.queue_task("task-123")
        after_queue = datetime.now()

        assert before_queue <= handle.queued_at <= after_queue

    @pytest.mark.unit
    def test_executing_task_stores_start_time(self, scheduler: TaskScheduler) -> None:
        """Should store when task started executing."""
        scheduler.queue_task("task-123")
        mock_worktree_path = Path("/tmp/worktree/task-123")
        scheduler.worktree_manager.create_worktree.return_value = mock_worktree_path

        before_dispatch = datetime.now()
        executing = scheduler.dispatch_next()
        after_dispatch = datetime.now()

        assert executing is not None
        assert before_dispatch <= executing.started_at <= after_dispatch
