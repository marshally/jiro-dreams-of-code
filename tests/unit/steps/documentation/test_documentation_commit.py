"""Tests for DocumentationCommit class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.documentation.documentation_commit import DocumentationCommit
from jiro.steps.documentation.documentation_result import DocumentationResult
from jiro.steps.types import VerificationError
from jiro.verifications.base import VerificationResult


class TestDocumentationCommitIsCommit:
    """Test that DocumentationCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """DocumentationCommit should inherit from Commit."""
        assert issubclass(DocumentationCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate DocumentationCommit."""
        commit = DocumentationCommit()
        assert isinstance(commit, DocumentationCommit)


class TestDocumentationCommitCreate:
    """Test the create method."""

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_markdown_only_commit(self, mock_run):
        """Should create commit for markdown-only changes."""
        # Mock git add and git commit
        mock_run.return_value = MagicMock(
            stdout="[main abc1234] 📝 Improve documentation (1 markdown file)\n"
        )

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc1234"
        assert "markdown file" in commit_result.message

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_python_doc_changes_commit(self, mock_run):
        """Should create commit for Python docstring changes."""
        mock_run.return_value = MagicMock(
            stdout="[main def5678] 📝 Improve code documentation (2 files)\n"
        )

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("module1.py"), Path("module2.py")],
            doc_files_changed=0,
            py_files_changed=2,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        assert commit_result.sha == "def5678"
        assert "code documentation" in commit_result.message
        assert "2 files" in commit_result.message

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_mixed_changes_commit(self, mock_run):
        """Should create commit for mixed markdown and Python changes."""
        mock_run.return_value = MagicMock(
            stdout="[main ghi9012] 📝 Improve documentation (1 markdown, 1 code files)\n"
        )

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("README.md"), Path("module.py")],
            doc_files_changed=1,
            py_files_changed=1,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        assert commit_result.sha == "ghi9012"
        assert "markdown" in commit_result.message
        assert "code files" in commit_result.message

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_stages_files(self, mock_run):
        """Should stage all changed files."""
        mock_run.return_value = MagicMock(stdout="[main xyz] message\n")

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("file1.md"), Path("file2.md")],
            doc_files_changed=2,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        # Should have called git add for each file
        calls = [call[0][0] for call in mock_run.call_args_list]
        git_add_calls = [call for call in calls if "add" in call]
        assert len(git_add_calls) == 2
        _ = commit_result  # Mark as used

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_uses_emoji(self, mock_run):
        """Should use 📝 emoji in commit message."""
        mock_run.return_value = MagicMock(stdout="[main abc] message\n")

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        commit_result = commit.create(result=result, verification=verification, e2e_time=2.0)

        assert "📝" in commit_result.message

    @patch("jiro.steps.documentation.documentation_commit.subprocess.run")
    def test_create_git_commit_failure(self, mock_run):
        """Should raise VerificationError if git commit fails."""
        from subprocess import CalledProcessError

        commit = DocumentationCommit()
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="test",
            verification_output="Verified",
            verification_time=0.5,
        )

        # First call is git add, which succeeds
        # Second call is git commit, which fails
        error = CalledProcessError(1, ["git", "commit"], stderr="error message")
        mock_run.side_effect = [
            MagicMock(),  # git add succeeds
            error,  # git commit fails
        ]

        with pytest.raises(VerificationError, match="Git commit failed"):
            commit.create(result=result, verification=verification, e2e_time=2.0)


class TestDocumentationCommitExtractSha:
    """Test the _extract_sha helper method."""

    def test_extract_sha_normal_format(self):
        """Should extract SHA from normal git commit output."""
        output = "[main abc1234def5678] 📝 Improve documentation\n"
        sha = DocumentationCommit._extract_sha(output)
        assert sha == "abc1234def5678"

    def test_extract_sha_short_format(self):
        """Should extract SHA from short format."""
        output = "[main abc1234] Message\n"
        sha = DocumentationCommit._extract_sha(output)
        assert sha == "abc1234"

    def test_extract_sha_with_branch_name(self):
        """Should extract SHA even with branch name."""
        output = "[feature-branch abc123def456] Message\n"
        sha = DocumentationCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_invalid_raises(self):
        """Should raise ValueError if SHA cannot be extracted."""
        output = "Invalid output format"
        with pytest.raises(ValueError, match="Could not extract SHA"):
            DocumentationCommit._extract_sha(output)
