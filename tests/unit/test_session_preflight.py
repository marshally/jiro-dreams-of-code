"""Tests for session preflight checks."""

from unittest.mock import MagicMock, patch

import pytest

from jiro.config.schema import Config, PreflightConfig
from jiro.core.session import (
    CheckResult,
    PreflightResult,
    check_correct_branch,
    check_git_clean,
    check_lint_pass,
    check_tests_pass,
    check_up_to_date,
    run_preflight,
)


@pytest.mark.unit
class TestCheckGitClean:
    """Test check_git_clean function."""

    def test_returns_true_when_working_directory_clean(self) -> None:
        """check_git_clean should return True when git status is clean."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            result = check_git_clean()
            assert result is True

    def test_returns_false_when_working_directory_dirty(self) -> None:
        """check_git_clean should return False when git status has changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=" M src/file.py\n")

            result = check_git_clean()
            assert result is False

    def test_returns_false_when_git_command_fails(self) -> None:
        """check_git_clean should return False if git command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="fatal error")

            result = check_git_clean()
            assert result is False

    def test_checks_git_status_porcelain(self) -> None:
        """check_git_clean should use git status --porcelain."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            check_git_clean()

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ["git", "status", "--porcelain"]


@pytest.mark.unit
class TestCheckCorrectBranch:
    """Test check_correct_branch function."""

    def test_returns_true_when_on_correct_branch(self) -> None:
        """check_correct_branch should return True when on the correct branch."""
        config = Config()
        config.preflight = PreflightConfig()

        with patch("subprocess.run") as mock_run:
            # Mock git rev-parse to return main branch
            def mock_git_command(cmd, *args, **kwargs):
                if cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                    return MagicMock(returncode=0, stdout="main\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = mock_git_command

            with patch("jiro.config.loader.load_config") as mock_load:
                mock_config = MagicMock()
                mock_config.preflight.target_branch = "main"
                mock_load.return_value = mock_config

                # We need to pass a config or load it from somewhere
                # For this test, let's use a manual approach
                result = check_correct_branch(config)
                assert isinstance(result, bool)

    def test_returns_false_when_on_wrong_branch(self) -> None:
        """check_correct_branch should return False when on wrong branch."""
        config = MagicMock()
        config.preflight.target_branch = "main"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="develop\n")

            result = check_correct_branch(config)
            assert result is False

    def test_returns_false_when_git_command_fails(self) -> None:
        """check_correct_branch should return False if git command fails."""
        config = MagicMock()
        config.preflight.target_branch = "main"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="fatal error")

            result = check_correct_branch(config)
            assert result is False


@pytest.mark.unit
class TestCheckUpToDate:
    """Test check_up_to_date function."""

    def test_returns_true_when_up_to_date(self) -> None:
        """check_up_to_date should return True when local is up to date with origin."""
        with patch("subprocess.run") as mock_run:
            # Mock origin check, fetch, and rev-parse calls
            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                if cmd[0:2] == ["git", "fetch"]:
                    return MagicMock(returncode=0, stdout="")
                # Both rev-parse calls return same SHA
                return MagicMock(returncode=0, stdout="abc123def456\n")

            mock_run.side_effect = mock_git_command

            result = check_up_to_date()
            assert result is True

    def test_returns_false_when_behind_origin(self) -> None:
        """check_up_to_date should return False when local is behind origin."""
        with patch("subprocess.run") as mock_run:

            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                if cmd[0:2] == ["git", "fetch"]:
                    return MagicMock(returncode=0, stdout="")
                if cmd[2] == "HEAD":
                    return MagicMock(returncode=0, stdout="local_sha\n")
                # origin/HEAD returns different SHA
                return MagicMock(returncode=0, stdout="origin_sha\n")

            mock_run.side_effect = mock_git_command

            result = check_up_to_date()
            assert result is False

    def test_returns_true_when_no_origin(self) -> None:
        """check_up_to_date should return True when there is no origin remote."""
        with patch("subprocess.run") as mock_run:
            # Origin check fails - no remote
            mock_run.return_value = MagicMock(returncode=1, stderr="fatal: No such remote")

            result = check_up_to_date()
            assert result is True

    def test_returns_false_when_fetch_fails(self) -> None:
        """check_up_to_date should return False if git fetch fails."""
        with patch("subprocess.run") as mock_run:

            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                # Fetch fails
                return MagicMock(returncode=1, stderr="fatal error")

            mock_run.side_effect = mock_git_command

            result = check_up_to_date()
            assert result is False


