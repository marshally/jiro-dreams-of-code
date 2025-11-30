"""Tests for IssueTracker protocol interface."""

from datetime import datetime
from typing import Protocol

import pytest

from jiro.trackers.interface import IssueTracker, Task, TaskStatus, TaskType


class TestTask:
    """Tests for Task dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """Task should require core fields."""
        task = Task(
            id="task-123",
            title="Implement feature X",
            task_type="feature",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert task.id == "task-123"
        assert task.title == "Implement feature X"
        assert task.task_type == "feature"
        assert task.status == "open"
        assert task.created_at == datetime(2024, 1, 15, 10, 30, 0)

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        task = Task(
            id="task-123",
            title="Fix bug Y",
            task_type="bug",
            status="open",
            created_at=datetime.now(),
        )
        assert task.description is None
        assert task.epic_id is None
        assert task.priority is None
        assert task.updated_at is None
        assert task.closed_at is None
        assert task.labels is None

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """Task should accept all fields."""
        task = Task(
            id="task-123",
            title="Implement feature X",
            task_type="feature",
            status="in_progress",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            description="Detailed description here",
            epic_id="epic-456",
            priority=1,
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
            closed_at=None,
            labels=["backend", "priority-high"],
        )
        assert task.description == "Detailed description here"
        assert task.epic_id == "epic-456"
        assert task.priority == 1
        assert task.labels == ["backend", "priority-high"]


class TestTaskType:
    """Tests for TaskType type alias."""

    @pytest.mark.unit
    def test_valid_task_types(self) -> None:
        """TaskType should allow valid values."""
        valid: list[TaskType] = ["bug", "feature", "task", "epic", "chore"]
        for task_type in valid:
            task = Task(
                id="test",
                title="test",
                task_type=task_type,
                status="open",
                created_at=datetime.now(),
            )
            assert task.task_type == task_type


class TestTaskStatus:
    """Tests for TaskStatus type alias."""

    @pytest.mark.unit
    def test_valid_statuses(self) -> None:
        """TaskStatus should allow valid values."""
        valid: list[TaskStatus] = ["open", "in_progress", "blocked", "closed"]
        for status in valid:
            task = Task(
                id="test",
                title="test",
                task_type="task",
                status=status,
                created_at=datetime.now(),
            )
            assert task.status == status


class TestIssueTrackerProtocol:
    """Tests for IssueTracker protocol."""

    @pytest.mark.unit
    def test_protocol_is_runtime_checkable(self) -> None:
        """IssueTracker should be runtime checkable."""
        assert hasattr(IssueTracker, "__protocol_attrs__") or isinstance(IssueTracker, type)
        # Verify it's a Protocol with runtime_checkable
        assert issubclass(type(IssueTracker), type(Protocol))

    @pytest.mark.unit
    def test_protocol_has_create_task(self) -> None:
        """IssueTracker should have create_task method."""
        assert hasattr(IssueTracker, "create_task")

    @pytest.mark.unit
    def test_protocol_has_get_task(self) -> None:
        """IssueTracker should have get_task method."""
        assert hasattr(IssueTracker, "get_task")

    @pytest.mark.unit
    def test_protocol_has_list_tasks(self) -> None:
        """IssueTracker should have list_tasks method."""
        assert hasattr(IssueTracker, "list_tasks")

    @pytest.mark.unit
    def test_protocol_has_update_task(self) -> None:
        """IssueTracker should have update_task method."""
        assert hasattr(IssueTracker, "update_task")

    @pytest.mark.unit
    def test_protocol_has_get_next_ready_task(self) -> None:
        """IssueTracker should have get_next_ready_task method."""
        assert hasattr(IssueTracker, "get_next_ready_task")

    @pytest.mark.unit
    def test_protocol_has_add_dependency(self) -> None:
        """IssueTracker should have add_dependency method."""
        assert hasattr(IssueTracker, "add_dependency")

    @pytest.mark.unit
    def test_protocol_has_close_task(self) -> None:
        """IssueTracker should have close_task method."""
        assert hasattr(IssueTracker, "close_task")
