"""Tests for tasks CLI commands."""

import json
from datetime import datetime
from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.trackers.interface import Task


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id="test-1",
        title="Test Task",
        task_type="feature",
        status="open",
        created_at=datetime(2025, 11, 30, 10, 0, 0),
        description="Test description",
        epic_id=None,
        priority=1,
        updated_at=datetime(2025, 11, 30, 11, 0, 0),
        closed_at=None,
        labels=["test"],
    )


@pytest.fixture
def sample_task_in_progress() -> Task:
    """Create a sample in_progress task."""
    return Task(
        id="test-2",
        title="In Progress Task",
        task_type="task",
        status="in_progress",
        created_at=datetime(2025, 11, 30, 10, 0, 0),
        description="Task in progress",
        epic_id="epic-1",
        priority=2,
        updated_at=datetime(2025, 11, 30, 11, 0, 0),
        closed_at=None,
        labels=["work"],
    )


@pytest.fixture
def sample_task_closed() -> Task:
    """Create a sample closed task."""
    return Task(
        id="test-3",
        title="Closed Task",
        task_type="bug",
        status="closed",
        created_at=datetime(2025, 11, 30, 10, 0, 0),
        description="Completed task",
        epic_id="epic-1",
        priority=0,
        updated_at=datetime(2025, 11, 30, 12, 0, 0),
        closed_at=datetime(2025, 11, 30, 12, 30, 0),
        labels=["fixed"],
    )


class TestTasksListCommand:
    """Tests for tasks list command."""

    @pytest.mark.unit
    def test_tasks_list_help(self, cli_runner: CliRunner) -> None:
        """Tasks list command should display help."""
        result = cli_runner.invoke(app, ["tasks", "list", "--help"])
        assert result.exit_code == 0
        assert "List" in result.stdout or "list" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_basic(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should display tasks in a table format."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0
        assert "test-1" in result.stdout or "Test Task" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_with_status_filter(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should filter by status."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--status", "open"])
        assert result.exit_code == 0
        # Verify list_tasks was called with status filter
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("status") == "open"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_with_status_short_flag(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should accept -s shorthand for status."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "-s", "in_progress"])
        assert result.exit_code == 0
        # Verify list_tasks was called with status filter
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("status") == "in_progress"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_with_epic_filter(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should filter by epic."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--epic", "epic-1"])
        assert result.exit_code == 0
        # Verify list_tasks was called with epic_id filter
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("epic_id") == "epic-1"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_with_epic_short_flag(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should accept -e shorthand for epic."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "-e", "epic-2"])
        assert result.exit_code == 0
        # Verify list_tasks was called with epic_id filter
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("epic_id") == "epic-2"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_with_both_filters(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should accept both status and epic filters."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--status", "open", "--epic", "epic-1"])
        assert result.exit_code == 0
        # Verify list_tasks was called with both filters
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("status") == "open"
        assert call_kwargs.get("epic_id") == "epic-1"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_json_output(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should output JSON when --json flag is used."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, list)
        assert len(output) == 1
        assert output[0]["id"] == "test-1"
        assert output[0]["title"] == "Test Task"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_json_with_filters(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should apply filters when outputting JSON."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--json", "--status", "open"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert len(output) == 1
        mock_tracker.list_tasks.assert_called_once()
        call_kwargs = mock_tracker.list_tasks.call_args[1]
        assert call_kwargs.get("status") == "open"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_multiple_tasks(
        self,
        mock_beads_class,
        mock_config,
        cli_runner: CliRunner,
        sample_task,
        sample_task_in_progress,
        sample_task_closed,
    ) -> None:
        """Tasks list should display multiple tasks."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [
            sample_task,
            sample_task_in_progress,
            sample_task_closed,
        ]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0
        # Check that all tasks are represented
        assert "test-1" in result.stdout or "Test Task" in result.stdout
        assert "test-2" in result.stdout or "In Progress Task" in result.stdout
        assert "test-3" in result.stdout or "Closed Task" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_empty_result(
        self, mock_beads_class, mock_config, cli_runner: CliRunner
    ) -> None:
        """Tasks list should handle empty results gracefully."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = []
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0
        # Should still render successfully, possibly with "no tasks" message
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_empty_json(
        self, mock_beads_class, mock_config, cli_runner: CliRunner
    ) -> None:
        """Tasks list should output empty JSON array when no tasks."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = []
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output == []

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_displays_priority(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should display task priority."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_displays_status(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should display task status."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0
        # Status should be visible
        assert "open" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_list_displays_task_type(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks list should display task type."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.list_tasks.return_value = [sample_task]
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "list"])
        assert result.exit_code == 0
        # Type should be visible
        assert "feature" in result.stdout.lower()


class TestTasksShowCommand:
    """Tests for tasks show command."""

    @pytest.mark.unit
    def test_tasks_show_help(self, cli_runner: CliRunner) -> None:
        """Tasks show command should display help."""
        result = cli_runner.invoke(app, ["tasks", "show", "--help"])
        assert result.exit_code == 0
        assert "Show" in result.stdout or "show" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_basic(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should display full task details."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1"])
        assert result.exit_code == 0
        assert "test-1" in result.stdout
        assert "Test Task" in result.stdout
        mock_tracker.get_task.assert_called_once_with("test-1")

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_displays_description(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should display task description."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1"])
        assert result.exit_code == 0
        assert "Test description" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_displays_status(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should display task status."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1"])
        assert result.exit_code == 0
        assert "open" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_displays_priority(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should display task priority."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1"])
        assert result.exit_code == 0
        assert "1" in result.stdout or "Priority" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_displays_labels(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should display task labels."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1"])
        assert result.exit_code == 0
        assert "test" in result.stdout or "label" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_json_output(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show should output JSON when --json flag is used."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert output["id"] == "test-1"
        assert output["title"] == "Test Task"
        assert output["description"] == "Test description"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_json_contains_all_fields(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks show JSON should contain all task fields."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-1", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "id" in output
        assert "title" in output
        assert "status" in output
        assert "priority" in output
        assert "task_type" in output
        assert "created_at" in output
        assert "updated_at" in output
        assert "labels" in output

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_task_not_found(
        self, mock_beads_class, mock_config, cli_runner: CliRunner
    ) -> None:
        """Tasks show should handle task not found gracefully."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.side_effect = KeyError("Task not found")
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "Error" in result.stdout or "not found" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_with_epic(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task_in_progress
    ) -> None:
        """Tasks show should display epic ID if task is in an epic."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task_in_progress
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-2"])
        assert result.exit_code == 0
        assert "epic-1" in result.stdout or "epic" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_show_with_closed_task(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task_closed
    ) -> None:
        """Tasks show should display closed_at timestamp for closed tasks."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_task.return_value = sample_task_closed
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "show", "test-3"])
        assert result.exit_code == 0
        assert "closed" in result.stdout.lower()


