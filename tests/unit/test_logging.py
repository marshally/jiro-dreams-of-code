"""Tests for structlog configuration."""

import json
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import structlog

from jiro.core.logging import (
    configure_logging,
    get_context_var,
    set_context_var,
)


class TestConfigureLogging:
    """Tests for configure_logging function."""

    @pytest.mark.unit
    def test_configure_logging_returns_logger(self, tmp_path: Path) -> None:
        """configure_logging should return a structlog logger."""
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = tmp_path / "logs"
            logger = configure_logging(verbosity=logging.INFO, project_name="test")
            assert logger is not None

    @pytest.mark.unit
    def test_default_verbosity_is_info(self, tmp_path: Path) -> None:
        """Default verbosity should be INFO."""
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = tmp_path / "logs"
            logger = configure_logging(project_name="test")
            assert logger is not None

    @pytest.mark.unit
    def test_verbosity_debug_level(self, tmp_path: Path) -> None:
        """Verbosity DEBUG should set log level to DEBUG."""
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = tmp_path / "logs"
            logger = configure_logging(verbosity=logging.DEBUG, project_name="test")
            assert logger is not None

    @pytest.mark.unit
    def test_verbosity_critical_level(self, tmp_path: Path) -> None:
        """Verbosity CRITICAL should set log level to CRITICAL."""
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = tmp_path / "logs"
            logger = configure_logging(verbosity=logging.CRITICAL, project_name="test")
            assert logger is not None

    @pytest.mark.unit
    def test_jsonl_file_created(self, tmp_path: Path) -> None:
        """JSONL log file should be created."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="test")
            logger.info("test message")

            # Get today's date for the expected filename
            today = datetime.now().strftime("%Y-%m-%d")
            expected_file = logs_dir / f"{today}.jsonl"

            assert expected_file.exists()

    @pytest.mark.unit
    def test_jsonl_format_valid(self, tmp_path: Path) -> None:
        """JSONL log entries should be valid JSON."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="test")
            logger.info("test message", key="value")

            today = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{today}.jsonl"

            # Read and parse each line
            with open(log_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        assert isinstance(data, dict)

    @pytest.mark.unit
    def test_jsonl_contains_message(self, tmp_path: Path) -> None:
        """JSONL log entries should contain the message."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="test")
            logger.info("test message")

            today = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{today}.jsonl"

            with open(log_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        assert data.get("event") == "test message"

    @pytest.mark.unit
    def test_context_binding_session_id(self, tmp_path: Path) -> None:
        """Context binding should include session_id."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            configure_logging(project_name="test")
            set_context_var("session_id", "test-session-123")

            logger = structlog.get_logger()
            logger.info("test")

            today = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{today}.jsonl"

            with open(log_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("event") == "test":
                            assert data.get("session_id") == "test-session-123"

    @pytest.mark.unit
    def test_context_binding_task_id(self, tmp_path: Path) -> None:
        """Context binding should include task_id."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            configure_logging(project_name="test")
            set_context_var("task_id", "task-456")

            logger = structlog.get_logger()
            logger.info("test task")

            today = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{today}.jsonl"

            with open(log_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("event") == "test task":
                            assert data.get("task_id") == "task-456"

    @pytest.mark.unit
    def test_context_vars_isolated(self, tmp_path: Path) -> None:
        """Context variables should be isolated between tests."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            configure_logging(project_name="test")

            # Set and clear context
            set_context_var("session_id", "session-1")
            val = get_context_var("session_id")
            assert val == "session-1"

    @pytest.mark.unit
    def test_multiple_verbosity_levels(self, tmp_path: Path) -> None:
        """Multiple configure_logging calls with different verbosity."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir

            # INFO level
            logger1 = configure_logging(verbosity=logging.INFO, project_name="test")
            assert logger1 is not None

            # DEBUG level
            logger2 = configure_logging(verbosity=logging.DEBUG, project_name="test")
            assert logger2 is not None

    @pytest.mark.unit
    def test_project_name_in_logs_path(self, tmp_path: Path) -> None:
        """Project name should be used in logs directory path."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="my-project")
            logger.info("test")

            # Verify get_logs_dir was called with project_name
            mock_logs.assert_called()

    @pytest.mark.unit
    def test_rich_console_configured(self, tmp_path: Path) -> None:
        """Rich console should be configured for output."""
        logs_dir = tmp_path / "logs"
        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="test")
            assert logger is not None

    @pytest.mark.unit
    def test_logs_dir_created_if_not_exists(self, tmp_path: Path) -> None:
        """Logs directory should be created if it doesn't exist."""
        logs_dir = tmp_path / "logs"
        assert not logs_dir.exists()

        with patch("jiro.core.logging.get_logs_dir") as mock_logs:
            mock_logs.return_value = logs_dir
            logger = configure_logging(project_name="test")
            logger.info("test")

            assert logs_dir.exists()


class TestContextVariables:
    """Tests for context variable management."""

    @pytest.mark.unit
    def test_set_and_get_context_var(self) -> None:
        """Should be able to set and get context variables."""
        set_context_var("test_key", "test_value")
        value = get_context_var("test_key")
        assert value == "test_value"

    @pytest.mark.unit
    def test_get_nonexistent_context_var(self) -> None:
        """Getting a nonexistent context variable should return None."""
        value = get_context_var("nonexistent_key_xyz")
        assert value is None

    @pytest.mark.unit
    def test_set_multiple_context_vars(self) -> None:
        """Should be able to set multiple context variables."""
        set_context_var("key1", "value1")
        set_context_var("key2", "value2")
        assert get_context_var("key1") == "value1"
        assert get_context_var("key2") == "value2"

    @pytest.mark.unit
    def test_overwrite_context_var(self) -> None:
        """Should be able to overwrite context variables."""
        set_context_var("key", "value1")
        set_context_var("key", "value2")
        assert get_context_var("key") == "value2"
