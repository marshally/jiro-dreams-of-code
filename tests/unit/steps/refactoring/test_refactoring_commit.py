"""Tests for RefactoringCommit class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.refactoring.refactoring_commit import RefactoringCommit
from jiro.steps.refactoring.refactoring_result import RefactoringResult
from jiro.steps.types import VerificationError
from jiro.verifications.base import VerificationResult


class TestRefactoringCommitIsCommit:
    """Test that RefactoringCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """RefactoringCommit should inherit from Commit."""
        assert issubclass(RefactoringCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate RefactoringCommit."""
        commit = RefactoringCommit()
        assert isinstance(commit, RefactoringCommit)


class TestRefactoringCommitStageFiles:
    """Test the _stage_files method."""

    @patch("subprocess.run")
    def test_stages_all_changed_files(self, mock_run):
        """Should stage all files in changed_files."""
        commit = RefactoringCommit()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py"), Path("src/models/user.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        mock_run.return_value = MagicMock(returncode=0)

        commit._stage_files(result)

        # Should call git add for each file
        assert mock_run.call_count == 2
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any("src/auth.py" in str(c) for c in calls)
        assert any("src/models/user.py" in str(c) for c in calls)

    @patch("subprocess.run")
    def test_handles_staging_failure(self, mock_run):
        """Should raise VerificationError on git add failure."""
        commit = RefactoringCommit()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git add", stderr="fatal error")

        with pytest.raises(VerificationError, match="Could not stage files"):
            commit._stage_files(result)


class TestRefactoringCommitExtractSha:
    """Test the _extract_sha helper method."""

    def test_extracts_sha_from_standard_output(self):
        """Should extract SHA from git commit output."""
        output = "[main abc1234] Fix login validation\n 1 file changed, 5 insertions(+)\n"
        sha = RefactoringCommit._extract_sha(output)
        assert sha == "abc1234"

    def test_extracts_sha_with_branch_name(self):
        """Should extract SHA even with branch name."""
        output = "[feature/auth abc123def456] Refactor auth\n"
        sha = RefactoringCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_raises_on_invalid_output(self):
        """Should raise ValueError if SHA cannot be extracted."""
        output = "Some unexpected output without SHA"
        with pytest.raises(ValueError, match="Could not extract SHA"):
            RefactoringCommit._extract_sha(output)


class TestRefactoringCommitCreate:
    """Test the create method."""

    @patch("subprocess.run")
    def test_creates_commit_with_refactor_emoji(self, mock_run):
        """Should create commit with ♻️ emoji."""
        commit = RefactoringCommit()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="extract_method",
            checksum="abc123",
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=1.0,
        )

        # Mock git commands
        def git_mock(cmd, *args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "commit" in cmd:
                result.stdout = "[main abc1234] ♻️ Refactor: extract_method\n"
            return result

        mock_run.side_effect = git_mock

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert isinstance(commit_result, CommitResult)
        assert "♻️" in commit_result.message
        assert "extract_method" in commit_result.message

    @patch("subprocess.run")
    def test_returns_commit_sha(self, mock_run):
        """Should return CommitResult with SHA."""
        commit = RefactoringCommit()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=1.0,
        )

        # Mock git commands
        call_count = [0]

        def git_mock(cmd, *args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            result.returncode = 0
            if "commit" in cmd:
                result.stdout = "[main xyz9999] ♻️ Refactor: rename\n"
            return result

        mock_run.side_effect = git_mock

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert commit_result.sha == "xyz9999"

    @patch("subprocess.run")
    def test_handles_commit_failure(self, mock_run):
        """Should raise VerificationError on git commit failure."""
        commit = RefactoringCommit()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="PASSED",
            verification_time=1.0,
        )

        # Mock git add success, git commit failure
        call_count = [0]

        def git_mock(cmd, *args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if "commit" in cmd:
                result.returncode = 1
                result.stderr = "nothing to commit"
                from subprocess import CalledProcessError

                raise CalledProcessError(1, "git commit", stderr="nothing to commit")
            result.returncode = 0
            return result

        mock_run.side_effect = git_mock

        with pytest.raises(VerificationError, match="Git commit failed"):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )
