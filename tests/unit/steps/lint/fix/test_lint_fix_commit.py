"""Tests for LintFixCommit class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from jiro.commits.base import Commit, CommitResult
from jiro.steps.lint.fix.lint_fix_commit import LintFixCommit
from jiro.steps.lint.fix.lint_fix_result import LintFixResult
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import VerificationResult


class TestLintFixCommitClass:
    """Test that LintFixCommit is properly defined."""

    def test_inherits_from_commit(self):
        """LintFixCommit should inherit from Commit."""
        assert issubclass(LintFixCommit, Commit)


class TestLintFixCommitMessage:
    """Test commit message creation."""

    def test_commit_message_format(self):
        """Should create commit message with correct format."""
        commit = LintFixCommit()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # We'll need to patch the subprocess calls
        with patch("jiro.steps.lint.fix.lint_fix_commit.subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = "[branch abc1234] message\n"
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            verification = VerificationResult(
                success=True,
                verification_command="flake8",
                verification_output="passed",
                verification_time=1.0,
            )

            _ = commit.create(
                result=result,
                verification=verification,
                e2e_time=5.0,
            )

            # The commit should be created with the message
            calls = list(mock_run.call_args_list)
            # First call is git add, second is git commit
            git_commit_call = calls[1]
            commit_args = git_commit_call[0][0]
            message = commit_args[-1]

            assert "🧹" in message
            assert "lint fix" in message
            assert "E501" in message
            assert "src/example.py" in message


class TestLintFixCommitStaging:
    """Test file staging."""

    @patch("jiro.steps.lint.fix.lint_fix_commit.subprocess.run")
    def test_stage_single_file(self, mock_run):
        """Should stage the single changed file."""
        commit = LintFixCommit()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        commit._stage_files(result)

        # Should have called git add for the file
        mock_run.assert_called()
        calls = mock_run.call_args_list
        # Check that git add was called with the file
        git_add_call = calls[0]
        assert "git" in git_add_call[0][0]
        assert "add" in git_add_call[0][0]
        assert "src/example.py" in git_add_call[0][0]

    @patch("jiro.steps.lint.fix.lint_fix_commit.subprocess.run")
    def test_staging_failure(self, mock_run):
        """Should raise VerificationError if git add fails."""
        commit = LintFixCommit()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock git add failure with CalledProcessError
        from subprocess import CalledProcessError

        error = CalledProcessError(1, "git add", stderr="fatal: not a git repository")
        mock_run.side_effect = error

        try:
            commit._stage_files(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "Could not stage files" in e.rule_violated


class TestLintFixCommitExtractSHA:
    """Test SHA extraction from git output."""

    def test_extract_sha_standard_format(self):
        """Should extract SHA from standard git output."""
        commit = LintFixCommit()
        output = "[main abc1234def5678] lint fix E501 in src/example.py\n 1 file changed, 1 insertion(+)\n"
        sha = commit._extract_sha(output)
        assert sha == "abc1234def5678"

    def test_extract_sha_short_format(self):
        """Should extract short SHA."""
        commit = LintFixCommit()
        output = "[main abc1234] message\n"
        sha = commit._extract_sha(output)
        assert sha == "abc1234"

    def test_extract_sha_invalid_format(self):
        """Should raise ValueError for invalid format."""
        commit = LintFixCommit()
        output = "No bracket format here\n"
        try:
            commit._extract_sha(output)
            raise AssertionError("Should raise ValueError")
        except ValueError as e:
            assert "Could not extract SHA" in str(e)


class TestLintFixCommitIntegration:
    """Test full commit creation flow."""

    @patch("jiro.steps.lint.fix.lint_fix_commit.subprocess.run")
    def test_create_commit_success(self, mock_run):
        """Should create commit successfully."""
        commit = LintFixCommit()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        verification = VerificationResult(
            success=True,
            verification_command="flake8",
            verification_output="passed",
            verification_time=1.0,
        )

        # Mock subprocess calls
        mock_process = MagicMock()
        mock_process.stdout = "[main abc1234] lint fix E501 in src/example.py\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=5.0,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc1234"
        assert "🧹" in commit_result.message
        assert "E501" in commit_result.message
