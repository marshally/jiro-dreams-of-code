"""Tests for PerformanceCommit."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.performance.performance_commit import PerformanceCommit
from jiro.steps.performance.performance_result import PerformanceResult
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import VerificationResult


class TestPerformanceCommitIsCommit:
    """Test that PerformanceCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """PerformanceCommit should inherit from Commit."""
        assert issubclass(PerformanceCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate PerformanceCommit."""
        commit = PerformanceCommit()
        assert isinstance(commit, PerformanceCommit)


class TestPerformanceCommitStaging:
    """Test file staging."""

    @patch("jiro.steps.performance.performance_commit.subprocess.run")
    def test_stage_files_success(self, mock_run):
        """Should stage files successfully."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        commit = PerformanceCommit()
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
        commit._stage_files(result)

    @patch("jiro.steps.performance.performance_commit.subprocess.run")
    def test_stage_files_failure(self, mock_run):
        """Should raise VerificationError if staging fails."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git add", stderr="fatal: pathspec error")

        commit = PerformanceCommit()
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
            commit._stage_files(result)

        assert exc_info.value.step_type == StepType.PERFORMANCE
        assert "Could not stage files" in exc_info.value.rule_violated


class TestPerformanceCommitExtractSha:
    """Test SHA extraction from git output."""

    def test_extract_sha_standard_format(self):
        """Should extract SHA from standard git output."""
        output = "[main abc123def456] 🚀 Performance optimization\n"
        sha = PerformanceCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_with_spaces(self):
        """Should extract SHA even with extra spaces."""
        output = "[main   abc123def456   ] 🚀 Performance optimization\n"
        sha = PerformanceCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_branch_with_slashes(self):
        """Should handle branch names with slashes."""
        output = "[feature/optimize abc123def456] 🚀 Performance optimization\n"
        sha = PerformanceCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_invalid_format_raises_error(self):
        """Should raise ValueError if SHA cannot be extracted."""
        output = "Some other output without SHA\n"
        with pytest.raises(ValueError) as exc_info:
            PerformanceCommit._extract_sha(output)
        assert "Could not extract SHA" in str(exc_info.value)


class TestPerformanceCommitMessage:
    """Test commit message."""

    @patch("jiro.steps.performance.performance_commit.subprocess.run")
    def test_commit_message_has_rocket_emoji(self, mock_run):
        """Commit message should include 🚀 emoji."""
        # Mock git add and git commit
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        mock_proc.stdout = "[main abc123] message\n"
        mock_run.return_value = mock_proc

        commit = PerformanceCommit()
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
        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        # Check that the message was called with the rocket emoji
        assert "🚀" in commit_result.message
        assert (
            "Performance" in commit_result.message
            or "optimization" in commit_result.message.lower()
        )


class TestPerformanceCommitCreateFull:
    """Test full create method."""

    @patch("jiro.steps.performance.performance_commit.subprocess.run")
    def test_create_success(self, mock_run):
        """Should create commit successfully."""
        # Mock git add
        mock_add = MagicMock()
        mock_add.returncode = 0
        mock_add.stderr = ""

        # Mock git commit
        mock_commit = MagicMock()
        mock_commit.returncode = 0
        mock_commit.stderr = ""
        mock_commit.stdout = "[main abc123def456] 🚀 Performance optimization\n"

        mock_run.side_effect = [mock_add, mock_commit]

        commit = PerformanceCommit()
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
        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc123def456"
        assert "🚀" in commit_result.message

    @patch("jiro.steps.performance.performance_commit.subprocess.run")
    def test_create_failure_on_commit(self, mock_run):
        """Should raise VerificationError if commit fails."""
        from subprocess import CalledProcessError

        mock_add = MagicMock()
        mock_add.returncode = 0

        # Simulate git commit failure
        mock_run.side_effect = [
            mock_add,
            CalledProcessError(1, "git commit", stderr="nothing to commit"),
        ]

        commit = PerformanceCommit()
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
        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=0.5,
        )

        with pytest.raises(VerificationError) as exc_info:
            commit.create(result=result, verification=verification, e2e_time=2.0)

        assert exc_info.value.step_type == StepType.PERFORMANCE
        assert "Git commit failed" in exc_info.value.rule_violated
