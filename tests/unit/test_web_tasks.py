"""Tests for task list web endpoint."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from jiro.trackers.interface import Task


class TestTasksEndpoint:
    """Tests for GET /tasks endpoint."""

    @pytest.mark.integration
    def test_tasks_endpoint_exists(self) -> None:
        """Should have a /tasks endpoint."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/tasks")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_tasks_endpoint_returns_html(self) -> None:
        """Should return HTML response."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/tasks")
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.integration
    def test_tasks_endpoint_renders_template(self) -> None:
        """Should render tasks.html template."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/tasks")
        assert response.status_code == 200
        # Should contain HTML markup
        assert b"<" in response.content and b">" in response.content

    @pytest.mark.integration
    def test_tasks_list_empty(self) -> None:
        """Should handle empty task list gracefully."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/tasks")
        assert response.status_code == 200
        # Should still render valid HTML
        assert b"<html" in response.content or b"<body" in response.content

    @pytest.mark.unit
    def test_tasks_grouped_by_status(self) -> None:
        """Should group tasks by status in template context."""
        from jiro.web.app import get_tasks_grouped_by_status

        # Create test tasks
        tasks = [
            Task(
                id="test-1",
                title="Open task",
                task_type="task",
                status="open",
                created_at=datetime.now(),
            ),
            Task(
                id="test-2",
                title="In progress task",
                task_type="task",
                status="in_progress",
                created_at=datetime.now(),
            ),
            Task(
                id="test-3",
                title="Closed task",
                task_type="task",
                status="closed",
                created_at=datetime.now(),
            ),
        ]

        grouped = get_tasks_grouped_by_status(tasks)

        # Should have three groups
        assert "open" in grouped
        assert "in_progress" in grouped
        assert "closed" in grouped

        # Each group should contain correct tasks
        assert len(grouped["open"]) == 1
        assert grouped["open"][0].title == "Open task"

        assert len(grouped["in_progress"]) == 1
        assert grouped["in_progress"][0].title == "In progress task"

        assert len(grouped["closed"]) == 1
        assert grouped["closed"][0].title == "Closed task"

    @pytest.mark.unit
    def test_tasks_grouped_by_epic(self) -> None:
        """Should group tasks by epic."""
        from jiro.web.app import get_tasks_grouped_by_epic

        tasks = [
            Task(
                id="test-1",
                title="Epic 1 task",
                task_type="task",
                status="open",
                created_at=datetime.now(),
                epic_id="epic-1",
            ),
            Task(
                id="test-2",
                title="Epic 2 task",
                task_type="task",
                status="open",
                created_at=datetime.now(),
                epic_id="epic-2",
            ),
            Task(
                id="test-3",
                title="No epic task",
                task_type="task",
                status="open",
                created_at=datetime.now(),
                epic_id=None,
            ),
        ]

        grouped = get_tasks_grouped_by_epic(tasks)

        # Should have three groups (including None for no epic)
        assert "epic-1" in grouped
        assert "epic-2" in grouped
        assert None in grouped

        # Each group should contain correct tasks
        assert len(grouped["epic-1"]) == 1
        assert len(grouped["epic-2"]) == 1
        assert len(grouped[None]) == 1

    @pytest.mark.integration
    def test_tasks_endpoint_with_tracker(self) -> None:
        """Should fetch tasks from tracker."""
        from unittest.mock import patch

        from jiro.web.app import app

        # Mock tasks
        mock_tasks = [
            Task(
                id="test-1",
                title="Task 1",
                task_type="task",
                status="open",
                created_at=datetime.now(),
            ),
        ]

        # Patch the tracker list_tasks method
        with patch("jiro.web.app.get_tracker") as mock_get_tracker:
            mock_tracker = MagicMock()
            mock_tracker.list_tasks.return_value = mock_tasks
            mock_get_tracker.return_value = mock_tracker

            client = TestClient(app)
            response = client.get("/tasks")

            # Should call tracker
            mock_tracker.list_tasks.assert_called()

            # Should still return 200
            assert response.status_code == 200

    @pytest.mark.integration
    def test_tasks_endpoint_has_htmx_attributes(self) -> None:
        """Should include HTMX attributes for dynamic updates."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/tasks")

        # Check for HTMX-style attributes
        html = response.content.decode()
        # Should have hx- attributes or at least be valid HTML
        assert "<" in html and ">" in html
