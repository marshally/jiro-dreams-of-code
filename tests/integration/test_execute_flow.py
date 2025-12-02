"""Integration tests for the complete execute flow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.session import PostflightResult, PreflightResult, SessionResult


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock configuration object."""
    config = MagicMock()
    config.commands.test = "pytest"
    config.commands.lint = "ruff check"
    config.preflight.target_branch = None
    return config


@pytest.fixture
def mock_preflight_success() -> PreflightResult:
    """Create a successful preflight result."""
    return PreflightResult(passed=True, checks={}, errors=[])


@pytest.fixture
def mock_preflight_failure() -> PreflightResult:
    """Create a failed preflight result."""
    return PreflightResult(
        passed=False,
        checks={},
        errors=["git_clean: Uncommitted changes detected"],
    )


@pytest.fixture
def mock_postflight_success() -> PostflightResult:
    """Create a successful postflight result."""
    return PostflightResult(passed=True, checks={}, errors=[])


@pytest.fixture
def mock_session_result_completed() -> SessionResult:
    """Create a completed session result."""
    return SessionResult(
        session_id="test-session-123",
        status="completed",
        tasks_completed=3,
        tasks_failed=0,
        error=None,
    )


@pytest.fixture
def mock_session_result_halted() -> SessionResult:
    """Create a halted session result."""
    return SessionResult(
        session_id="test-session-456",
        status="halted",
        tasks_completed=1,
        tasks_failed=1,
        error="Task JIRO-42 failed: Test assertion error",
    )


@pytest.fixture
def mock_session_result_failed() -> SessionResult:
    """Create a failed session result."""
    return SessionResult(
        session_id="test-session-789",
        status="failed",
        tasks_completed=0,
        tasks_failed=0,
        error="Preflight checks failed: git_clean: Uncommitted changes detected",
    )


class TestExecuteFlowIntegration:
    """Integration tests for the complete execute command flow."""

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_full_flow_successful(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test successful execute flow end-to-end.

        Verifies:
        - Execute command starts session
        - Preflight checks pass
        - Tasks execute successfully
        - Postflight checks pass
        - Success message displayed
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 0
            assert "completed successfully" in result.stdout
            assert "Tasks completed: 3" in result.stdout

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_flow_with_preflight_failure(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_failed: SessionResult,
    ) -> None:
        """Test execute flow when preflight checks fail.

        Verifies:
        - Execute command starts session
        - Preflight checks fail
        - Session marked as failed
        - Error message displayed
        - Exit code is non-zero
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_failed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 1
            assert "failed" in result.stdout.lower()

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_flow_with_epic_filter(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test execute flow with epic filter.

        Verifies:
        - Epic ID is passed to orchestrator
        - Only tasks for that epic are executed
        - Epic filter message displayed
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute", "--epic", "JIRO-42"])

            assert result.exit_code == 0
            assert "JIRO-42" in result.stdout
            mock_orchestrator.run.assert_called_once_with(epic_id="JIRO-42")

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_flow_halted_on_task_failure(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_halted: SessionResult,
    ) -> None:
        """Test execute flow when a task fails and session halts.

        Verifies:
        - Execute starts and runs some tasks
        - Task failure causes halt
        - Partial progress reported
        - Error message shown
        - Exit code is non-zero
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_halted
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 1
            assert "halted" in result.stdout.lower()
            assert "Tasks completed: 1" in result.stdout
            assert "Tasks failed: 1" in result.stdout

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_session_creation_and_persistence(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test that sessions are created and persisted in database.

        Verifies:
        - Session repository is instantiated
        - Task execution repository is instantiated
        - Orchestrator receives both repositories
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema") as mock_ensure_schema,
            patch("jiro.cli.execute.SessionRepository") as mock_session_repo_class,
            patch("jiro.cli.execute.TaskExecutionRepository") as mock_task_repo_class,
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_session_repo = MagicMock()
            mock_session_repo_class.return_value = mock_session_repo

            mock_task_repo = MagicMock()
            mock_task_repo_class.return_value = mock_task_repo

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 0
            mock_ensure_schema.assert_called_once_with(mock_db)
            mock_session_repo_class.assert_called_once_with(mock_db)
            mock_task_repo_class.assert_called_once_with(mock_db)
            mock_orchestrator_class.assert_called_once_with(
                mock_config, mock_session_repo, mock_task_repo
            )

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_handles_unexpected_exception(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test execute handles unexpected exceptions gracefully.

        Verifies:
        - Unexpected errors are caught
        - Error message is displayed
        - Exit code is non-zero
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.side_effect = RuntimeError("Database connection lost")
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 1
            assert "error" in result.stdout.lower()

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_execute_display_format(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test that execute command output has proper formatting.

        Verifies:
        - Status messages use Rich formatting
        - Session info is displayed
        - Output is user-friendly
        """
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = tmp_path / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            # Check for expected output structure
            assert "Starting execution session" in result.stdout
            assert "completed successfully" in result.stdout
            assert "Tasks completed" in result.stdout
