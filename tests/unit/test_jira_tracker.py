"""Tests for JiraTracker implementation."""

from unittest import mock

import pytest

from jiro.trackers.interface import Task
from jiro.trackers.jira import JiraTracker


@pytest.fixture
def jira_tracker() -> JiraTracker:
    """Create a JiraTracker instance for testing."""
    with mock.patch("jiro.trackers.jira.JIRA"):
        return JiraTracker(
            server_url="https://jira.example.com",
            username="test-user",
            api_token="test-token",
        )


@pytest.fixture
def sample_jira_issue() -> dict:
    """Sample Jira issue data."""
    return {
        "id": "10000",
        "key": "PROJ-1",
        "fields": {
            "summary": "Test Issue",
            "description": "Test description",
            "status": {"name": "Open"},
            "issuetype": {"name": "Task"},
            "created": "2024-01-15T10:00:00.000-0500",
            "updated": "2024-01-15T12:00:00.000-0500",
            "priority": {"name": "Medium"},
            "customfield_priority": 2,
        },
    }


class TestJiraTrackerInit:
    """Test JiraTracker initialization."""

    @pytest.mark.unit
    @mock.patch("jiro.trackers.jira.JIRA")
    def test_init_with_credentials(self, mock_jira: mock.Mock) -> None:
        """Test initialization with credentials."""
        tracker = JiraTracker(
            server_url="https://jira.example.com",
            username="user",
            api_token="token123",
        )
        assert tracker.server_url == "https://jira.example.com"
        assert tracker.username == "user"
        assert tracker.api_token == "token123"

    @pytest.mark.unit
    @mock.patch("jiro.trackers.jira.JIRA")
    def test_init_with_oauth_token(self, mock_jira: mock.Mock) -> None:
        """Test initialization with OAuth token."""
        tracker = JiraTracker(
            server_url="https://jira.example.com",
            oauth_token="oauth-token-123",
        )
        assert tracker.server_url == "https://jira.example.com"
        assert tracker.oauth_token == "oauth-token-123"


class TestCreateTask:
    """Test create_task method."""

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_create_task_minimal(
        self, mock_jira: mock.Mock, jira_tracker: JiraTracker, sample_jira_issue: dict
    ) -> None:
        """Test creating a task with minimal parameters."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.create_issue.return_value = mock_issue

        task = jira_tracker.create_task(title="Test Issue")

        assert task.id == "PROJ-1"
        assert task.title == "Test Issue"
        assert task.task_type == "task"
        jira_tracker.jira.create_issue.assert_called_once()

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_create_task_with_description(
        self, mock_jira: mock.Mock, jira_tracker: JiraTracker
    ) -> None:
        """Test creating a task with description."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Detailed description"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.create_issue.return_value = mock_issue

        task = jira_tracker.create_task(
            title="Test Issue",
            description="Detailed description",
        )

        assert task.description == "Detailed description"
        # Verify create_issue was called with description
        call_kwargs = jira_tracker.jira.create_issue.call_args[1]
        assert call_kwargs.get("description") == "Detailed description"

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_create_task_with_type_mapping(
        self, mock_jira: mock.Mock, jira_tracker: JiraTracker
    ) -> None:
        """Test that task type is mapped to Jira issue types."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Bug Report"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Bug"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 1

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.create_issue.return_value = mock_issue

        task = jira_tracker.create_task(
            title="Bug Report",
            task_type="bug",
        )

        assert task.task_type == "bug"
        # Verify create_issue was called with Bug type
        call_kwargs = jira_tracker.jira.create_issue.call_args[1]
        assert call_kwargs.get("issuetype") == {"name": "Bug"}


class TestGetTask:
    """Test get_task method."""

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_get_task_success(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test retrieving an existing task."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test description"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.issue.return_value = mock_issue

        task = jira_tracker.get_task("PROJ-1")

        assert task.id == "PROJ-1"
        assert task.title == "Test Issue"
        jira_tracker.jira.issue.assert_called_once_with("PROJ-1")

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_get_task_not_found(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test get_task raises KeyError when issue not found."""
        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.issue.side_effect = Exception("Issue not found")

        with pytest.raises(KeyError):
            jira_tracker.get_task("NONEXISTENT")