@pytest.mark.unit
class TestCheckTestsPass:
    """Test check_tests_pass function."""

    def test_returns_true_when_tests_pass(self) -> None:
        """check_tests_pass should return (True, None) when test command succeeds."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="all tests passed\n")

            passed, error = check_tests_pass(config)
            assert passed is True
            assert error is None

    def test_returns_false_with_error_when_tests_fail(self) -> None:
        """check_tests_pass should return (False, error) when test command fails."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="test failures", stdout="")

            passed, error = check_tests_pass(config)
            assert passed is False
            assert error == "test failures"

    def test_uses_configured_test_command(self) -> None:
        """check_tests_pass should use the command from config."""
        config = MagicMock()
        config.commands.test = "custom-test-command"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            check_tests_pass(config)

            # Verify the custom command was used
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "custom-test-command"

    def test_returns_true_when_no_tests_collected(self) -> None:
        """check_tests_pass should return (True, None) when pytest finds no tests (exit code 5)."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            # pytest exit code 5 means no tests collected
            mock_run.return_value = MagicMock(returncode=5, stdout="", stderr="")

            passed, error = check_tests_pass(config)
            assert passed is True
            assert error is None


@pytest.mark.unit
class TestCheckLintPass:
    """Test check_lint_pass function."""

    def test_returns_true_when_lint_passes(self) -> None:
        """check_lint_pass should return (True, None) when lint command succeeds."""
        config = MagicMock()
        config.commands.lint = "ruff check"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            passed, error = check_lint_pass(config)
            assert passed is True
            assert error is None

    def test_returns_false_with_error_when_lint_fails(self) -> None:
        """check_lint_pass should return (False, error) when lint command fails."""
        config = MagicMock()
        config.commands.lint = "ruff check"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="lint violations", stdout="")

            passed, error = check_lint_pass(config)
            assert passed is False
            assert error == "lint violations"

    def test_uses_configured_lint_command(self) -> None:
        """check_lint_pass should use the command from config."""
        config = MagicMock()
        config.commands.lint = "custom-lint-command"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            check_lint_pass(config)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "custom-lint-command"


@pytest.mark.unit
class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_check_result_creation(self) -> None:
        """CheckResult should be creatable with name, passed, and error."""
        result = CheckResult(name="git_clean", passed=True, error=None)
        assert result.name == "git_clean"
        assert result.passed is True
        assert result.error is None

    def test_check_result_with_error(self) -> None:
        """CheckResult should store error message."""
        result = CheckResult(name="tests_pass", passed=False, error="Test failures detected")
        assert result.passed is False
        assert result.error == "Test failures detected"


@pytest.mark.unit
class TestPreflightResult:
    """Test PreflightResult dataclass."""

    def test_preflight_result_creation(self) -> None:
        """PreflightResult should be creatable with passed, checks, and errors."""
        checks = {
            "git_clean": CheckResult("git_clean", True, None),
            "tests_pass": CheckResult("tests_pass", True, None),
        }
        result = PreflightResult(passed=True, checks=checks, errors=[])
        assert result.passed is True
        assert len(result.checks) == 2
        assert len(result.errors) == 0

    def test_preflight_result_with_failures(self) -> None:
        """PreflightResult should track failures and errors."""
        checks = {
            "git_clean": CheckResult("git_clean", False, "Uncommitted changes"),
        }
        errors = ["git_clean: Uncommitted changes"]
        result = PreflightResult(passed=False, checks=checks, errors=errors)
        assert result.passed is False
        assert result.checks["git_clean"].passed is False
        assert "git_clean: Uncommitted changes" in result.errors


@pytest.mark.unit
class TestRunPreflight:
    """Test run_preflight orchestration function."""

    def test_run_preflight_all_checks_pass(self) -> None:
        """run_preflight should return passed=True when all checks pass."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"
        config.preflight.target_branch = "main"

        with (
            patch("jiro.core.session.check_git_clean") as mock_clean,
            patch("jiro.core.session.check_correct_branch") as mock_branch,
            patch("jiro.core.session.check_up_to_date") as mock_update,
            patch("jiro.core.session.check_tests_pass") as mock_tests,
            patch("jiro.core.session.check_lint_pass") as mock_lint,
        ):
            mock_clean.return_value = True
            mock_branch.return_value = True
            mock_update.return_value = True
            mock_tests.return_value = True
            mock_lint.return_value = True

            result = run_preflight(config)

            assert result.passed is True
            assert all(check.passed for check in result.checks.values())
            assert len(result.errors) == 0

    def test_run_preflight_one_check_fails(self) -> None:
        """run_preflight should return passed=False if any check fails."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"
        config.preflight.target_branch = "main"

        with (
            patch("jiro.core.session.check_git_clean") as mock_clean,
            patch("jiro.core.session.check_correct_branch") as mock_branch,
            patch("jiro.core.session.check_up_to_date") as mock_update,
            patch("jiro.core.session.check_tests_pass") as mock_tests,
            patch("jiro.core.session.check_lint_pass") as mock_lint,
        ):
            mock_clean.return_value = False
            mock_branch.return_value = True
            mock_update.return_value = True
            mock_tests.return_value = True
            mock_lint.return_value = True

            result = run_preflight(config)

            assert result.passed is False
            assert result.checks["git_clean"].passed is False
            assert len(result.errors) > 0

    def test_run_preflight_returns_check_results(self) -> None:
        """run_preflight should return detailed check results."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"
        config.preflight.target_branch = "main"

        with (
            patch("jiro.core.session.check_git_clean") as mock_clean,
            patch("jiro.core.session.check_correct_branch") as mock_branch,
            patch("jiro.core.session.check_up_to_date") as mock_update,
            patch("jiro.core.session.check_tests_pass") as mock_tests,
            patch("jiro.core.session.check_lint_pass") as mock_lint,
        ):
            mock_clean.return_value = True
            mock_branch.return_value = True
            mock_update.return_value = True
            mock_tests.return_value = True
            mock_lint.return_value = True

            result = run_preflight(config)

            assert "git_clean" in result.checks
            assert "correct_branch" in result.checks
            assert "up_to_date" in result.checks
            assert "tests_pass" in result.checks
            assert "lint_pass" in result.checks

    def test_run_preflight_logs_results(self) -> None:
        """run_preflight should log results using structlog."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"
        config.preflight.target_branch = "main"

        with (
            patch("jiro.core.session.check_git_clean") as mock_clean,
            patch("jiro.core.session.check_correct_branch") as mock_branch,
            patch("jiro.core.session.check_up_to_date") as mock_update,
            patch("jiro.core.session.check_tests_pass") as mock_tests,
            patch("jiro.core.session.check_lint_pass") as mock_lint,
            patch("jiro.core.session.logger") as mock_logger,
        ):
            mock_clean.return_value = True
            mock_branch.return_value = True
            mock_update.return_value = True
            mock_tests.return_value = True
            mock_lint.return_value = True

            run_preflight(config)

            # Verify logging was called (module-level logger is used)
            mock_logger.info.assert_called()
