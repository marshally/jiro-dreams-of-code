"""Tests for TestOnlyCommit class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.test.only.test_only_commit import TestOnlyCommit
from jiro.steps.types import VerificationError


class TestTestOnlyCommitIsCommit:
    """Test that TestOnlyCommit is a proper Commit."""

    def test_is_commit_subclass(self):
        """TestOnlyCommit should inherit from Commit."""
        assert issubclass(TestOnlyCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate TestOnlyCommit."""
        commit = TestOnlyCommit()
        assert isinstance(commit, TestOnlyCommit)

    def test_has_create_method(self):
        """TestOnlyCommit should have create method."""
        commit = TestOnlyCommit()
        assert hasattr(commit, "create")
        assert callable(commit.create)


class TestTestOnlyCommitExtractSha:
    """Test the _extract_sha helper method."""

    def test_extract_sha_standard_format(self):
        """Should extract SHA from standard git output."""
        commit = TestOnlyCommit()
        output = "[main abc1234] 🧪 Add test for something\n"

        sha = commit._extract_sha(output)
        assert sha == "abc1234"

    def test_extract_sha_with_branch_name(self):
        """Should extract SHA from output with branch name."""
        commit = TestOnlyCommit()
        output = "[feature/test-123 def5678] message\n"

        sha = commit._extract_sha(output)
        assert sha == "def5678"

    def test_extract_sha_with_multiple_hashes(self):
        """Should extract the commit SHA (last word in brackets)."""
        commit = TestOnlyCommit()
        output = "[main 9abc def5678] message\n"

        sha = commit._extract_sha(output)
        # Should get the last word which is the hash
        assert sha in ["def5678", "9abc"]

    def test_extract_sha_invalid_format_raises(self):
        """Should raise ValueError for invalid format."""
        commit = TestOnlyCommit()
        output = "invalid output format"

        with pytest.raises(ValueError):
            commit._extract_sha(output)


class TestTestOnlyCommitStageFiles:
    """Test the _stage_files helper method."""

    @patch("subprocess.run")
    def test_stage_files_success(self, mock_run):
        """Should stage files successfully."""
        mock_run.return_value = MagicMock(returncode=0)

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [Path("tests/test_auth.py")]

        # Should not raise
        commit._stage_files(result)

        # Verify git add was called
        assert mock_run.called

    @patch("subprocess.run")
    def test_stage_multiple_files(self, mock_run):
        """Should stage multiple files."""
        mock_run.return_value = MagicMock(returncode=0)

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [
            Path("tests/test_auth.py"),
            Path("tests/test_utils_test.py"),
        ]

        commit._stage_files(result)

        # git add should be called twice
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_stage_files_failure(self, mock_run):
        """Should raise VerificationError if git add fails."""
        from subprocess import CalledProcessError

        error = CalledProcessError(1, "git add", stderr="fatal error")
        mock_run.side_effect = error

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [Path("tests/test_auth.py")]

        with pytest.raises(VerificationError) as exc_info:
            commit._stage_files(result)

        assert "Could not stage files" in exc_info.value.rule_violated


class TestTestOnlyCommitCreate:
    """Test the create method."""

    @patch("subprocess.run")
    def test_create_commit_success(self, mock_run):
        """Should create commit successfully."""
        # Mock git add (successful)
        git_add_result = MagicMock(returncode=0)

        # Mock git commit (successful)
        git_commit_result = MagicMock(
            returncode=0,
            stdout="[main abc1234] 🧪 Add test for validation\n",
        )

        def run_side_effect(*args, **kwargs):
            if "add" in args[0]:
                return git_add_result
            elif "commit" in args[0]:
                return git_commit_result
            return MagicMock()

        mock_run.side_effect = run_side_effect

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [Path("tests/test_new.py")]
        result.test_specifier = "tests/test_new.py::test_validation"

        verification = MagicMock()
        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=1.5,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc1234"
        assert "🧪" in commit_result.message
        assert "test_validation" in commit_result.message

    @patch("subprocess.run")
    def test_create_commit_with_test_name_extraction(self, mock_run):
        """Should extract test name from specifier for message."""
        git_add_result = MagicMock(returncode=0)
        git_commit_result = MagicMock(
            returncode=0,
            stdout="[main def5678] message\n",
        )

        def run_side_effect(*args, **kwargs):
            if "add" in args[0]:
                return git_add_result
            elif "commit" in args[0]:
                return git_commit_result
            return MagicMock()

        mock_run.side_effect = run_side_effect

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [Path("tests/test_utils.py")]
        result.test_specifier = "tests/test_utils.py::test_string_formatting"

        verification = MagicMock()
        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=0.8,
        )

        assert "test_string_formatting" in commit_result.message

    @patch("subprocess.run")
    def test_create_commit_git_commit_fails(self, mock_run):
        """Should raise VerificationError if git commit fails."""
        from subprocess import CalledProcessError

        git_add_result = MagicMock(returncode=0)

        def run_side_effect(*args, **kwargs):
            if "add" in args[0]:
                return git_add_result
            elif "commit" in args[0]:
                raise CalledProcessError(1, "git commit", stderr="nothing to commit")
            return MagicMock()

        mock_run.side_effect = run_side_effect

        commit = TestOnlyCommit()
        result = MagicMock()
        result.changed_files = [Path("tests/test_new.py")]
        result.test_specifier = "tests/test_new.py::test_example"

        verification = MagicMock()

        with pytest.raises(VerificationError) as exc_info:
            commit.create(
                result=result,
                verification=verification,
                e2e_time=1.0,
            )

        assert "Git commit failed" in exc_info.value.rule_violated

    def test_create_returns_commit_result(self):
        """Should return CommitResult instance."""
        with patch("subprocess.run") as mock_run:
            git_add_result = MagicMock(returncode=0)
            git_commit_result = MagicMock(
                returncode=0,
                stdout="[main abc1234] message\n",
            )

            def run_side_effect(*args, **kwargs):
                if "add" in args[0]:
                    return git_add_result
                elif "commit" in args[0]:
                    return git_commit_result
                return MagicMock()

            mock_run.side_effect = run_side_effect

            commit = TestOnlyCommit()
            result = MagicMock()
            result.changed_files = [Path("tests/test_new.py")]
            result.test_specifier = "tests/test_new.py::test_example"

            verification = MagicMock()
            commit_result = commit.create(
                result=result,
                verification=verification,
                e2e_time=1.0,
            )

            assert isinstance(commit_result, CommitResult)
            assert hasattr(commit_result, "sha")
            assert hasattr(commit_result, "message")
