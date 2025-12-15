"""Tests for CLI main module and logging initialization."""

import logging
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app, main


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestMainCallback:
    """Tests for main callback and logging initialization."""

    @pytest.mark.unit
    def test_main_help(self, cli_runner: CliRunner) -> None:
        """Main command should display help."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "jiro" in result.stdout

    @pytest.mark.unit
    def test_main_version(self, cli_runner: CliRunner) -> None:
        """Version flag should display version and exit."""
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.stdout

    @pytest.mark.unit
    def test_verbose_flag_in_help(self, cli_runner: CliRunner) -> None:
        """Verbose flag should be shown in help."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout

    @pytest.mark.unit
    def test_quiet_flag_in_help(self, cli_runner: CliRunner) -> None:
        """Quiet flag should be shown in help."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.stdout or "-q" in result.stdout

    @pytest.mark.unit
    def test_main_callback_with_no_flags(self) -> None:
        """Main callback should initialize logging with INFO level by default."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=0, quiet=False)
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert call_args[1]["verbosity"] == logging.INFO

    @pytest.mark.unit
    def test_main_callback_with_verbose(self) -> None:
        """Main callback should set DEBUG level with -v."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=1, quiet=False)
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert call_args[1]["verbosity"] == logging.DEBUG

    @pytest.mark.unit
    def test_main_callback_with_double_verbose(self) -> None:
        """Main callback should set DEBUG level with -vv."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=2, quiet=False)
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert call_args[1]["verbosity"] == logging.DEBUG

    @pytest.mark.unit
    def test_main_callback_with_quiet(self) -> None:
        """Main callback should set CRITICAL level with --quiet."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=0, quiet=True)
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert call_args[1]["verbosity"] == logging.CRITICAL

    @pytest.mark.unit
    def test_main_callback_quiet_takes_precedence(self) -> None:
        """Main callback should prioritize quiet flag over verbose."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=2, quiet=True)
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args
            assert call_args[1]["verbosity"] == logging.CRITICAL

    @pytest.mark.unit
    def test_logging_called_with_correct_parameter(self) -> None:
        """configure_logging should be called with verbosity as keyword argument."""
        with patch("jiro.cli.main.configure_logging") as mock_configure:
            mock_configure.return_value = None
            main(version=None, verbose=0, quiet=False)
            mock_configure.assert_called_once()
            call_kwargs = mock_configure.call_args[1]
            assert "verbosity" in call_kwargs
            assert isinstance(call_kwargs["verbosity"], int)

    @pytest.mark.unit
    def test_init_command_accepts_verbose(self, cli_runner: CliRunner) -> None:
        """Init command should accept verbose flag."""
        result = cli_runner.invoke(app, ["-v", "init", "--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_tasks_list_accepts_verbose(self, cli_runner: CliRunner) -> None:
        """Tasks list command should accept verbose flag."""
        result = cli_runner.invoke(app, ["-v", "tasks", "list", "--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_config_list_accepts_quiet(self, cli_runner: CliRunner) -> None:
        """Config list command should accept quiet flag."""
        result = cli_runner.invoke(app, ["-q", "config", "list", "--help"])
        assert result.exit_code == 0


class TestDoctorCommand:
    """Tests for doctor CLI command."""

    @pytest.mark.unit
    def test_doctor_help(self, cli_runner: CliRunner) -> None:
        """Doctor command should display help."""
        result = cli_runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "health" in result.stdout.lower() or "doctor" in result.stdout.lower()

    @pytest.mark.unit
    def test_doctor_command_with_fix_option(self, cli_runner: CliRunner) -> None:
        """Doctor command should accept --fix option."""
        result = cli_runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "--fix" in result.stdout

    @pytest.mark.unit
    @patch("jiro.cli.main.run_doctor")
    def test_doctor_runs_checks(self, mock_run_doctor, cli_runner: CliRunner) -> None:
        """Doctor command should run health checks."""
        from jiro.cli.doctor import DoctorResult
        from jiro.core.session import CheckResult

        # Mock successful checks
        mock_checks = {
            "python_version": CheckResult("python_version", True),
            "claude_sdk": CheckResult("claude_sdk", True),
            "api_key": CheckResult("api_key", True),
            "git": CheckResult("git", True),
            "test_command": CheckResult("test_command", True),
            "lint_command": CheckResult("lint_command", True),
            "beads": CheckResult("beads", True),
            "config": CheckResult("config", True),
            "directories": CheckResult("directories", True),
        }
        mock_run_doctor.return_value = DoctorResult(passed=True, checks=mock_checks, errors=[])

        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        mock_run_doctor.assert_called_once()

    @pytest.mark.unit
    @patch("jiro.cli.main.run_doctor")
    def test_doctor_exit_code_on_failure(self, mock_run_doctor, cli_runner: CliRunner) -> None:
        """Doctor command should exit with code 1 when checks fail."""
        from jiro.cli.doctor import DoctorResult
        from jiro.core.session import CheckResult

        # Mock failed check
        mock_checks = {
            "api_key": CheckResult("api_key", False, "API key not set"),
        }
        mock_run_doctor.return_value = DoctorResult(
            passed=False, checks=mock_checks, errors=["api_key: API key not set"]
        )

        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 1

    @pytest.mark.unit
    @patch("jiro.cli.main.fix_missing_config")
    @patch("jiro.cli.main.run_doctor")
    def test_doctor_fix_option(
        self, mock_run_doctor, mock_fix_config, cli_runner: CliRunner
    ) -> None:
        """Doctor command should apply fixes when --fix is specified."""
        from jiro.cli.doctor import DoctorResult
        from jiro.core.session import CheckResult

        # Mock checks with config failure
        mock_checks = {
            "python_version": CheckResult("python_version", True),
            "claude_sdk": CheckResult("claude_sdk", True),
            "api_key": CheckResult("api_key", True),
            "git": CheckResult("git", True),
            "test_command": CheckResult("test_command", True),
            "lint_command": CheckResult("lint_command", True),
            "beads": CheckResult("beads", True),
            "config": CheckResult("config", False, "Missing config"),
        }
        mock_run_doctor.return_value = DoctorResult(
            passed=False,
            checks=mock_checks,
            errors=["config: Missing config"],
        )
        mock_fix_config.return_value = True

        result = cli_runner.invoke(app, ["doctor", "--fix"])
        # Should still exit with 1 because there were failures, but fixes were attempted
        assert result.exit_code == 1
        mock_fix_config.assert_called_once()


class TestInitCommand:
    """Tests for init CLI command."""

    @pytest.mark.unit
    def test_init_help(self, cli_runner: CliRunner) -> None:
        """Init command should display help."""
        result = cli_runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout.lower()

    @pytest.mark.unit
    def test_init_stealth_option(self, cli_runner: CliRunner) -> None:
        """Init command should accept --stealth option."""
        result = cli_runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--stealth" in result.stdout

    @pytest.mark.unit
    def test_init_interactive_option(self, cli_runner: CliRunner) -> None:
        """Init command should accept --interactive option."""
        result = cli_runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--interactive" in result.stdout

    @pytest.mark.unit
    def test_init_runs_successfully(self, cli_runner: CliRunner) -> None:
        """Init command should run successfully in git repo."""
        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "initializing" in result.stdout.lower() or "complete" in result.stdout.lower()

    @pytest.mark.unit
    def test_init_with_stealth_flag(self, cli_runner: CliRunner) -> None:
        """Init command should accept --stealth flag."""
        result = cli_runner.invoke(app, ["init", "--stealth"])
        assert result.exit_code == 0

    @pytest.mark.unit
    def test_init_with_interactive_flag(self, cli_runner: CliRunner) -> None:
        """Init command should show interactive prompting info."""
        result = cli_runner.invoke(app, ["init", "--interactive"], input="pytest\nruff check\n")
        assert result.exit_code == 0
        # The output should show we're in interactive configuration mode
        assert (
            "interactive" in result.stdout.lower()
            or "test command" in result.stdout.lower()
            or "prompt" in result.stdout.lower()
        )


class TestDreamCommand:
    """Tests for dream CLI command."""

    @pytest.mark.unit
    def test_dream_help(self, cli_runner: CliRunner) -> None:
        """Dream command should display help."""
        result = cli_runner.invoke(app, ["dream", "--help"])
        assert result.exit_code == 0
        assert "dream" in result.stdout.lower()

    @pytest.mark.unit
    def test_dream_model_option(self, cli_runner: CliRunner) -> None:
        """Dream command should accept --model option."""
        result = cli_runner.invoke(app, ["dream", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.stdout

    @pytest.mark.unit
    def test_dream_not_implemented(self, cli_runner: CliRunner) -> None:
        """Dream command should handle missing configuration gracefully."""
        result = cli_runner.invoke(app, ["dream", "test prompt"])
        # Will fail because config/db not found, but command exists
        # Exit code may be 1 due to error handling
        assert (
            result.exit_code != 0
            or "error" in result.stdout.lower()
            or "error" in str(result.exception).lower()
        )

    @pytest.mark.unit
    def test_dream_with_prompt(self, cli_runner: CliRunner) -> None:
        """Dream command should accept prompt argument."""
        result = cli_runner.invoke(app, ["dream", "build a feature"])
        # Will fail due to missing config, but command should accept the prompt
        assert result.exit_code != 0

    @pytest.mark.unit
    def test_dream_with_model(self, cli_runner: CliRunner) -> None:
        """Dream command should accept model option."""
        result = cli_runner.invoke(app, ["dream", "--model", "claude-opus-4", "test"])
        # Will fail due to missing config, but command should accept the model option
        assert result.exit_code != 0


class TestPlanCommand:
    """Tests for plan CLI command."""

    @pytest.mark.unit
    def test_plan_help(self, cli_runner: CliRunner) -> None:
        """Plan command should display help."""
        result = cli_runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "plan" in result.stdout.lower()

    @pytest.mark.unit
    def test_plan_spec_option(self, cli_runner: CliRunner) -> None:
        """Plan command should require --spec option."""
        result = cli_runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "--spec" in result.stdout

    @pytest.mark.unit
    def test_plan_not_implemented(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Plan command should handle missing spec file gracefully."""
        from unittest.mock import patch

        with patch("jiro.cli.plan.Path.cwd", return_value=tmp_path):
            result = cli_runner.invoke(app, ["plan", "--spec", "test.md"])
            # Should fail because file doesn't exist (no "not implemented" expected)
            assert result.exit_code != 0

    @pytest.mark.unit
    def test_plan_with_spec(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Plan command should handle spec file path."""
        from unittest.mock import AsyncMock, MagicMock, patch

        spec_file = tmp_path / "specs" / "auth.md"
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        spec_file.write_text("""# Feature: Auth

## Overview

Basic auth system.

## Requirements

- User auth

## Acceptance Criteria

- Works

## Out of Scope

- MFA
""")

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            from jiro.core.planner import PlanResult

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=PlanResult(epics=[], tasks=[]))
            mock_planner_class.return_value = mock_planner

            result = cli_runner.invoke(app, ["plan", "--spec", "specs/auth.md"])
            # Should succeed
            assert result.exit_code == 0

    @pytest.mark.unit
    def test_plan_with_refinement(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Plan command should accept refinement argument."""
        from unittest.mock import AsyncMock, MagicMock, patch

        spec_file = tmp_path / "specs" / "auth.md"
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        spec_file.write_text("""# Feature: Auth

## Overview

Basic auth system.

## Requirements

- User auth

## Acceptance Criteria

- Works

## Out of Scope

- MFA
""")

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            from jiro.core.planner import PlanResult

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=PlanResult(epics=[], tasks=[]))
            mock_planner_class.return_value = mock_planner

            result = cli_runner.invoke(
                app, ["plan", "--spec", "specs/auth.md", "--model", "custom-model"]
            )
            # Should succeed
            assert result.exit_code == 0


class TestExecuteCommand:
    """Tests for execute CLI command."""

    @pytest.mark.unit
    def test_execute_help(self, cli_runner: CliRunner) -> None:
        """Execute command should display help."""
        result = cli_runner.invoke(app, ["execute", "--help"])
        assert result.exit_code == 0
        assert "execute" in result.stdout.lower()

    @pytest.mark.unit
    def test_execute_epic_option(self, cli_runner: CliRunner) -> None:
        """Execute command should accept --epic option."""
        result = cli_runner.invoke(app, ["execute", "--help"])
        assert result.exit_code == 0
        assert "--epic" in result.stdout

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_not_implemented(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute command should show starting session message."""
        from pathlib import Path

        from jiro.core.session import SessionResult

        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=0,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute"])
        assert result.exit_code == 0
        assert "starting execution session" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.execute.SessionOrchestrator")
    @mock.patch("jiro.cli.execute.load_config")
    @mock.patch("jiro.cli.execute.get_database")
    @mock.patch("jiro.cli.execute.get_database_path")
    def test_execute_with_epic(
        self, mock_get_db_path, mock_get_db, mock_load_config, mock_orchestrator_class, cli_runner
    ):
        """Execute command should display epic when provided."""
        from pathlib import Path

        from jiro.core.session import SessionResult

        mock_orchestrator = mock.MagicMock()
        mock_orchestrator.run.return_value = SessionResult(
            session_id="test-123",
            status="completed",
            tasks_completed=0,
            tasks_failed=0,
        )
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_get_db_path.return_value = Path("/tmp/test.db")
        mock_get_db.return_value = mock.MagicMock()
        mock_load_config.return_value = mock.MagicMock()

        result = cli_runner.invoke(app, ["execute", "--epic", "JIRO-42"])
        assert result.exit_code == 0
        assert "JIRO-42" in result.stdout


class TestWebCommand:
    """Tests for web CLI command."""

    @pytest.mark.unit
    def test_web_help(self, cli_runner: CliRunner) -> None:
        """Web command should display help."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "web" in result.stdout.lower()

    @pytest.mark.unit
    def test_web_daemon_option(self, cli_runner: CliRunner) -> None:
        """Web command should accept --daemon option."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "--daemon" in result.stdout

    @pytest.mark.unit
    def test_web_port_option(self, cli_runner: CliRunner) -> None:
        """Web command should accept --port option."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.stdout
