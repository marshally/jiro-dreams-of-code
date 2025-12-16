"""Tests for GitHubTracker implementation."""

import json
import subprocess
from unittest import mock

import pytest

from jiro.trackers.github import GitHubTracker
from jiro.trackers.interface import Task


@pytest.fixture
def github_tracker() -> GitHubTracker:
    """Create a GitHubTracker instance for testing."""
    return GitHubTracker(
        repo_owner="test-owner",
        repo_name="test-repo",
        github_token="test-token",
    )


@pytest.fixture
def sample_github_issue() -> dict:
    """Sample GitHub issue data."""
    return {
        "id": 1,
        "number": 123,
        "title": "Test Issue",
        "body": "Test description",
        "state": "open",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z",
        "closed_at": None,
        "labels": [{"name": "type:feature"}, {"name": "priority:1"}],
    }


class TestGitHubTrackerInit:
    """Test GitHubTracker initialization."""

    @pytest.mark.unit
    def test_init_with_token(self) -> None:
        """Test initialization with token."""
        tracker = GitHubTracker(
            repo_owner="owner",
            repo_name="repo",
            github_token="token123",
        )
        assert tracker.repo_owner == "owner"
        assert tracker.repo_name == "repo"

    @pytest.mark.unit
    def test_init_without_token(self) -> None:
        """Test initialization without token uses gh CLI."""
        tracker = GitHubTracker(
            repo_owner="owner",
            repo_name="repo",
        )
        assert tracker.repo_owner == "owner"
        assert tracker.repo_name == "repo"


class TestCreateTask:
    """Test create_task method."""

    @mock.patch("subprocess.run")
    def test_create_task_minimal(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test creating a task with minimal parameters."""
        # Mock returns JSON from create
        sample_github_issue["labels"] = [{"name": "type:task"}]
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.create_task(title="Test Issue")

        assert task.id == "123"  # GitHub issue number as ID
        assert task.title == "Test Issue"
        assert task.task_type == "task"
        # Should have at least one call (create)
        assert mock_run.call_count >= 1

    @mock.patch("subprocess.run")
    def test_create_task_with_description(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test creating a task with description."""
        sample_github_issue["body"] = "Detailed description"
        sample_github_issue["labels"] = [{"name": "type:task"}]
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.create_task(
            title="Test Issue",
            description="Detailed description",
        )

        assert task.description == "Detailed description"

    @mock.patch("subprocess.run")
    def test_create_task_with_type_mapping(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test that task type is mapped to GitHub labels."""
        sample_github_issue["labels"] = [{"name": "type:bug"}]
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.create_task(
            title="Bug Report",
            task_type="bug",
        )

        assert task.task_type == "bug"
        # Verify gh command was called with labels
        assert mock_run.call_count >= 1
        # Check that type:bug was in one of the calls
        all_args = [str(call) for call in mock_run.call_args_list]
        assert any("type:bug" in arg for arg in all_args)

    @mock.patch("subprocess.run")
    def test_create_task_command_failure(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker
    ) -> None:
        """Test create_task handles command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh issue create")

        with pytest.raises(subprocess.CalledProcessError):
            github_tracker.create_task(title="Test")


class TestGetTask:
    """Test get_task method."""

    @mock.patch("subprocess.run")
    def test_get_task_success(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test retrieving an existing task."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.get_task("123")

        assert task.id == "123"
        assert task.title == "Test Issue"
        mock_run.assert_called_once()

    @mock.patch("subprocess.run")
    def test_get_task_not_found(self, mock_run: mock.Mock, github_tracker: GitHubTracker) -> None:
        """Test get_task raises KeyError when issue not found."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh issue view")

        with pytest.raises(KeyError):
            github_tracker.get_task("nonexistent")


class TestListTasks:
    """Test list_tasks method."""

    @mock.patch("subprocess.run")
    def test_list_tasks_all(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test listing all tasks."""
        issues = [sample_github_issue, {**sample_github_issue, "number": 124}]
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(issues).encode(),
        )

        tasks = github_tracker.list_tasks()

        assert len(tasks) == 2
        assert all(isinstance(t, Task) for t in tasks)

    @mock.patch("subprocess.run")
    def test_list_tasks_filter_by_status(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test listing tasks filtered by status."""
        sample_github_issue["state"] = "closed"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps([sample_github_issue]).encode(),
        )

        tasks = github_tracker.list_tasks(status="closed")

        assert len(tasks) == 1
        assert tasks[0].status == "closed"

    @mock.patch("subprocess.run")
    def test_list_tasks_empty(self, mock_run: mock.Mock, github_tracker: GitHubTracker) -> None:
        """Test listing tasks when none exist."""
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=b"[]",
        )

        tasks = github_tracker.list_tasks()

        assert tasks == []


class TestUpdateTask:
    """Test update_task method."""

    @mock.patch("subprocess.run")
    def test_update_task_status(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test updating task status."""
        sample_github_issue["state"] = "closed"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.update_task("123", status="closed")

        assert task.status == "closed"
        # update_task calls edit then get_task
        assert mock_run.call_count >= 1

    @mock.patch("subprocess.run")
    def test_update_task_title(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test updating task title."""
        sample_github_issue["title"] = "Updated Title"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        task = github_tracker.update_task("123", title="Updated Title")

        assert task.title == "Updated Title"


class TestCloseTask:
    """Test close_task method."""

    @mock.patch("subprocess.run")
    def test_close_task_success(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test closing a task."""
        sample_github_issue["state"] = "closed"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        github_tracker.close_task("123")

        # close calls gh issue close
        assert mock_run.call_count >= 1

    @mock.patch("subprocess.run")
    def test_close_task_with_reason(
        self, mock_run: mock.Mock, github_tracker: GitHubTracker, sample_github_issue: dict
    ) -> None:
        """Test closing a task with a reason."""
        sample_github_issue["state"] = "closed"
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(sample_github_issue).encode(),
        )

        github_tracker.close_task("123", reason="Completed successfully")

        # close then comment calls subprocess twice
        assert mock_run.call_count >= 1