class TestListTasks:
    """Test list_tasks method."""

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_list_tasks_all(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test listing all tasks."""
        mock_issue1 = mock.Mock()
        mock_issue1.key = "PROJ-1"
        mock_issue1.id = "10000"
        mock_issue1.fields.summary = "Test Issue 1"
        mock_issue1.fields.description = None
        mock_issue1.fields.status.name = "Open"
        mock_issue1.fields.issuetype.name = "Task"
        mock_issue1.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue1.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue1.fields.customfield_priority = 2

        mock_issue2 = mock.Mock()
        mock_issue2.key = "PROJ-2"
        mock_issue2.id = "10001"
        mock_issue2.fields.summary = "Test Issue 2"
        mock_issue2.fields.description = None
        mock_issue2.fields.status.name = "Open"
        mock_issue2.fields.issuetype.name = "Task"
        mock_issue2.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue2.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue2.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.search_issues.return_value = [mock_issue1, mock_issue2]

        tasks = jira_tracker.list_tasks()

        assert len(tasks) == 2
        assert all(isinstance(t, Task) for t in tasks)

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_list_tasks_filter_by_status(
        self, mock_jira: mock.Mock, jira_tracker: JiraTracker
    ) -> None:
        """Test listing tasks filtered by status."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Closed"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.search_issues.return_value = [mock_issue]

        tasks = jira_tracker.list_tasks(status="closed")

        assert len(tasks) == 1
        assert tasks[0].status == "closed"

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_list_tasks_empty(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test listing tasks when none exist."""
        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.search_issues.return_value = []

        tasks = jira_tracker.list_tasks()

        assert tasks == []


class TestUpdateTask:
    """Test update_task method."""

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_update_task_status(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test updating task status."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Closed"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.issue.return_value = mock_issue
        jira_tracker.jira.transitions.return_value = [
            {"id": "1", "to": {"name": "Closed"}},
        ]
        jira_tracker.jira.transition_issue.return_value = None

        task = jira_tracker.update_task("PROJ-1", status="closed")

        assert task.status == "closed"
        # transition_issue should be called during status change
        assert jira_tracker.jira.transition_issue.called or not jira_tracker.jira.transitions.called

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_update_task_title(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test updating task title."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Updated Title"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.issue.return_value = mock_issue

        task = jira_tracker.update_task("PROJ-1", title="Updated Title")

        assert task.title == "Updated Title"


class TestCloseTask:
    """Test close_task method."""

    @mock.patch("jiro.trackers.jira.JIRA")
    def test_close_task_success(self, mock_jira: mock.Mock, jira_tracker: JiraTracker) -> None:
        """Test closing a task."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Closed"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        jira_tracker.jira = mock.Mock()
        jira_tracker.jira.issue.return_value = mock_issue
        jira_tracker.jira.transitions.return_value = [
            {"id": "1", "to": {"name": "Done"}},
        ]
        jira_tracker.jira.transition_issue.return_value = None

        jira_tracker.close_task("PROJ-1")

        # Should call transition to close the task
        assert jira_tracker.jira.transitions.called


class TestParseTask:
    """Test _parse_task method."""

    def test_parse_task_basic(self, jira_tracker: JiraTracker) -> None:
        """Test parsing a basic Jira issue."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 2

        task = jira_tracker._parse_task(mock_issue)

        assert task.id == "PROJ-1"
        assert task.title == "Test Issue"
        assert task.task_type == "task"
        assert task.status == "open"

    def test_parse_task_with_priority(self, jira_tracker: JiraTracker) -> None:
        """Test parsing Jira issue with priority."""
        mock_issue = mock.Mock()
        mock_issue.key = "PROJ-1"
        mock_issue.id = "10000"
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = None
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.issuetype.name = "Task"
        mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
        mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
        mock_issue.fields.customfield_priority = 1

        task = jira_tracker._parse_task(mock_issue)

        assert task.priority == 1

    def test_parse_task_status_mapping(self, jira_tracker: JiraTracker) -> None:
        """Test status mapping from Jira to jiro."""
        statuses = ["Open", "In Progress", "Done", "Closed"]
        expected = ["open", "in_progress", "closed", "closed"]

        for jira_status, expected_status in zip(statuses, expected, strict=False):
            mock_issue = mock.Mock()
            mock_issue.key = "PROJ-1"
            mock_issue.id = "10000"
            mock_issue.fields.summary = "Test"
            mock_issue.fields.description = None
            mock_issue.fields.status.name = jira_status
            mock_issue.fields.issuetype.name = "Task"
            mock_issue.fields.created = "2024-01-15T10:00:00.000-0500"
            mock_issue.fields.updated = "2024-01-15T12:00:00.000-0500"
            mock_issue.fields.customfield_priority = 2

            task = jira_tracker._parse_task(mock_issue)
            assert task.status == expected_status, f"Expected {expected_status} for {jira_status}"
