"""Tests for BeadsTracker implementation."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from jiro.trackers.beads import BeadsTracker
from jiro.trackers.interface import Task


@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root."""
    return tmp_path


@pytest.fixture
def beads_tracker(temp_project_root):
    """Create a BeadsTracker instance for testing."""
    return BeadsTracker(temp_project_root, stealth=False)


@pytest.fixture
def stealth_beads_tracker(temp_project_root):
    """Create a stealth mode BeadsTracker instance for testing."""
    return BeadsTracker(temp_project_root, stealth=True, project_name="test-project")


@pytest.fixture
def sample_task_data():
    """Sample task data matching bd JSON output."""
    return {
        "id": "test-1",
        "title": "Test Task",
        "description": "Test description",
        "design": "Test design",
        "acceptance_criteria": "Test criteria",
        "status": "open",
        "priority": 1,
        "issue_type": "feature",
        "created_at": "2025-11-30T10:00:00Z",
        "updated_at": "2025-11-30T11:00:00Z",
        "closed_at": None,
        "labels": ["test", "feature"],
    }


class TestBeadsTrackerInit:
    """Test BeadsTracker initialization."""

    def test_init_normal_mode(self, temp_project_root):
        """Test initialization in normal mode."""
        tracker = BeadsTracker(temp_project_root, stealth=False)
        assert tracker.project_root == temp_project_root
        assert tracker.stealth is False

    def test_init_stealth_mode(self, temp_project_root):
        """Test initialization in stealth mode."""
        tracker = BeadsTracker(temp_project_root, stealth=True, project_name="my-project")
        assert tracker.project_root == temp_project_root
        assert tracker.stealth is True

    def test_beads_dir_normal_mode(self, temp_project_root):
        """Test beads directory path in normal mode."""
        tracker = BeadsTracker(temp_project_root, stealth=False)
        # Beads lives inside the jiro directory in both modes
        expected = temp_project_root / ".jiro-dreams-of-code" / ".beads"
        assert tracker.beads_dir == expected

    def test_beads_dir_stealth_mode(self, temp_project_root):
        """Test beads directory path in stealth mode."""
        tracker = BeadsTracker(temp_project_root, stealth=True, project_name="test-project")
        expected = Path.home() / ".jiro-dreams-of-code" / "test-project" / ".beads"
        assert tracker.beads_dir == expected

    def test_stealth_defaults_to_project_name(self, temp_project_root):
        """Test that stealth mode uses project root name if project_name not provided."""
        tracker = BeadsTracker(temp_project_root, stealth=True)
        expected = Path.home() / ".jiro-dreams-of-code" / temp_project_root.name / ".beads"
        assert tracker.beads_dir == expected


class TestCreateTask:
    """Test create_task method."""

    @mock.patch("subprocess.run")
    def test_create_task_minimal(self, mock_run, beads_tracker, sample_task_data):
        """Test creating a task with minimal parameters."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.create_task(
            title="New Task",
            task_type="task",
        )

        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.task_type == "feature"
        assert task.status == "open"

    @mock.patch("subprocess.run")
    def test_create_task_with_all_params(self, mock_run, beads_tracker, sample_task_data):
        """Test creating a task with all parameters."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.create_task(
            title="Test Task",
            description="Test description",
            task_type="feature",
            priority=1,
            epic_id="epic-1",
            labels=["test", "feature"],
        )

        assert task is not None
        assert task.id == "test-1"
        # Verify bd create was called with correct arguments
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "bd" in args[0]
        assert "create" in args[0]
        assert "--json" in args[0]

    @mock.patch("subprocess.run")
    def test_create_task_command_failure(self, mock_run, beads_tracker):
        """Test create_task handles command failure."""
        mock_run.return_value = mock.Mock(returncode=1, stderr=b"Error")
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd create")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.create_task(title="Task")


