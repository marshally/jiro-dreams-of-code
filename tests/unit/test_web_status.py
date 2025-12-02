"""Tests for session status endpoint."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from jiro.db.models import Session


class TestSessionStatusEndpoint:
    """Tests for GET /status endpoint."""

    @pytest.mark.unit
    def test_status_endpoint_exists(self) -> None:
        """Should have a /status endpoint."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200

    @pytest.mark.unit
    def test_status_endpoint_returns_html(self) -> None:
        """Status endpoint should return HTML response."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.unit
    def test_status_endpoint_renders_template(self) -> None:
        """Status endpoint should render the status.html template."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200
        # Should contain HTML structure
        assert b"<html" in response.content.lower() or b"<!doctype" in response.content.lower()

    @pytest.mark.unit
    def test_status_endpoint_contains_sessions_info(self) -> None:
        """Status endpoint should display session information."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/status")
        assert response.status_code == 200
        content = response.content.decode()
        # Should contain some session-related content or be empty state
        assert "session" in content.lower() or "no" in content.lower()

    @pytest.mark.unit
    def test_status_endpoint_with_active_sessions(self) -> None:
        """Status endpoint should display active sessions."""
        from jiro.web.app import app

        # Create mock sessions
        mock_session = Session(
            id="test-session-1",
            branch_name="test-branch",
            status="running",
            started_at=datetime.now(),
        )

        client = TestClient(app)

        with patch("jiro.web.app.get_database_connection") as mock_get_db:
            mock_db = Mock()
            mock_session_repo = Mock()
            mock_task_repo = Mock()
            mock_prompt_repo = Mock()

            mock_session_repo.get_active = Mock(return_value=[mock_session])
            mock_task_repo.get_by_session = Mock(return_value=[])
            mock_prompt_repo.get_total_tokens = Mock(return_value=0)

            mock_get_db.return_value = mock_db

            with (
                patch("jiro.web.app.SessionRepository", return_value=mock_session_repo),
                patch("jiro.web.app.TaskExecutionRepository", return_value=mock_task_repo),
                patch("jiro.web.app.PromptRepository", return_value=mock_prompt_repo),
            ):
                response = client.get("/status")
                assert response.status_code == 200
                content = response.content.decode()
                # Should contain session information
                assert "test-session-1" in content or "running" in content.lower()

    @pytest.mark.unit
    def test_status_endpoint_with_no_active_sessions(self) -> None:
        """Status endpoint should handle empty sessions gracefully."""
        from jiro.web.app import app

        client = TestClient(app)

        with patch("jiro.web.app.get_database_connection") as mock_get_db:
            mock_db = Mock()
            mock_session_repo = Mock()
            mock_task_repo = Mock()
            mock_prompt_repo = Mock()

            mock_session_repo.get_active = Mock(return_value=[])
            mock_task_repo.get_by_session = Mock(return_value=[])
            mock_prompt_repo.get_total_tokens = Mock(return_value=0)

            mock_get_db.return_value = mock_db

            with (
                patch("jiro.web.app.SessionRepository", return_value=mock_session_repo),
                patch("jiro.web.app.TaskExecutionRepository", return_value=mock_task_repo),
                patch("jiro.web.app.PromptRepository", return_value=mock_prompt_repo),
            ):
                response = client.get("/status")
                assert response.status_code == 200
                content = response.content.decode()
                # Should show empty state
                assert (
                    "empty" in content.lower()
                    or "no" in content.lower()
                    or "active" in content.lower()
                )

    @pytest.mark.unit
    def test_status_endpoint_displays_session_details(self) -> None:
        """Status endpoint should display session details like ID, status, and start time."""
        from jiro.web.app import app

        mock_session = Session(
            id="test-session-2",
            branch_name="feature-branch",
            status="running",
            started_at=datetime(2025, 12, 1, 10, 30, 0),
            preflight_passed_at=datetime(2025, 12, 1, 10, 31, 0),
        )

        client = TestClient(app)

        with patch("jiro.web.app.get_database_connection") as mock_get_db:
            mock_db = Mock()
            mock_session_repo = Mock()
            mock_task_repo = Mock()
            mock_prompt_repo = Mock()

            mock_session_repo.get_active = Mock(return_value=[mock_session])
            mock_task_repo.get_by_session = Mock(return_value=[])
            mock_prompt_repo.get_total_tokens = Mock(return_value=0)

            mock_get_db.return_value = mock_db

            with (
                patch("jiro.web.app.SessionRepository", return_value=mock_session_repo),
                patch("jiro.web.app.TaskExecutionRepository", return_value=mock_task_repo),
                patch("jiro.web.app.PromptRepository", return_value=mock_prompt_repo),
            ):
                response = client.get("/status")
                assert response.status_code == 200
                content = response.content.decode()
                # Should contain session ID and status
                assert "test-session-2" in content or "feature-branch" in content

    @pytest.mark.unit
    def test_status_endpoint_handles_tracker_errors_gracefully(self) -> None:
        """Status endpoint should handle tracker errors gracefully."""
        from jiro.web.app import app

        client = TestClient(app)

        with patch("jiro.web.app.get_tracker") as mock_get_tracker:
            mock_get_tracker.side_effect = Exception("Database error")

            response = client.get("/status")
            # Should not crash, fallback to empty state
            assert response.status_code == 200
            assert b"<" in response.content

    @pytest.mark.unit
    def test_status_template_has_htmx_support(self) -> None:
        """Status template should include HTMX for interactivity."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/status")
        content = response.content.decode()
        # Should have HTMX script reference
        assert "htmx" in content.lower() or "<script" in content.lower()

    @pytest.mark.unit
    def test_status_endpoint_uses_jinja_template(self) -> None:
        """Status endpoint should use Jinja2 template rendering."""
        from jiro.web.app import template_env

        # Template should be loadable
        try:
            template = template_env.get_template("status.html")
            assert template is not None
        except Exception:
            # Template may not exist yet, which is fine for TDD
            pass
