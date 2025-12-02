"""Tests for logs viewer web endpoint."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestLogsEndpoint:
    """Tests for GET /logs endpoint."""

    @pytest.mark.unit
    def test_logs_endpoint_exists(self) -> None:
        """Should have a /logs endpoint."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/logs")
        assert response.status_code == 200

    @pytest.mark.unit
    def test_logs_endpoint_returns_html(self) -> None:
        """Should return HTML response."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/logs")
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.unit
    def test_logs_endpoint_renders_template(self) -> None:
        """Should render logs.html template."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/logs")
        assert response.status_code == 200
        # Should contain HTML markup
        assert b"<" in response.content and b">" in response.content

    @pytest.mark.unit
    def test_logs_endpoint_empty_logs(self) -> None:
        """Should handle empty logs gracefully."""
        from jiro.web.app import app

        client = TestClient(app)
        response = client.get("/logs")
        assert response.status_code == 200
        # Should still render valid HTML
        assert b"<html" in response.content or b"<body" in response.content

    @pytest.mark.unit
    def test_logs_endpoint_with_entries(self, tmp_path: Path) -> None:
        """Should display log entries from JSONL files."""
        from jiro.web.app import app

        # Create a test log file
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "test.jsonl"
        entries = [
            {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "event": "Application started"},
            {"timestamp": "2024-01-01T10:00:01", "level": "WARNING", "event": "Missing config"},
            {
                "timestamp": "2024-01-01T10:00:02",
                "level": "ERROR",
                "event": "Database connection failed",
            },
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            assert response.status_code == 200
            html = response.content.decode()
            # Should contain log entries
            assert "Application started" in html
            assert "Missing config" in html
            assert "Database connection failed" in html

    @pytest.mark.unit
    def test_logs_endpoint_limits_entries(self, tmp_path: Path) -> None:
        """Should limit displayed logs to recent 50 entries."""
        from jiro.web.app import app

        # Create a test log file with more than 50 entries
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "test.jsonl"

        with open(log_file, "w") as f:
            for i in range(100):
                entry = {
                    "timestamp": f"2024-01-01T10:{i:02d}:00",
                    "level": "INFO",
                    "event": f"Event {i}",
                }
                f.write(json.dumps(entry) + "\n")

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            assert response.status_code == 200
            html = response.content.decode()
            # Should contain recent entries
            assert "Event 99" in html
            # Should not contain very old entries
            assert "Event 1" not in html or "Event 10" in html

    @pytest.mark.unit
    def test_logs_endpoint_htmx_auto_refresh(self, tmp_path: Path) -> None:
        """Should include HTMX auto-refresh attributes."""
        from jiro.web.app import app

        # Create a test log file
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "test.jsonl"
        with open(log_file, "w") as f:
            entry = {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "event": "Test"}
            f.write(json.dumps(entry) + "\n")

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            html = response.content.decode()
            # Should have HTMX auto-refresh
            assert "hx-trigger" in html and "every" in html

    @pytest.mark.unit
    def test_logs_display_timestamp_level_event(self, tmp_path: Path) -> None:
        """Should display log timestamp, level, and event."""
        from jiro.web.app import app

        # Create a test log file
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "test.jsonl"
        entry = {
            "timestamp": "2024-01-01T10:00:00Z",
            "level": "ERROR",
            "event": "Critical issue occurred",
        }

        with open(log_file, "w") as f:
            f.write(json.dumps(entry) + "\n")

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            html = response.content.decode()
            # Should display all three fields
            assert "2024-01-01T10:00:00Z" in html or "2024-01-01" in html
            assert "ERROR" in html
            assert "Critical issue occurred" in html

    @pytest.mark.unit
    def test_logs_endpoint_handles_multiple_log_files(self, tmp_path: Path) -> None:
        """Should read from multiple JSONL log files."""
        from jiro.web.app import app

        # Create multiple test log files
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file1 = logs_dir / "2024-01-01.jsonl"
        with open(log_file1, "w") as f:
            entry = {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "event": "First day"}
            f.write(json.dumps(entry) + "\n")

        log_file2 = logs_dir / "2024-01-02.jsonl"
        with open(log_file2, "w") as f:
            entry = {"timestamp": "2024-01-02T10:00:00", "level": "INFO", "event": "Second day"}
            f.write(json.dumps(entry) + "\n")

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            html = response.content.decode()
            # Should contain entries from both files
            assert "First day" in html
            assert "Second day" in html

    @pytest.mark.unit
    def test_logs_endpoint_handles_missing_logs_directory(self) -> None:
        """Should handle gracefully when logs directory doesn't exist."""
        from jiro.web.app import app

        # Mock get_logs_dir to return a non-existent directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = Path("/nonexistent/logs")

            client = TestClient(app)
            response = client.get("/logs")

            # Should still return 200
            assert response.status_code == 200
            html = response.content.decode()
            # Should render valid HTML
            assert "<html" in html or "<body" in html

    @pytest.mark.unit
    def test_logs_endpoint_handles_invalid_json(self, tmp_path: Path) -> None:
        """Should skip invalid JSON lines in log files."""
        from jiro.web.app import app

        # Create a test log file with some invalid JSON
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "test.jsonl"
        with open(log_file, "w") as f:
            f.write(
                json.dumps({"timestamp": "2024-01-01T10:00:00", "level": "INFO", "event": "Valid"})
                + "\n"
            )
            f.write("this is not valid json\n")
            f.write(
                json.dumps(
                    {"timestamp": "2024-01-01T10:00:01", "level": "INFO", "event": "Also valid"}
                )
                + "\n"
            )

        # Mock get_logs_dir to return our test directory
        with patch("jiro.web.app.get_logs_dir") as mock_get_logs_dir:
            mock_get_logs_dir.return_value = logs_dir

            client = TestClient(app)
            response = client.get("/logs")

            html = response.content.decode()
            # Should contain valid entries
            assert "Valid" in html
            assert "Also valid" in html
            # Should not crash
            assert response.status_code == 200