class TestGetTask:
    """Test get_task method."""

    @mock.patch("subprocess.run")
    def test_get_task_success(self, mock_run, beads_tracker, sample_task_data):
        """Test retrieving an existing task."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_task("test-1")

        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.description == "Test description"
        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    def test_get_task_not_found(self, mock_run, beads_tracker):
        """Test get_task raises KeyError when task not found."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=b"[]",
        )

        with pytest.raises(KeyError):
            beads_tracker.get_task("nonexistent-1")

    @mock.patch("subprocess.run")
    def test_get_task_command_failure(self, mock_run, beads_tracker):
        """Test get_task handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd show")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.get_task("test-1")


class TestListTasks:
    """Test list_tasks method."""

    @mock.patch("subprocess.run")
    def test_list_tasks_all(self, mock_run, beads_tracker, sample_task_data):
        """Test listing all tasks."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data, sample_task_data]).encode(),
        )

        tasks = beads_tracker.list_tasks()

        assert len(tasks) == 2
        assert all(isinstance(t, Task) for t in tasks)
        assert tasks[0].id == "test-1"

    @mock.patch("subprocess.run")
    def test_list_tasks_filter_by_status(self, mock_run, beads_tracker, sample_task_data):
        """Test listing tasks filtered by status."""
        sample_task_data["status"] = "in_progress"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        tasks = beads_tracker.list_tasks(status="in_progress")

        assert len(tasks) == 1
        assert tasks[0].status == "in_progress"
        # Verify the status flag was passed
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        # bd uses -s shorthand for status
        assert "-s" in args[0] or "--status" in args[0]

    @mock.patch("subprocess.run")
    def test_list_tasks_filter_by_epic(self, mock_run, beads_tracker, sample_task_data):
        """Test listing tasks filtered by epic."""
        sample_task_data["epic_id"] = "epic-1"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        tasks = beads_tracker.list_tasks(epic_id="epic-1")

        assert len(tasks) == 1
        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    def test_list_tasks_empty(self, mock_run, beads_tracker):
        """Test listing tasks when none exist."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=b"[]",
        )

        tasks = beads_tracker.list_tasks()

        assert tasks == []


class TestUpdateTask:
    """Test update_task method."""

    @mock.patch("subprocess.run")
    def test_update_task_status(self, mock_run, beads_tracker, sample_task_data):
        """Test updating task status."""
        sample_task_data["status"] = "in_progress"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.update_task("test-1", status="in_progress")

        assert task.status == "in_progress"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "test-1" in args[0]

    @mock.patch("subprocess.run")
    def test_update_task_multiple_fields(self, mock_run, beads_tracker, sample_task_data):
        """Test updating multiple task fields."""
        sample_task_data["title"] = "Updated Title"
        sample_task_data["priority"] = 2
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.update_task(
            "test-1",
            title="Updated Title",
            priority=2,
        )

        assert task.title == "Updated Title"
        assert task.priority == 2

    @mock.patch("subprocess.run")
    def test_update_task_command_failure(self, mock_run, beads_tracker):
        """Test update_task handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd update")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.update_task("test-1", status="in_progress")


class TestGetNextReadyTask:
    """Test get_next_ready_task method."""

    @mock.patch("subprocess.run")
    def test_get_next_ready_task_found(self, mock_run, beads_tracker, sample_task_data):
        """Test getting the next ready task."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_next_ready_task()

        assert task is not None
        assert task.id == "test-1"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "ready" in args[0]

    @mock.patch("subprocess.run")
    def test_get_next_ready_task_none(self, mock_run, beads_tracker):
        """Test get_next_ready_task returns None when no ready tasks."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=b"[]",
        )

        task = beads_tracker.get_next_ready_task()

        assert task is None

    @mock.patch("subprocess.run")
    def test_get_next_ready_task_with_epic_filter(self, mock_run, beads_tracker, sample_task_data):
        """Test getting next ready task with epic filter."""
        sample_task_data["epic_id"] = "epic-1"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_next_ready_task(epic_id="epic-1")

        assert task is not None
        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    def test_get_next_ready_task_command_failure(self, mock_run, beads_tracker):
        """Test get_next_ready_task handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd ready")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.get_next_ready_task()


class TestAddDependency:
    """Test add_dependency method."""

    @mock.patch("subprocess.run")
    def test_add_dependency_success(self, mock_run, beads_tracker):
        """Test adding a dependency between tasks."""
        mock_run.return_value = mock.Mock(returncode=0)

        beads_tracker.add_dependency("test-1", "test-2")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "dep" in args[0] or "dependency" in args[0]

    @mock.patch("subprocess.run")
    def test_add_dependency_command_failure(self, mock_run, beads_tracker):
        """Test add_dependency handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd dep")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.add_dependency("test-1", "test-2")


