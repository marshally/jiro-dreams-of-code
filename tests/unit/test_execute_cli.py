"""Tests for execute CLI command."""

from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.session import SessionResult


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


class TestExecuteCommand:
    """Tests for execute command."""

    @pytest.mark.unit
    def test_execute_help(self, cli_runner: CliRunner) -> None:
        """Execute command should display help."""
        result = cli_runner.invoke(app, ["execute", "--help"])
        assert result.exit_code == 0
        assert "execute" in result.stdout.lower() or "Execute" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_creates_session(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should create and run a session."""
        # Setup mocks
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=5,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute"])

        assert result.exit_code == 0
        assert mock_orchestrator.run.called

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_with_epic_filter(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should pass epic filter to orchestrator."""
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=3,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute", "--epic", "EPIC-42"])

        assert result.exit_code == 0
        mock_orchestrator.run.assert_called_with(epic_id="EPIC-42")

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_halted_exits_with_error(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should exit with code 1 when session is halted."""
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="halted",
            tasks_completed=2,
            tasks_failed=1,
            error="Task failed: test error",
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute"])

        assert result.exit_code == 1
        assert "halted" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_failed_exits_with_error(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should exit with code 1 when session fails."""
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="failed",
            tasks_completed=0,
            tasks_failed=0,
            error="Preflight checks failed",
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_displays_task_counts(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should display task counts in output."""
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=5,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute"])

        assert result.exit_code == 0
        assert "5" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_shows_epic_in_output(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute should show epic filter in output when provided."""
        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=3,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute", "--epic", "EPIC-42"])

        assert result.exit_code == 0
        assert "EPIC-42" in result.stdout
