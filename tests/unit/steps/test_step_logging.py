"""Tests for step execution logging infrastructure.

Tests cover:
- Console output formatting and readability
- JSON file output structure
- Timing tracking for each phase
- Error logging and exception handling
- Integration with existing logging
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jiro.results.base import Result
from jiro.steps.logging import PhaseLog, StepLog, StepLogger
from jiro.steps.types import StepType


class TestPhaseLog:
    """Tests for PhaseLog dataclass."""

    def test_phase_log_creation(self) -> None:
        """Test creating a PhaseLog entry."""
        log = PhaseLog(
            phase="command",
            event="start",
            timestamp="2025-01-15T12:34:56Z",
        )

        assert log.phase == "command"
        assert log.event == "start"
        assert log.timestamp == "2025-01-15T12:34:56Z"
        assert log.duration_s is None
        assert log.details is None

    def test_phase_log_with_duration(self) -> None:
        """Test PhaseLog with duration."""
        log = PhaseLog(
            phase="verify",
            event="success",
            timestamp="2025-01-15T12:34:57Z",
            duration_s=1.5,
        )

        assert log.duration_s == 1.5

    def test_phase_log_with_details(self) -> None:
        """Test PhaseLog with details dictionary."""
        details = {"error_type": "ValueError", "error_message": "Invalid input"}
        log = PhaseLog(
            phase="verify",
            event="error",
            timestamp="2025-01-15T12:34:57Z",
            duration_s=0.8,
            details=details,
        )

        assert log.details == details

    def test_phase_log_as_dict(self) -> None:
        """Test converting PhaseLog to dictionary."""
        log = PhaseLog(
            phase="command",
            event="start",
            timestamp="2025-01-15T12:34:56Z",
        )
        log_dict = log.as_dict()

        assert isinstance(log_dict, dict)
        assert log_dict["phase"] == "command"
        assert log_dict["event"] == "start"
        assert log_dict["timestamp"] == "2025-01-15T12:34:56Z"

    def test_phase_log_as_json(self) -> None:
        """Test converting PhaseLog to JSON."""
        log = PhaseLog(
            phase="command",
            event="success",
            timestamp="2025-01-15T12:34:57Z",
            duration_s=5.2,
        )
        json_str = log.as_json()

        parsed = json.loads(json_str)
        assert parsed["phase"] == "command"
        assert parsed["event"] == "success"
        assert parsed["duration_s"] == 5.2


class TestStepLog:
    """Tests for StepLog dataclass."""

    def test_step_log_creation(self) -> None:
        """Test creating a StepLog entry."""
        log = StepLog(
            step_type="tdd_red",
            event="start",
            timestamp="2025-01-15T12:34:56Z",
        )

        assert log.step_type == "tdd_red"
        assert log.event == "start"
        assert log.commit_sha is None
        assert log.duration_s is None

    def test_step_log_with_sha(self) -> None:
        """Test StepLog with commit SHA."""
        log = StepLog(
            step_type="tdd_green",
            event="success",
            timestamp="2025-01-15T12:35:00Z",
            duration_s=18.5,
            commit_sha="abc1234567890def",
        )

        assert log.commit_sha == "abc1234567890def"

    def test_step_log_as_json(self) -> None:
        """Test converting StepLog to JSON."""
        log = StepLog(
            step_type="tdd_red",
            event="success",
            timestamp="2025-01-15T12:35:00Z",
            duration_s=20.0,
            commit_sha="abc1234567890def",
        )
        json_str = log.as_json()

        parsed = json.loads(json_str)
        assert parsed["step_type"] == "tdd_red"
        assert parsed["event"] == "success"
        assert parsed["commit_sha"] == "abc1234567890def"


class TestStepLogger:
    """Tests for StepLogger class."""

    @pytest.fixture
    def mock_logs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary logs directory."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        return logs_dir

    @pytest.fixture
    def logger(self, mock_logs_dir: Path) -> StepLogger:
        """Create a StepLogger with mocked logs directory."""
        with (
            patch("jiro.steps.logging.get_logs_dir", return_value=mock_logs_dir),
            patch("jiro.steps.logging.structlog.get_logger"),
        ):
            logger = StepLogger(StepType.TDD_RED)
            logger.log_file = mock_logs_dir / "steps-2025-01-15.jsonl"
            return logger

    def test_logger_initialization(self, logger: StepLogger) -> None:
        """Test StepLogger initialization."""
        assert logger.step_type == StepType.TDD_RED
        assert logger.project_name == "jiro"

    def test_format_duration_seconds(self) -> None:
        """Test formatting duration in seconds."""
        assert StepLogger._format_duration(5.0) == "5.0s"
        assert StepLogger._format_duration(0.5) == "0.5s"
        assert StepLogger._format_duration(59.9) == "59.9s"

    def test_format_duration_minutes(self) -> None:
        """Test formatting duration in minutes and seconds."""
        assert StepLogger._format_duration(60.0) == "1m 0s"
        assert StepLogger._format_duration(90.0) == "1m 30s"
        assert StepLogger._format_duration(150.5) == "2m 30s"

    def test_log_step_start(self, logger: StepLogger) -> None:
        """Test logging step start."""
        with patch.object(logger, "logger") as mock_logger:
            logger.log_step_start()

            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Starting step:" in str(call_args)

    def test_log_command_start(self, logger: StepLogger) -> None:
        """Test logging command start."""
        with patch.object(logger, "logger") as mock_logger:
            logger.log_command_start()

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Command:" in str(call_args)

    def test_log_command_success(self, logger: StepLogger, tmp_path: Path) -> None:
        """Test logging successful command execution."""
        # Create a mock result
        result = Mock(spec=Result)
        result.changed_files = [Path("src/file.py"), Path("tests/test_file.py")]

        with patch.object(logger, "logger") as mock_logger:
            logger.log_command_success(
                duration=5.2,
                result=result,
                subagent_metrics={"tokens_in": 1000, "tokens_out": 500},
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "complete" in str(call_args).lower()

    def test_log_command_error(self, logger: StepLogger) -> None:
        """Test logging command execution error."""
        error = ValueError("Test error")

        with patch.object(logger, "logger") as mock_logger:
            logger.log_command_error(duration=2.0, error=error)

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "failed" in str(call_args).lower()
            assert "ValueError" in str(call_args)

    def test_log_verify_start(self, logger: StepLogger) -> None:
        """Test logging verification start."""
        with patch.object(logger, "logger") as mock_logger:
            logger.log_verify_start()

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Verification:" in str(call_args)

    def test_log_verify_success(self, logger: StepLogger) -> None:
        """Test logging successful verification."""
        verification_result = Mock()
        verification_result.verification_command = "pytest tests/"
        verification_result.verification_time = 3.5

        with patch.object(logger, "logger") as mock_logger:
            logger.log_verify_success(
                duration=3.5,
                verification_result=verification_result,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "passed" in str(call_args).lower()

    def test_log_verify_error(self, logger: StepLogger) -> None:
        """Test logging verification error."""
        error = AssertionError("Verification failed")

        with patch.object(logger, "logger") as mock_logger:
            logger.log_verify_error(duration=1.0, error=error)

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "failed" in str(call_args).lower()

    def test_log_commit_start(self, logger: StepLogger) -> None:
        """Test logging commit start."""
        with patch.object(logger, "logger") as mock_logger:
            logger.log_commit_start(message_preview="🔴 Add failing test")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Commit:" in str(call_args)

    def test_log_commit_success(self, logger: StepLogger) -> None:
        """Test logging successful commit creation."""
        commit_result = Mock()
        commit_result.sha = "abc1234567890def"
        commit_result.message = "🔴 Add failing test\n\nDetails here"

        with patch.object(logger, "logger") as mock_logger:
            logger.log_commit_success(
                duration=1.5,
                commit_result=commit_result,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "success" in str(call_args).lower()

    def test_log_commit_error(self, logger: StepLogger) -> None:
        """Test logging commit creation error."""
        error = RuntimeError("Git commit failed")

        with patch.object(logger, "logger") as mock_logger:
            logger.log_commit_error(duration=0.5, error=error)

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "failed" in str(call_args).lower()

    def test_log_step_complete(self, logger: StepLogger) -> None:
        """Test logging step completion."""
        with patch.object(logger, "logger") as mock_logger:
            logger.log_step_complete(
                duration=18.5,
                commit_sha="abc1234567890def",
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "complete" in str(call_args).lower()
            assert "tdd_red" in str(call_args).lower()

    def test_log_step_error(self, logger: StepLogger) -> None:
        """Test logging step error."""
        error = RuntimeError("Step execution failed")

        with patch.object(logger, "logger") as mock_logger:
            logger.log_step_error(duration=10.0, error=error)

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "failed" in str(call_args).lower()

    def test_json_output_file_written(self, logger: StepLogger, tmp_path: Path) -> None:
        """Test that JSON logs are written to file."""
        logger.log_file = tmp_path / "test-logs.jsonl"

        # Create a phase log
        phase_log = PhaseLog(
            phase="command",
            event="success",
            timestamp=datetime.now().isoformat(),
            duration_s=5.0,
        )

        logger._write_json_log(phase_log)

        # Verify file was created and contains valid JSON
        assert logger.log_file.exists()
        content = logger.log_file.read_text()
        parsed = json.loads(content.strip())
        assert parsed["phase"] == "command"
        assert parsed["event"] == "success"

    def test_multiple_json_logs_appended(self, logger: StepLogger, tmp_path: Path) -> None:
        """Test that multiple JSON logs are appended to file."""
        logger.log_file = tmp_path / "test-logs.jsonl"

        # Write multiple logs
        for i in range(3):
            log = PhaseLog(
                phase="command",
                event="start",
                timestamp=datetime.now().isoformat(),
                duration_s=float(i),
            )
            logger._write_json_log(log)

        # Verify all logs were written
        content = logger.log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 3

        # Verify each line is valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "phase" in parsed
            assert "event" in parsed

    def test_json_log_write_error_handling(self, logger: StepLogger, tmp_path: Path) -> None:
        """Test graceful handling of JSON write errors."""
        # Set log file to an invalid path
        logger.log_file = Path("/invalid/path/that/does/not/exist.jsonl")

        with patch.object(logger, "logger") as mock_logger:
            # Should not raise, but should log an error
            phase_log = PhaseLog(
                phase="command",
                event="start",
                timestamp=datetime.now().isoformat(),
            )
            logger._write_json_log(phase_log)

            # Logger.exception should have been called
            mock_logger.exception.assert_called_once()

    def test_log_context_variable_set(self, logger: StepLogger) -> None:
        """Test that context variables are set for this step."""
        with patch("jiro.steps.logging.set_context_var") as mock_set_context:
            StepLogger(StepType.TDD_GREEN)

            # Verify context variable was set
            mock_set_context.assert_called()
            call_args = mock_set_context.call_args
            assert call_args[0][0] == "step_type"
            assert call_args[0][1] == str(StepType.TDD_GREEN)


class TestStepLoggerIntegration:
    """Integration tests for StepLogger with real file operations."""

    def test_full_step_logging_flow(self, tmp_path: Path) -> None:
        """Test complete logging flow for a step."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        with (
            patch("jiro.steps.logging.get_logs_dir", return_value=logs_dir),
            patch("jiro.steps.logging.structlog.get_logger"),
        ):
            logger = StepLogger(StepType.TDD_RED)
            logger.log_file = logs_dir / "steps-test.jsonl"

            # Simulate a complete step execution flow
            logger.log_step_start()
            time.sleep(0.01)

            logger.log_command_start()
            time.sleep(0.01)

            result = Mock(spec=Result)
            result.changed_files = [Path("test.py")]
            logger.log_command_success(0.05, result)

            logger.log_verify_start()
            time.sleep(0.01)

            verification_result = Mock()
            verification_result.verification_command = "pytest"
            verification_result.verification_time = 0.02
            logger.log_verify_success(0.03, verification_result)

            logger.log_commit_start()
            time.sleep(0.01)

            commit_result = Mock()
            commit_result.sha = "abc123"
            commit_result.message = "Test commit"
            logger.log_commit_success(0.02, commit_result)

            logger.log_step_complete(0.15, "abc123")

            # Verify log file contains all entries
            assert logger.log_file.exists()
            content = logger.log_file.read_text()
            lines = content.strip().split("\n")

            # Should have at least: step_start, command_start, command_success,
            # verify_start, verify_success, commit_start, commit_success, step_complete
            assert len(lines) >= 8

            # Verify JSON structure of each line
            for line in lines:
                parsed = json.loads(line)
                assert "timestamp" in parsed
                assert "event" in parsed
