"""Tests for BugGreenCommit class."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.bug.green.bug_green_commit import BugGreenCommit
from jiro.steps.bug.green.bug_green_result import BugGreenResult
from jiro.steps.types import VerificationError
from jiro.verifications.base import VerificationResult


class TestBugGreenCommitIsCommit:
    """Test that BugGreenCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """BugGreenCommit should inherit from Commit."""
        assert issubclass(BugGreenCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate BugGreenCommit."""
        commit = BugGreenCommit()
        assert isinstance(commit, BugGreenCommit)


class TestBugGreenCommitCreate:
    """Test the create method."""

    @patch("subprocess.run")
    def test_create_returns_commit_result(self, mock_run):
        """create() should return CommitResult."""
        # Mock git add and git commit
        mock_run.side_effect = [
            # First call: git add
            MagicMock(stdout="", stderr="", returncode=0),
            # Second call: git commit
            MagicMock(
                stdout="[main abc123def] 🦋 Fix bug verified by tests/test_auth.py::test_example\n",
                stderr="",
                returncode=0,
            ),
        ]

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc123def"
        assert "🦋" in commit_result.message

    @patch("subprocess.run")
    def test_create_stages_files(self, mock_run):
        """create() should stage files with git add."""
        # First call: git add, second call: git commit
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),
            MagicMock(stdout="[main abc123] message\n", stderr="", returncode=0),
        ]

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        # Should have called git add
        calls = [call[0][0] for call in mock_run.call_args_list]
        assert ["git", "add", "src/auth.py"] in calls

    @patch("subprocess.run")
    def test_commit_message_includes_test_specifier(self, mock_run):
        """Commit message should include test specifier."""
        mock_run.return_value = MagicMock(
            stdout="[main abc123] message\n",
            stderr="",
            returncode=0,
        )

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_password_validation",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert "tests/test_auth.py::test_password_validation" in commit_result.message

    @patch("subprocess.run")
    def test_commit_message_includes_emoji(self, mock_run):
        """Commit message should include 🦋 emoji."""
        mock_run.return_value = MagicMock(
            stdout="[main abc123] message\n",
            stderr="",
            returncode=0,
        )

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert "🦋" in commit_result.message

    @patch("subprocess.run")
    def test_git_add_failure_raises_verification_error(self, mock_run):
        """Should raise VerificationError if git add fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="git add",
            stderr="error: pathspec 'src/auth.py' did not match any files",
        )

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        with pytest.raises(VerificationError, match="Could not stage files"):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )

    @patch("subprocess.run")
    def test_git_commit_failure_raises_verification_error(self, mock_run):
        """Should raise VerificationError if git commit fails."""
        # First call succeeds (git add), second fails (git commit)
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),
            subprocess.CalledProcessError(
                returncode=1,
                cmd="git commit",
                stderr="error: nothing to commit",
            ),
        ]

        commit = BugGreenCommit()
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
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
            verification_time=1.0,
        )

        with pytest.raises(VerificationError, match="Git commit failed"):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )


class TestBugGreenCommitExtractSha:
    """Test the _extract_sha helper method."""

    def test_extract_sha_from_standard_format(self):
        """Should extract SHA from standard git commit output."""
        commit = BugGreenCommit()
        output = "[main abc123def456] 🦋 Fix bug verified\n"

        sha = commit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_with_branch_name(self):
        """Should extract SHA even with complex branch name."""
        commit = BugGreenCommit()
        output = "[feature/bugfix abc123abc123] message\n"

        sha = commit._extract_sha(output)
        assert sha == "abc123abc123"

    def test_extract_sha_with_multiple_words(self):
        """Should handle output with multiple words."""
        commit = BugGreenCommit()
        output = "[main f1234567] Fix bug verified\n"

        sha = commit._extract_sha(output)
        assert sha == "f1234567"

    def test_extract_sha_invalid_format_raises_value_error(self):
        """Should raise ValueError if SHA cannot be extracted."""
        commit = BugGreenCommit()
        output = "Some other output without SHA\n"

        with pytest.raises(ValueError, match="Could not extract SHA"):
            commit._extract_sha(output)