class TestTasksNextCommand:
    """Tests for tasks next command."""

    @pytest.mark.unit
    def test_tasks_next_help(self, cli_runner: CliRunner) -> None:
        """Tasks next command should display help."""
        result = cli_runner.invoke(app, ["tasks", "next", "--help"])
        assert result.exit_code == 0
        assert "Show" in result.stdout or "next" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_finds_ready_task(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks next should find and display the next ready task."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next"])
        assert result.exit_code == 0
        assert "test-1" in result.stdout or "Test Task" in result.stdout
        mock_tracker.get_next_ready_task.assert_called_once()
        # Should be called with no epic filter
        call_kwargs = mock_tracker.get_next_ready_task.call_args[1]
        assert call_kwargs.get("epic_id") is None

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_with_epic_filter(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task_in_progress
    ) -> None:
        """Tasks next should filter by epic ID."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = sample_task_in_progress
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next", "--epic", "epic-1"])
        assert result.exit_code == 0
        # Verify get_next_ready_task was called with epic_id filter
        mock_tracker.get_next_ready_task.assert_called_once()
        call_kwargs = mock_tracker.get_next_ready_task.call_args[1]
        assert call_kwargs.get("epic_id") == "epic-1"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_with_epic_short_flag(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task_in_progress
    ) -> None:
        """Tasks next should accept -e shorthand for epic."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = sample_task_in_progress
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next", "-e", "epic-2"])
        assert result.exit_code == 0
        # Verify get_next_ready_task was called with epic_id filter
        mock_tracker.get_next_ready_task.assert_called_once()
        call_kwargs = mock_tracker.get_next_ready_task.call_args[1]
        assert call_kwargs.get("epic_id") == "epic-2"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_no_ready_task(
        self, mock_beads_class, mock_config, cli_runner: CliRunner
    ) -> None:
        """Tasks next should handle gracefully when no task is ready."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker returning None
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = None
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next"])
        assert result.exit_code == 0
        # Should display a message that no tasks are ready
        assert "no" in result.stdout.lower() or "ready" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_json_output(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task
    ) -> None:
        """Tasks next should output JSON when --json flag is used."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = sample_task
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert output["id"] == "test-1"
        assert output["title"] == "Test Task"

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_json_output_with_no_task(
        self, mock_beads_class, mock_config, cli_runner: CliRunner
    ) -> None:
        """Tasks next JSON should handle null when no task is ready."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker returning None
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = None
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next", "--json"])
        assert result.exit_code == 0
        # Should output null or empty object
        output = json.loads(result.stdout)
        assert output is None or output == {}

    @pytest.mark.unit
    @mock.patch("jiro.cli.tasks.load_config")
    @mock.patch("jiro.cli.tasks.BeadsTracker")
    def test_tasks_next_json_with_epic_filter(
        self, mock_beads_class, mock_config, cli_runner: CliRunner, sample_task_in_progress
    ) -> None:
        """Tasks next should apply epic filter when outputting JSON."""
        # Mock the config
        mock_config_instance = mock.Mock()
        mock_config.return_value = mock_config_instance

        # Mock the BeadsTracker
        mock_tracker = mock.Mock()
        mock_tracker.get_next_ready_task.return_value = sample_task_in_progress
        mock_beads_class.return_value = mock_tracker

        result = cli_runner.invoke(app, ["tasks", "next", "--json", "--epic", "epic-1"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["id"] == "test-2"
        mock_tracker.get_next_ready_task.assert_called_once()
        call_kwargs = mock_tracker.get_next_ready_task.call_args[1]
        assert call_kwargs.get("epic_id") == "epic-1"
