"""Tests for LinearTracker implementation."""

from datetime import datetime
from unittest import mock

import pytest

from jiro.trackers.linear import LinearTracker


@pytest.fixture
def linear_tracker() -> LinearTracker:
    """Create a LinearTracker instance for testing."""
    return LinearTracker(api_key="test-api-key")


@pytest.fixture
def sample_linear_issue() -> dict:
    """Sample Linear issue data from GraphQL response."""
    return {
        "id": "PROJ-123",
        "identifier": "PROJ-123",
        "title": "Test Issue",
        "description": "Test description",
        "state": {"name": "Todo"},
        "type": "Task",
        "priority": 2,
        "createdAt": "2024-01-15T10:00:00.000Z",
        "updatedAt": "2024-01-15T12:00:00.000Z",
        "archivedAt": None,
        "cycle": {"name": "Sprint 1"},
        "team": {"name": "Backend"},
    }


@pytest.fixture
def mock_linear_session(linear_tracker: LinearTracker) -> mock.Mock:
    """Create a mock session for LinearTracker."""
    mock_session = mock.Mock()
    linear_tracker.session = mock_session
    return mock_session


class TestLinearTrackerInit:
    """Test LinearTracker initialization."""

    @pytest.mark.unit
    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        tracker = LinearTracker(api_key="test-key")
        assert tracker.api_key == "test-key"

    @pytest.mark.unit
    def test_init_sets_graphql_endpoint(self) -> None:
        """Test initialization sets GraphQL endpoint."""
        tracker = LinearTracker(api_key="test-key")
        assert tracker.graphql_endpoint == "https://api.linear.app/graphql"


class TestParseTask:
    """Test _parse_task method."""

    @pytest.mark.unit
    def test_parse_task_basic(
        self, linear_tracker: LinearTracker, sample_linear_issue: dict
    ) -> None:
        """Test parsing a basic Linear issue to Task."""
        task = linear_tracker._parse_task(sample_linear_issue)

        assert task.id == "PROJ-123"
        assert task.title == "Test Issue"
        assert task.description == "Test description"
        assert task.task_type == "task"
        assert task.status == "open"
        # Linear priority 2 (medium) maps to jiro priority 3 (medium)
        assert task.priority == 3

    @pytest.mark.unit
    def test_parse_task_type_mapping(
        self, linear_tracker: LinearTracker, sample_linear_issue: dict
    ) -> None:
        """Test that Linear issue types are mapped correctly."""
        # Test each type mapping
        sample_linear_issue["type"] = "Bug"
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.task_type == "bug"

        sample_linear_issue["type"] = "Feature"
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.task_type == "feature"

        sample_linear_issue["type"] = "Epic"
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.task_type == "epic"

    @pytest.mark.unit
    def test_parse_task_status_mapping(
        self, linear_tracker: LinearTracker, sample_linear_issue: dict
    ) -> None:
        """Test that Linear states are mapped to Task statuses."""
        # Test various state mappings
        sample_linear_issue["state"] = {"name": "Todo"}
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.status == "open"

        sample_linear_issue["state"] = {"name": "In Progress"}
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.status == "in_progress"

        sample_linear_issue["state"] = {"name": "Done"}
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.status == "closed"

        sample_linear_issue["state"] = {"name": "Blocked"}
        task = linear_tracker._parse_task(sample_linear_issue)
        assert task.status == "blocked"

    @pytest.mark.unit
    def test_parse_task_timestamps(
        self, linear_tracker: LinearTracker, sample_linear_issue: dict
    ) -> None:
        """Test that timestamps are parsed correctly."""
        task = linear_tracker._parse_task(sample_linear_issue)

        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.closed_at is None

        # Test with archived issue
        sample_linear_issue["archivedAt"] = "2024-01-20T15:00:00.000Z"
        task = linear_tracker._parse_task(sample_linear_issue)
        assert isinstance(task.closed_at, datetime)


