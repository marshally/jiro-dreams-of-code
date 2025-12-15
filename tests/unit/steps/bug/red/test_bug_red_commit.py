"""Tests for BugRedCommit class."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.bug.red.bug_red_commit import BugRedCommit
from jiro.steps.bug.red.bug_red_result import BugRedResult
from jiro.steps.types import VerificationError
from jiro.verifications.base import VerificationResult


class TestBugRedCommitIsCommit:
    """Test that BugRedCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """BugRedCommit should inherit from Commit."""
        assert issubclass(BugRedCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate BugRedCommit."""
        commit = BugRedCommit()
        assert isinstance(commit, BugRedCommit)


class TestBugRedCommitCreate:
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
                stdout="[main abc123def] 🐛 Add failing test to reproduce test_example\n",
                stderr="",
                returncode=0,
            ),
        ]

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc123def"
        assert "🐛" in commit_result.message

    @patch("subprocess.run")
    def test_create_stages_files(self, mock_run):
        """create() should stage files with git add."""
        # First call: git add, second call: git commit
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),
            MagicMock(stdout="[main abc123] message\n", stderr="", returncode=0),
        ]

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        # Check that git add was called
        calls = mock_run.call_args_list
        assert len(calls) >= 1
        first_call_args = calls[0][0][0]
        assert "add" in first_call_args

    @patch("subprocess.run")
    def test_create_multiple_files(self, mock_run):
        """create() should handle multiple files."""
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git add file1
            MagicMock(stdout="", stderr="", returncode=0),  # git add file2
            MagicMock(stdout="[main xyz789] message\n", stderr="", returncode=0),  # git commit
        ]

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py"), Path("tests/test_login.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert commit_result.sha == "xyz789"

    @patch("subprocess.run")
    def test_create_git_add_failure(self, mock_run):
        """create() should raise VerificationError if git add fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git add")

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        with pytest.raises(VerificationError):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )

    @patch("subprocess.run")
    def test_create_git_commit_failure(self, mock_run):
        """create() should raise VerificationError if git commit fails."""
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git add succeeds
            subprocess.CalledProcessError(1, "git commit"),  # git commit fails
        ]

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        with pytest.raises(VerificationError):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )

    @patch("subprocess.run")
    def test_bug_emoji_in_message(self, mock_run):
        """create() should include bug emoji in commit message."""
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),
            MagicMock(stdout="[main abc123] message\n", stderr="", returncode=0),
        ]

        commit = BugRedCommit()
        result = BugRedResult(
            changed_files=[Path("tests/test_bug.py")],
            test_file=Path("tests/test_bug.py"),
            test_name="test_my_bug",
            test_specifier="tests/test_bug.py::test_my_bug",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="FAILED",
            verification_time=1.0,
        )

        commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        # Check that the commit message contains the bug emoji
        calls = mock_run.call_args_list
        commit_call_args = calls[1][0][0]  # Second call should be git commit
        # Look for the emoji in the actual -m argument
        assert any("🐛" in str(arg) for arg in commit_call_args)


class TestBugRedCommitExtractSha:
    """Test SHA extraction from git commit output."""

    def test_extract_sha_standard_format(self):
        """Should extract SHA from standard git output."""
        output = "[main abc123def] 🐛 Add failing test\n"
        sha = BugRedCommit._extract_sha(output)
        assert sha == "abc123def"

    def test_extract_sha_with_branch_name(self):
        """Should handle branch names with hyphens."""
        output = "[feature/bug-fix a1b2c3d] 🐛 Fix bug\n"
        sha = BugRedCommit._extract_sha(output)
        assert sha == "a1b2c3d"

    def test_extract_sha_short_hash(self):
        """Should work with shorter hashes."""
        output = "[main abc123] message\n"
        sha = BugRedCommit._extract_sha(output)
        assert sha == "abc123"

    def test_extract_sha_invalid_raises_error(self):
        """Should raise error if SHA cannot be extracted."""
        output = "No hash here\n"
        with pytest.raises(ValueError):
            BugRedCommit._extract_sha(output)
