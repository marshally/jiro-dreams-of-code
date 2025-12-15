"""Tests for PerformanceVerify verification."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.performance.performance_result import PerformanceResult
from jiro.steps.performance.performance_verify import PerformanceVerify
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult


class TestPerformanceVerifyIsVerification:
    """Test that PerformanceVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """PerformanceVerify should inherit from Verification."""
        assert issubclass(PerformanceVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate PerformanceVerify."""
        verify = PerformanceVerify()
        assert isinstance(verify, PerformanceVerify)


class TestPerformanceVerifyGitDiffMatches:
    """Test git diff validation."""

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_git_diff_matches_success(self, mock_run):
        """Should pass when git diff matches changed_files."""
        # Mock git diff output
        mock_proc = MagicMock()
        mock_proc.stdout = "src/optimize.py\n"
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_git_diff_matches(result)

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_git_diff_mismatch_raises_error(self, mock_run):
        """Should raise VerificationError when git diff doesn't match."""
        # Mock git diff with different files
        mock_proc = MagicMock()
        mock_proc.stdout = "src/other.py\n"
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_git_diff_matches(result)

        assert exc_info.value.step_type == StepType.PERFORMANCE
        assert "git diff does not match" in exc_info.value.rule_violated

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_git_command_failure_raises_error(self, mock_run):
        """Should raise VerificationError if git command fails."""
        # Mock git diff failure
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git", stderr="fatal: not a git repo")

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_git_diff_matches(result)

        assert exc_info.value.step_type == StepType.PERFORMANCE
        assert "Could not run git diff" in exc_info.value.rule_violated


class TestPerformanceVerifyTestsPassing:
    """Test tests passing validation."""

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_tests_pass_success(self, mock_run):
        """Should pass when tests pass."""
        # Mock pytest success
        mock_proc = MagicMock()
        mock_proc.stdout = "passed in 0.5s"
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        output = verify._verify_tests_pass(result)
        assert "passed" in output

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_tests_fail_raises_error(self, mock_run):
        """Should raise VerificationError when tests fail."""
        # Mock pytest failure
        mock_proc = MagicMock()
        mock_proc.stdout = "FAILED test.py::test_speed"
        mock_proc.stderr = ""
        mock_proc.returncode = 1
        mock_run.return_value = mock_proc

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_tests_pass(result)

        assert exc_info.value.step_type == StepType.PERFORMANCE
        assert "Tests do not pass" in exc_info.value.rule_violated


class TestPerformanceVerifyFull:
    """Test full verify method."""

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_success(self, mock_run):
        """Should return VerificationResult on success."""
        # Mock git diff and pytest calls separately
        mock_git_diff = MagicMock()
        mock_git_diff.stdout = "src/optimize.py\n"
        mock_git_diff.stderr = ""
        mock_git_diff.returncode = 0

        mock_pytest = MagicMock()
        mock_pytest.stdout = "passed in 0.5s"
        mock_pytest.stderr = ""
        mock_pytest.returncode = 0

        # First call is git diff, second is pytest
        mock_run.side_effect = [mock_git_diff, mock_pytest]

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification_result = verify.verify(result=result)
        assert isinstance(verification_result, VerificationResult)
        assert verification_result.success is True
        assert "pytest" in verification_result.verification_command

    @patch("jiro.steps.performance.performance_verify.subprocess.run")
    def test_verify_failure_on_git_diff(self, mock_run):
        """Should raise VerificationError on git diff failure."""
        # Mock git diff failure
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git", stderr="fatal: not a git repo")

        verify = PerformanceVerify()
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError):
            verify.verify(result=result)