class TestCreateTask:
    """Test create_task method."""

    def test_create_task_minimal(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test creating a task with minimal parameters."""
        sample_linear_issue["type"] = "Task"
        sample_linear_issue["state"] = {"name": "Todo"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueCreate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.create_task(title="Test Issue")

        assert task.id == "PROJ-123"
        assert task.title == "Test Issue"
        assert task.task_type == "task"
        assert mock_linear_session.post.called

    def test_create_task_with_description(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test creating a task with description."""
        sample_linear_issue["description"] = "Detailed description"
        sample_linear_issue["type"] = "Task"
        sample_linear_issue["state"] = {"name": "Todo"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueCreate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.create_task(
            title="Test Issue",
            description="Detailed description",
        )

        assert task.description == "Detailed description"

    def test_create_task_with_type(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test creating a task with specific type."""
        sample_linear_issue["type"] = "Bug"
        sample_linear_issue["state"] = {"name": "Todo"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueCreate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.create_task(
            title="Bug Report",
            task_type="bug",
        )

        assert task.task_type == "bug"

    def test_create_task_with_priority(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test creating a task with priority."""
        sample_linear_issue["priority"] = 4
        sample_linear_issue["type"] = "Task"
        sample_linear_issue["state"] = {"name": "Todo"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueCreate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.create_task(
            title="Urgent Task",
            priority=1,  # jiro priority 1 (highest) maps to Linear 4 (urgent)
        )

        # Linear priority 4 (urgent) maps to jiro priority 1 (highest)
        assert task.priority == 1


class TestGetTask:
    """Test get_task method."""

    def test_get_task_success(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test retrieving an existing task."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issue": sample_linear_issue}},
        )

        task = linear_tracker.get_task("PROJ-123")

        assert task.id == "PROJ-123"
        assert task.title == "Test Issue"
        assert mock_linear_session.post.called

    def test_get_task_not_found(
        self, linear_tracker: LinearTracker, mock_linear_session: mock.Mock
    ) -> None:
        """Test retrieving a non-existent task."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issue": None}},
        )

        with pytest.raises(KeyError):
            linear_tracker.get_task("NONEXISTENT-123")


class TestListTasks:
    """Test list_tasks method."""

    def test_list_tasks_all(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test listing all tasks."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {
                "data": {
                    "issues": {
                        "edges": [{"node": sample_linear_issue}],
                    }
                }
            },
        )

        tasks = linear_tracker.list_tasks()

        assert len(tasks) == 1
        assert tasks[0].id == "PROJ-123"

    def test_list_tasks_by_status(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test listing tasks filtered by status."""
        sample_linear_issue["state"] = {"name": "In Progress"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {
                "data": {
                    "issues": {
                        "edges": [{"node": sample_linear_issue}],
                    }
                }
            },
        )

        tasks = linear_tracker.list_tasks(status="in_progress")

        assert len(tasks) == 1
        assert tasks[0].status == "in_progress"

    def test_list_tasks_empty(
        self, linear_tracker: LinearTracker, mock_linear_session: mock.Mock
    ) -> None:
        """Test listing tasks when none exist."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issues": {"edges": []}}},
        )

        tasks = linear_tracker.list_tasks()

        assert len(tasks) == 0


class TestUpdateTask:
    """Test update_task method."""

    def test_update_task_status(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test updating task status."""
        sample_linear_issue["state"] = {"name": "Done"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueUpdate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.update_task("PROJ-123", status="closed")

        assert task.status == "closed"
        assert mock_linear_session.post.called

    def test_update_task_title(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test updating task title."""
        sample_linear_issue["title"] = "Updated Title"
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueUpdate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.update_task("PROJ-123", title="Updated Title")

        assert task.title == "Updated Title"

    def test_update_task_priority(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test updating task priority."""
        sample_linear_issue["priority"] = 4
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueUpdate": {"issue": sample_linear_issue}}},
        )

        task = linear_tracker.update_task("PROJ-123", priority=4)

        # Linear priority 4 maps to jiro priority 1
        assert task.priority == 1


class TestGetNextReadyTask:
    """Test get_next_ready_task method."""

    def test_get_next_ready_task(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test getting next ready task."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {
                "data": {
                    "issues": {
                        "edges": [{"node": sample_linear_issue}],
                    }
                }
            },
        )

        task = linear_tracker.get_next_ready_task()

        assert task is not None
        assert task.id == "PROJ-123"

    def test_get_next_ready_task_none(
        self, linear_tracker: LinearTracker, mock_linear_session: mock.Mock
    ) -> None:
        """Test getting next ready task when none available."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issues": {"edges": []}}},
        )

        task = linear_tracker.get_next_ready_task()

        assert task is None


class TestAddDependency:
    """Test add_dependency method."""

    def test_add_dependency(
        self, linear_tracker: LinearTracker, mock_linear_session: mock.Mock
    ) -> None:
        """Test adding a dependency between tasks."""
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueLinkCreate": {"issueLink": {}}}},
        )

        # Should not raise
        linear_tracker.add_dependency("PROJ-123", "PROJ-124")

        assert mock_linear_session.post.called


class TestCloseTask:
    """Test close_task method."""

    def test_close_task(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test closing a task."""
        sample_linear_issue["state"] = {"name": "Done"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueUpdate": {"issue": sample_linear_issue}}},
        )

        # Should not raise
        linear_tracker.close_task("PROJ-123", reason="Completed")

        assert mock_linear_session.post.called

    def test_close_task_without_reason(
        self,
        linear_tracker: LinearTracker,
        sample_linear_issue: dict,
        mock_linear_session: mock.Mock,
    ) -> None:
        """Test closing a task without a reason."""
        sample_linear_issue["state"] = {"name": "Done"}
        mock_linear_session.post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"data": {"issueUpdate": {"issue": sample_linear_issue}}},
        )

        # Should not raise
        linear_tracker.close_task("PROJ-123")

        assert mock_linear_session.post.called


class TestLinearTrackerIntegration:
    """Integration tests for LinearTracker."""

    @pytest.mark.unit
    def test_tracker_implements_interface(self, linear_tracker: LinearTracker) -> None:
        """Test that LinearTracker implements IssueTracker protocol."""
        # Check that all required methods exist
        assert hasattr(linear_tracker, "create_task")
        assert hasattr(linear_tracker, "get_task")
        assert hasattr(linear_tracker, "list_tasks")
        assert hasattr(linear_tracker, "update_task")
        assert hasattr(linear_tracker, "get_next_ready_task")
        assert hasattr(linear_tracker, "add_dependency")
        assert hasattr(linear_tracker, "close_task")
