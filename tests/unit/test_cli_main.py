"""Tests for CLI main module and logging initialization."""

import logging
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
    @patch("jiro.cli.main.fix_missing_directories")
    @patch("jiro.cli.main.run_doctor")
    def test_doctor_fix_option(
        self, mock_run_doctor, mock_fix_dirs, mock_fix_config, cli_runner: CliRunner
    ) -> None:
        """Doctor command should apply fixes when --fix is specified."""
        from pathlib import Path

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
            "directories": CheckResult("directories", False, "Missing directories"),
        }
        mock_run_doctor.return_value = DoctorResult(
            passed=False,
            checks=mock_checks,
            errors=["directories: Missing directories"],
        )
        mock_fix_dirs.return_value = [Path("/tmp/src"), Path("/tmp/tests")]
        mock_fix_config.return_value = False

        result = cli_runner.invoke(app, ["doctor", "--fix"])
        # Should still exit with 1 because there were failures, but fixes were attempted
        assert result.exit_code == 1
        mock_fix_dirs.assert_called_once()
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
        """Dream command should show not implemented message."""
        result = cli_runner.invoke(app, ["dream", "test prompt"])
        assert result.exit_code == 0
        assert "not implemented" in result.stdout.lower()

    @pytest.mark.unit
    def test_dream_with_prompt(self, cli_runner: CliRunner) -> None:
        """Dream command should accept prompt argument."""
        result = cli_runner.invoke(app, ["dream", "build a feature"])
        assert result.exit_code == 0
        assert "build a feature" in result.stdout

    @pytest.mark.unit
    def test_dream_with_model(self, cli_runner: CliRunner) -> None:
        """Dream command should display model when provided."""
        result = cli_runner.invoke(app, ["dream", "--model", "claude-opus-4", "test"])
        assert result.exit_code == 0
        assert "claude-opus-4" in result.stdout


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
    def test_plan_not_implemented(self, cli_runner: CliRunner) -> None:
        """Plan command should show not implemented message."""
        result = cli_runner.invoke(app, ["plan", "--spec", "test.md"])
        assert result.exit_code == 0
        assert "not implemented" in result.stdout.lower()

    @pytest.mark.unit
    def test_plan_with_spec(self, cli_runner: CliRunner) -> None:
        """Plan command should display spec path."""
        result = cli_runner.invoke(app, ["plan", "--spec", "specs/auth.md"])
        assert result.exit_code == 0
        assert "specs/auth.md" in result.stdout

    @pytest.mark.unit
    def test_plan_with_refinement(self, cli_runner: CliRunner) -> None:
        """Plan command should display refinement when provided."""
        result = cli_runner.invoke(app, ["plan", "--spec", "specs/auth.md", "focus on security"])
        assert result.exit_code == 0
        assert "focus on security" in result.stdout


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
    def test_execute_not_implemented(self, cli_runner: CliRunner) -> None:
        """Execute command should show not implemented message."""
        result = cli_runner.invoke(app, ["execute"])
        assert result.exit_code == 0
        assert "not implemented" in result.stdout.lower()

    @pytest.mark.unit
    def test_execute_with_epic(self, cli_runner: CliRunner) -> None:
        """Execute command should display epic when provided."""
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

    @pytest.mark.unit
    def test_web_not_implemented(self, cli_runner: CliRunner) -> None:
        """Web command should show not implemented message."""
        result = cli_runner.invoke(app, ["web"])
        assert result.exit_code == 0
        assert "not implemented" in result.stdout.lower()

    @pytest.mark.unit
    def test_web_with_port(self, cli_runner: CliRunner) -> None:
        """Web command should display custom port."""
        result = cli_runner.invoke(app, ["web", "--port", "9000"])
        assert result.exit_code == 0
        assert "9000" in result.stdout

    @pytest.mark.unit
    def test_web_with_daemon(self, cli_runner: CliRunner) -> None:
        """Web command should display daemon info."""
        result = cli_runner.invoke(app, ["web", "--daemon"])
        assert result.exit_code == 0
        assert "background" in result.stdout.lower()
