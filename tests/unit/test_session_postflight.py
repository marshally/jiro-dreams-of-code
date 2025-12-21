"""Tests for session postflight checks."""

from unittest.mock import MagicMock, patch

import pytest

from jiro.core.session import (
    CheckResult,
    PostflightResult,
    push_to_origin,
    run_full_lint,
    run_full_tests,
    run_postflight,
)


@pytest.mark.unit
class TestRunFullTests:
    """Test run_full_tests function."""

    def test_returns_true_when_tests_pass(self) -> None:
        """run_full_tests should return True when test command succeeds."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="all tests passed\n")

            result = run_full_tests(config)
            assert result is True

    def test_returns_false_when_tests_fail(self) -> None:
        """run_full_tests should return False when test command fails."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="test failures")

            result = run_full_tests(config)
            assert result is False

    def test_uses_configured_test_command(self) -> None:
        """run_full_tests should use the command from config."""
        config = MagicMock()
        config.commands.test = "custom-test-command"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            run_full_tests(config)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "custom-test-command"

    def test_returns_false_on_exception(self) -> None:
        """run_full_tests should return False if subprocess raises exception."""
        config = MagicMock()
        config.commands.test = "pytest"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("subprocess error")

            result = run_full_tests(config)
            assert result is False


@pytest.mark.unit
class TestRunFullLint:
    """Test run_full_lint function."""

    def test_returns_true_when_lint_passes(self) -> None:
        """run_full_lint should return True when lint command succeeds."""
        config = MagicMock()
        config.commands.lint = "ruff check"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            result = run_full_lint(config)
            assert result is True

    def test_returns_false_when_lint_fails(self) -> None:
        """run_full_lint should return False when lint command fails."""
        config = MagicMock()
        config.commands.lint = "ruff check"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="lint violations")

            result = run_full_lint(config)
            assert result is False

    def test_uses_configured_lint_command(self) -> None:
        """run_full_lint should use the command from config."""
        config = MagicMock()
        config.commands.lint = "custom-lint-command"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            run_full_lint(config)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "custom-lint-command"

    def test_returns_false_on_exception(self) -> None:
        """run_full_lint should return False if subprocess raises exception."""
        config = MagicMock()
        config.commands.lint = "ruff check"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("subprocess error")

            result = run_full_lint(config)
            assert result is False


