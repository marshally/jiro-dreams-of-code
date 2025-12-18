"""Tests for TOON formatter."""

from datetime import datetime

import pytest

from jiro.formatters.toon import ToonFormatter
from jiro.trackers.interface import Task


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id="task-001",
        title="Implement feature X",
        task_type="feature",
        status="open",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        description="This is a feature task",
        epic_id="epic-001",
        priority=2,
        updated_at=datetime(2024, 1, 16, 14, 45, 0),
        closed_at=None,
        labels=["backend", "enhancement"],
    )


@pytest.fixture
def sample_task_minimal() -> Task:
    """Create a minimal task for testing."""
    return Task(
        id="task-002",
        title="Simple task",
        task_type="task",
        status="closed",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        description=None,
        epic_id=None,
        priority=None,
        updated_at=None,
        closed_at=datetime(2024, 1, 20, 16, 0, 0),
        labels=None,
    )


class TestToonFormatterBasics:
    """Test basic TOON formatter functionality."""

    def test_format_single_task(self, sample_task: Task) -> None:
        """Test formatting a single task to TOON format."""
        formatter = ToonFormatter()
        result = formatter.format_task(sample_task)

        # Verify it contains the expected sections
        assert "[task]" in result
        assert "[/task]" in result
        assert "id: task-001" in result
        assert "title: Implement feature X" in result
        assert "task_type: feature" in result
        assert "status: open" in result
        assert "description: This is a feature task" in result

    def test_format_task_with_minimal_data(self, sample_task_minimal: Task) -> None:
        """Test formatting a task with minimal data."""
        formatter = ToonFormatter()
        result = formatter.format_task(sample_task_minimal)

        assert "[task]" in result
        assert "[/task]" in result
        assert "id: task-002" in result
        assert "title: Simple task" in result
        assert "status: closed" in result

    def test_format_task_list(self, sample_task: Task, sample_task_minimal: Task) -> None:
        """Test formatting multiple tasks."""
        formatter = ToonFormatter()
        tasks = [sample_task, sample_task_minimal]
        result = formatter.format_tasks(tasks)

        # Should contain both tasks
        assert result.count("[task]") == 2
        assert result.count("[/task]") == 2
        assert "task-001" in result
        assert "task-002" in result

    def test_format_empty_task_list(self) -> None:
        """Test formatting empty task list."""
        formatter = ToonFormatter()
        result = formatter.format_tasks([])

        # Should handle empty list gracefully
        assert isinstance(result, str)
        assert len(result) == 0 or "[task]" not in result

    def test_format_dict(self) -> None:
        """Test formatting a dictionary to TOON format."""
        formatter = ToonFormatter()
        data = {
            "session_id": "sess-123",
            "status": "running",
            "tasks_completed": 5,
            "tasks_total": 10,
            "progress_percent": 50.0,
        }
        result = formatter.format_dict(data, "session")

        assert "[session]" in result
        assert "[/session]" in result
        assert "session_id: sess-123" in result
        assert "status: running" in result
        assert "tasks_completed: 5" in result
        assert "progress_percent: 50.0" in result

    def test_format_list_of_dicts(self) -> None:
        """Test formatting a list of dictionaries."""
        formatter = ToonFormatter()
        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]
        result = formatter.format_list(data, "user")

        assert result.count("[user]") == 2
        assert result.count("[/user]") == 2
        assert "id: 1" in result
        assert "name: Alice" in result
        assert "id: 2" in result
        assert "name: Bob" in result

    def test_toon_format_structure(self, sample_task: Task) -> None:
        """Test that TOON format has correct structure."""
        formatter = ToonFormatter()
        result = formatter.format_task(sample_task)
        lines = result.split("\n")

        # First line should be opening tag
        assert lines[0].strip() == "[task]"
        # Last non-empty line should be closing tag
        last_non_empty = [line for line in lines if line.strip()][-1]
        assert last_non_empty.strip() == "[/task]"

    def test_timestamps_in_toon_format(self, sample_task: Task) -> None:
        """Test that timestamps are properly formatted in TOON."""
        formatter = ToonFormatter()
        result = formatter.format_task(sample_task)

        # Timestamps should be in ISO format
        assert "2024-01-15" in result
        assert "2024-01-16" in result


class TestToonFormatterEdgeCases:
    """Test edge cases and special characters."""

    def test_special_characters_in_values(self) -> None:
        """Test handling of special characters in field values."""
        formatter = ToonFormatter()
        task = Task(
            id="task-special",
            title="Task with: colons and [brackets] and newlines",
            task_type="feature",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            description="Description with\nmultiple\nlines",
        )
        result = formatter.format_task(task)

        # Should handle special characters gracefully
        assert "task-special" in result
        assert "Task with: colons and [brackets]" in result

    def test_none_values_handling(self) -> None:
        """Test that None values are handled appropriately."""
        formatter = ToonFormatter()
        task = Task(
            id="task-none",
            title="Task with nones",
            task_type="feature",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            description=None,
            epic_id=None,
            priority=None,
            labels=None,
        )
        result = formatter.format_task(task)

        assert "[task]" in result
        assert "[/task]" in result
        assert "id: task-none" in result

    def test_multiline_description(self) -> None:
        """Test handling of multiline descriptions."""
        formatter = ToonFormatter()
        description = """This is a multiline description.

It has multiple paragraphs.

And continues here."""
        task = Task(
            id="task-multiline",
            title="Test",
            task_type="task",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            description=description,
        )
        result = formatter.format_task(task)

        assert "task-multiline" in result

    def test_large_list_formatting(self) -> None:
        """Test formatting a large list of items."""
        formatter = ToonFormatter()
        tasks = [
            Task(
                id=f"task-{i}",
                title=f"Task {i}",
                task_type="task",
                status="open",
                created_at=datetime(2024, 1, 15, 10, 30, 0),
            )
            for i in range(100)
        ]
        result = formatter.format_tasks(tasks)

        assert result.count("[task]") == 100
        assert result.count("[/task]") == 100


class TestToonFormatterDataTypes:
    """Test handling of different data types."""

    def test_numeric_values(self) -> None:
        """Test formatting of numeric values."""
        formatter = ToonFormatter()
        data = {
            "integer": 42,
            "float": 3.14159,
            "zero": 0,
            "negative": -5,
        }
        result = formatter.format_dict(data, "numbers")

        assert "integer: 42" in result
        assert "float: 3.14159" in result
        assert "zero: 0" in result
        assert "negative: -5" in result

    def test_boolean_values(self) -> None:
        """Test formatting of boolean values."""
        formatter = ToonFormatter()
        data = {
            "is_active": True,
            "is_deleted": False,
        }
        result = formatter.format_dict(data, "flags")

        assert "is_active:" in result and ("True" in result or "true" in result)
        assert "is_deleted:" in result and ("False" in result or "false" in result)

    def test_list_values(self) -> None:
        """Test formatting of list values."""
        formatter = ToonFormatter()
        data = {
            "labels": ["bug", "feature", "enhancement"],
            "tags": ["python", "testing"],
        }
        result = formatter.format_dict(data, "metadata")

        assert "labels:" in result
        assert "tags:" in result
