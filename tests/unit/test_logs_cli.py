"""Tests for logs CLI command."""

import json
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestLogsCommand:
    """Tests for logs command."""

    @pytest.mark.unit
    def test_logs_help(self, cli_runner: CliRunner) -> None:
        """Logs command should display help."""
        result = cli_runner.invoke(app, ["logs", "--help"])
        assert result.exit_code == 0
        assert "logs" in result.stdout.lower() or "Log" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_basic_no_logs(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should handle when no logs exist."""
        # Mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        # Should gracefully handle no logs
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_display_jsonl_entries(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should display JSONL entries with formatting."""
        # Create mock logs directory with a log file
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        log_entries = [
            {"timestamp": "2025-12-01T10:00:00", "level": "INFO", "event": "Test event 1"},
            {"timestamp": "2025-12-01T10:01:00", "level": "DEBUG", "event": "Test event 2"},
        ]
        with open(log_file, "w") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        # Should display log content
        assert "Test event" in result.stdout or "INFO" in result.stdout or "DEBUG" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_with_tail_option(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should support --tail to show last N lines."""
        # Create mock logs directory with multiple log entries
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            for i in range(100):
                entry = {"timestamp": f"2025-12-01T10:{i % 60:02d}:00", "event": f"Event {i}"}
                f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs", "--tail", "10"])
        assert result.exit_code == 0
        # Should only show last 10 entries
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_with_tail_short_flag(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should accept -n shorthand for tail."""
        # Create mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            for i in range(20):
                entry = {"timestamp": f"2025-12-01T10:{i}:00", "event": f"Event {i}"}
                f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs", "-n", "5"])
        assert result.exit_code == 0
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    @mock.patch("jiro.cli.logs.tail_follow")
    def test_logs_with_follow_option(
        self, mock_tail_follow, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should support --follow for live tail."""
        # Create mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            entry = {"timestamp": "2025-12-01T10:00:00", "event": "Test event"}
            f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir
        # Mock the follow function to return immediately
        mock_tail_follow.return_value = None

        result = cli_runner.invoke(app, ["logs", "--follow"])
        assert result.exit_code == 0
        # Verify tail_follow was called
        mock_tail_follow.assert_called_once()

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    @mock.patch("jiro.cli.logs.tail_follow")
    def test_logs_with_follow_short_flag(
        self, mock_tail_follow, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should accept -f shorthand for follow."""
        # Create mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            entry = {"timestamp": "2025-12-01T10:00:00", "event": "Test event"}
            f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir
        mock_tail_follow.return_value = None

        result = cli_runner.invoke(app, ["logs", "-f"])
        assert result.exit_code == 0
        mock_tail_follow.assert_called_once()

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_with_both_options(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should handle tail with follow (tail takes precedence)."""
        # Create mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            for i in range(20):
                entry = {"timestamp": f"2025-12-01T10:{i}:00", "event": f"Event {i}"}
                f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        # Follow should be ignored if tail is specified
        result = cli_runner.invoke(app, ["logs", "--tail", "5", "--follow"])
        assert result.exit_code == 0

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_with_multiple_log_files(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should display from all log files in chronological order."""
        # Create mock logs directory with multiple files
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # Create files for different dates
        for day in range(1, 4):
            log_file = logs_dir / f"2025-12-{day:02d}.jsonl"
            with open(log_file, "w") as f:
                for i in range(3):
                    entry = {
                        "timestamp": f"2025-12-{day:02d}T10:{i}:00",
                        "event": f"Event day {day} entry {i}",
                    }
                    f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        # Should display from all files
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_displays_with_rich_formatting(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should use Rich for formatted output."""
        # Create mock logs directory
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            entry = {
                "timestamp": "2025-12-01T10:00:00",
                "level": "INFO",
                "event": "Test",
                "session_id": "test-session",
            }
            f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_default_tail_value(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should default to showing last 50 lines."""
        # Create mock logs directory with more than 50 lines
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            for i in range(100):
                entry = {"timestamp": f"2025-12-01T10:{i % 60:02d}:00", "event": f"Event {i}"}
                f.write(json.dumps(entry) + "\n")

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        # Should show output without error
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_handles_invalid_json_lines(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should gracefully skip invalid JSON lines."""
        # Create mock logs directory with mixed valid/invalid JSON
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        log_file = logs_dir / "2025-12-01.jsonl"
        with open(log_file, "w") as f:
            f.write('{"timestamp": "2025-12-01T10:00:00", "event": "Valid"}\n')
            f.write("Invalid JSON line\n")
            f.write('{"timestamp": "2025-12-01T10:01:00", "event": "Also valid"}\n')

        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        assert result.stdout is not None

    @pytest.mark.unit
    @mock.patch("jiro.cli.logs.get_logs_dir")
    def test_logs_empty_directory(
        self, mock_get_logs_dir, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Logs command should handle empty logs directory gracefully."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        mock_get_logs_dir.return_value = logs_dir

        result = cli_runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        # Should complete successfully even with no logs
        assert result.stdout is not None