@pytest.mark.unit
class TestPushToOrigin:
    """Test push_to_origin function."""

    def test_returns_true_when_push_succeeds(self) -> None:
        """push_to_origin should return True when git push succeeds."""
        with patch("subprocess.run") as mock_run:

            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                return MagicMock(returncode=0, stdout="")

            mock_run.side_effect = mock_git_command

            result = push_to_origin()
            assert result is True

    def test_returns_false_when_push_fails(self) -> None:
        """push_to_origin should return False when git push fails."""
        with patch("subprocess.run") as mock_run:

            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                return MagicMock(returncode=1, stderr="push failed")

            mock_run.side_effect = mock_git_command

            result = push_to_origin()
            assert result is False

    def test_returns_true_when_no_origin(self) -> None:
        """push_to_origin should return True when there is no origin remote."""
        with patch("subprocess.run") as mock_run:
            # Origin check fails - no remote
            mock_run.return_value = MagicMock(returncode=1, stderr="fatal: No such remote")

            result = push_to_origin()
            assert result is True

    def test_uses_git_push_origin_head(self) -> None:
        """push_to_origin should use 'git push origin HEAD' command."""
        with patch("subprocess.run") as mock_run:

            def mock_git_command(cmd, *args, **kwargs):
                if cmd[0:3] == ["git", "remote", "get-url"]:
                    return MagicMock(returncode=0, stdout="https://github.com/test/repo\n")
                return MagicMock(returncode=0, stdout="")

            mock_run.side_effect = mock_git_command

            push_to_origin()

            # Should be called twice: once for remote check, once for push
            assert mock_run.call_count == 2
            # Second call should be the push command
            args = mock_run.call_args_list[1][0][0]
            assert args == ["git", "push", "origin", "HEAD"]

    def test_returns_false_on_exception(self) -> None:
        """push_to_origin should return False if subprocess raises exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("subprocess error")

            result = push_to_origin()
            assert result is False


@pytest.mark.unit
class TestPostflightResult:
    """Test PostflightResult dataclass."""

    def test_postflight_result_creation(self) -> None:
        """PostflightResult should be creatable with passed, checks, and errors."""
        checks = {
            "full_tests": CheckResult("full_tests", True, None),
            "full_lint": CheckResult("full_lint", True, None),
            "push_to_origin": CheckResult("push_to_origin", True, None),
        }
        result = PostflightResult(passed=True, checks=checks, errors=[])
        assert result.passed is True
        assert len(result.checks) == 3
        assert len(result.errors) == 0

    def test_postflight_result_with_failures(self) -> None:
        """PostflightResult should track failures and errors."""
        checks = {
            "full_tests": CheckResult("full_tests", False, "Test failures detected"),
        }
        errors = ["full_tests: Test failures detected"]
        result = PostflightResult(passed=False, checks=checks, errors=errors)
        assert result.passed is False
        assert result.checks["full_tests"].passed is False
        assert "full_tests: Test failures detected" in result.errors


@pytest.mark.unit
class TestRunPostflight:
    """Test run_postflight orchestration function."""

    def test_run_postflight_all_checks_pass(self) -> None:
        """run_postflight should return passed=True when all checks pass."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"

        with (
            patch("jiro.core.session.run_full_tests") as mock_tests,
            patch("jiro.core.session.run_full_lint") as mock_lint,
            patch("jiro.core.session.push_to_origin") as mock_push,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_push.return_value = True

            result = run_postflight(config)

            assert result.passed is True
            assert all(check.passed for check in result.checks.values())
            assert len(result.errors) == 0

    def test_run_postflight_one_check_fails(self) -> None:
        """run_postflight should return passed=False if any check fails."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"

        with (
            patch("jiro.core.session.run_full_tests") as mock_tests,
            patch("jiro.core.session.run_full_lint") as mock_lint,
            patch("jiro.core.session.push_to_origin") as mock_push,
        ):
            mock_tests.return_value = False
            mock_lint.return_value = True
            mock_push.return_value = True

            result = run_postflight(config)

            assert result.passed is False
            assert result.checks["full_tests"].passed is False
            assert len(result.errors) > 0

    def test_run_postflight_returns_check_results(self) -> None:
        """run_postflight should return detailed check results."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"

        with (
            patch("jiro.core.session.run_full_tests") as mock_tests,
            patch("jiro.core.session.run_full_lint") as mock_lint,
            patch("jiro.core.session.push_to_origin") as mock_push,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_push.return_value = True

            result = run_postflight(config)

            assert "full_tests" in result.checks
            assert "full_lint" in result.checks
            assert "push_to_origin" in result.checks

    def test_run_postflight_logs_results(self) -> None:
        """run_postflight should log results using structlog."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"

        with (
            patch("jiro.core.session.run_full_tests") as mock_tests,
            patch("jiro.core.session.run_full_lint") as mock_lint,
            patch("jiro.core.session.push_to_origin") as mock_push,
            patch("jiro.core.session.logger") as mock_logger,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_push.return_value = True

            run_postflight(config)

            # Verify logging was called (module-level logger is used)
            mock_logger.info.assert_called()

    def test_run_postflight_with_multiple_failures(self) -> None:
        """run_postflight should handle multiple check failures."""
        config = MagicMock()
        config.commands.test = "pytest"
        config.commands.lint = "ruff check"

        with (
            patch("jiro.core.session.run_full_tests") as mock_tests,
            patch("jiro.core.session.run_full_lint") as mock_lint,
            patch("jiro.core.session.push_to_origin") as mock_push,
        ):
            mock_tests.return_value = False
            mock_lint.return_value = False
            mock_push.return_value = True

            result = run_postflight(config)

            assert result.passed is False
            assert result.checks["full_tests"].passed is False
            assert result.checks["full_lint"].passed is False
            assert result.checks["push_to_origin"].passed is True
            assert len(result.errors) == 2