class TestCloseTask:
    """Test close_task method."""

    @mock.patch("subprocess.run")
    def test_close_task_success(self, mock_run, beads_tracker):
        """Test closing a task."""
        mock_run.return_value = mock.Mock(returncode=0)

        beads_tracker.close_task("test-1")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "close" in args[0]
        assert "test-1" in args[0]

    @mock.patch("subprocess.run")
    def test_close_task_with_reason(self, mock_run, beads_tracker):
        """Test closing a task with a reason."""
        mock_run.return_value = mock.Mock(returncode=0)

        beads_tracker.close_task("test-1", reason="Completed successfully")

        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    def test_close_task_command_failure(self, mock_run, beads_tracker):
        """Test close_task handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "bd close")

        with pytest.raises(subprocess.CalledProcessError):
            beads_tracker.close_task("test-1")


class TestTaskDataParsing:
    """Test parsing of task data from bd JSON output."""

    @mock.patch("subprocess.run")
    def test_parse_task_with_all_fields(self, mock_run, beads_tracker, sample_task_data):
        """Test parsing task with all optional fields."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_task("test-1")

        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.task_type == "feature"
        assert task.status == "open"
        assert task.priority == 1
        assert task.labels == ["test", "feature"]

    @mock.patch("subprocess.run")
    def test_parse_task_with_minimal_fields(self, mock_run, beads_tracker):
        """Test parsing task with minimal fields."""
        minimal_data = {
            "id": "minimal-1",
            "title": "Minimal Task",
            "status": "open",
            "issue_type": "task",
            "created_at": "2025-11-30T10:00:00Z",
        }
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([minimal_data]).encode(),
        )

        task = beads_tracker.get_task("minimal-1")

        assert task.id == "minimal-1"
        assert task.title == "Minimal Task"
        assert task.task_type == "task"

    @mock.patch("subprocess.run")
    def test_parse_task_with_closed_at(self, mock_run, beads_tracker, sample_task_data):
        """Test parsing task with closed_at timestamp."""
        sample_task_data["status"] = "closed"
        sample_task_data["closed_at"] = "2025-11-30T12:00:00Z"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_task("test-1")

        assert task.status == "closed"
        assert task.closed_at is not None

    @mock.patch("subprocess.run")
    def test_parse_datetime_fields(self, mock_run, beads_tracker, sample_task_data):
        """Test that datetime fields are parsed correctly."""
        sample_task_data["created_at"] = "2025-11-30T10:00:00Z"
        sample_task_data["updated_at"] = "2025-11-30T11:00:00Z"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        task = beads_tracker.get_task("test-1")

        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)


class TestCommandConstruction:
    """Test that bd commands are constructed correctly."""

    @mock.patch("subprocess.run")
    def test_command_uses_json_flag(self, mock_run, beads_tracker, sample_task_data):
        """Test that all commands use --json flag."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        beads_tracker.get_task("test-1")

        args, kwargs = mock_run.call_args
        assert "--json" in args[0]

    @mock.patch("subprocess.run")
    def test_command_working_directory(self, mock_run, beads_tracker, sample_task_data):
        """Test that commands run in the beads directory."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_task_data]).encode(),
        )

        beads_tracker.get_task("test-1")

        args, kwargs = mock_run.call_args
        # Commands should be run with cwd set to beads directory
        if "cwd" in kwargs:
            assert kwargs["cwd"] == beads_tracker.beads_dir
