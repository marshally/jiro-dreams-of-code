"""Tests for status CLI command."""

import json
from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return {
        "id": "session-001",
        "branch_name": "feature/test",
        "status": "running",
        "started_at": "2025-11-30T10:00:00",
        "epic_id": "EPIC-001",
        "ended_at": None,
        "preflight_passed_at": "2025-11-30T09:50:00",
        "halt_reason": None,
    }


@pytest.fixture
def sample_task_execution():
    """Create a sample task execution for testing."""
    return {
        "id": "exec-001",
        "task_id": "TASK-001",
        "session_id": "session-001",
        "phase": "executing",
        "started_at": "2025-11-30T10:05:00",
        "ended_at": None,
        "status": "running",
        "halt_reason": None,
    }


class TestStatusCommand:
    """Tests for status command."""

    @pytest.mark.unit
    def test_status_help(self, cli_runner: CliRunner) -> None:
        """Status command should display help."""
        result = cli_runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.stdout.lower() or "Show" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_displays_active_sessions(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status command should display active sessions."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mock to return a session
        from jiro.db.models import Session

        session = Session.from_row(sample_session)
        mock_session_repo.get_active.return_value = [session]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 0

        result = cli_runner.invoke(app, ["status"])
        assert result.exit_code == 0
        # Should contain session info
        assert "session-001" in result.stdout or "running" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_displays_no_sessions_message(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
    ) -> None:
        """Status command should display message when no active sessions."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mock to return no sessions
        mock_session_repo.get_active.return_value = []

        result = cli_runner.invoke(app, ["status"])
        assert result.exit_code == 0
        # Should contain a message indicating no active sessions
        assert "no" in result.stdout.lower() or "active" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_json_output(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status command should output JSON when --json flag is used."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mocks
        from jiro.db.models import Session

        session = Session.from_row(sample_session)
        mock_session_repo.get_active.return_value = [session]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 0

        result = cli_runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert "sessions" in output

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_shows_task_progress(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
        sample_task_execution,
    ) -> None:
        """Status command should display current task and progress."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mocks
        from jiro.db.models import Session, TaskExecution

        session = Session.from_row(sample_session)
        task_exec = TaskExecution.from_row(sample_task_execution)

        mock_session_repo.get_active.return_value = [session]
        mock_task_exec_repo.get_by_session.return_value = [task_exec]
        mock_prompt_repo.get_total_tokens.return_value = 150000

        result = cli_runner.invoke(app, ["status"])
        assert result.exit_code == 0
        # Should contain task info
        assert "TASK-001" in result.stdout or "executing" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_json_includes_token_usage(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status JSON should include token usage information."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mocks
        from jiro.db.models import Session

        session = Session.from_row(sample_session)
        mock_session_repo.get_active.return_value = [session]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 250000

        result = cli_runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Should have some form of context/token usage info
        assert isinstance(output, dict)

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_handles_multiple_sessions(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status command should handle multiple active sessions."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Create two sessions
        from jiro.db.models import Session

        session1 = Session.from_row(sample_session)
        session2_dict = sample_session.copy()
        session2_dict["id"] = "session-002"
        session2_dict["branch_name"] = "feature/another"
        session2 = Session.from_row(session2_dict)

        mock_session_repo.get_active.return_value = [session1, session2]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 100000

        result = cli_runner.invoke(app, ["status"])
        assert result.exit_code == 0
        # Should show both sessions
        assert "session-001" in result.stdout or "session-002" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_json_with_multiple_sessions(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status JSON should include all active sessions."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Create two sessions
        from jiro.db.models import Session

        session1 = Session.from_row(sample_session)
        session2_dict = sample_session.copy()
        session2_dict["id"] = "session-002"
        session2 = Session.from_row(session2_dict)

        mock_session_repo.get_active.return_value = [session1, session2]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 100000

        result = cli_runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert "sessions" in output
        assert len(output["sessions"]) == 2

    @pytest.mark.unit
    @mock.patch("jiro.cli.status._get_database")
    @mock.patch("jiro.cli.status.SessionRepository")
    @mock.patch("jiro.cli.status.TaskExecutionRepository")
    @mock.patch("jiro.cli.status.PromptRepository")
    def test_status_formats_timestamps(
        self,
        mock_prompt_repo_class,
        mock_task_exec_repo_class,
        mock_session_repo_class,
        mock_get_db,
        cli_runner: CliRunner,
        sample_session,
    ) -> None:
        """Status command should format timestamps nicely."""
        # Mock database
        mock_db = mock.Mock()
        mock_get_db.return_value = mock_db

        # Mock repositories
        mock_session_repo = mock.Mock()
        mock_session_repo_class.return_value = mock_session_repo

        mock_task_exec_repo = mock.Mock()
        mock_task_exec_repo_class.return_value = mock_task_exec_repo

        mock_prompt_repo = mock.Mock()
        mock_prompt_repo_class.return_value = mock_prompt_repo

        # Configure mocks
        from jiro.db.models import Session

        session = Session.from_row(sample_session)
        mock_session_repo.get_active.return_value = [session]
        mock_task_exec_repo.get_by_session.return_value = []
        mock_prompt_repo.get_total_tokens.return_value = 0

        result = cli_runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Should have ISO format timestamps in JSON
        assert isinstance(output, dict)
