"""Tests for deterministic commit review checks."""

import subprocess
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from jiro.core.review import (
    verify_commit_files,
    verify_commit_message,
    verify_commit_message_format,
    verify_only_docs_files_changed,
    verify_task_reference,
    verify_task_reference_valid,
)
from jiro.trackers.interface import Task


class TestVerifyCommitFiles:
    """Tests for verify_commit_files function."""

    @pytest.mark.unit
    def test_docs_commit_with_md_files_only(self) -> None:
        """Docs commit with only .md files should pass."""
        files = ["README.md", "docs/api.md"]
        result = verify_commit_files(files, "docs")
        assert result.is_valid is True

    @pytest.mark.unit
    def test_docs_commit_with_txt_files(self) -> None:
        """Docs commit with .txt files should pass."""
        files = ["LICENSE.txt", "CHANGELOG.txt"]
        result = verify_commit_files(files, "docs")
        assert result.is_valid is True

    @pytest.mark.unit
    def test_docs_commit_with_py_files_fails(self) -> None:
        """Docs commit with .py files should fail."""
        files = ["README.md", "src/main.py"]
        result = verify_commit_files(files, "docs")
        assert result.is_valid is False
        assert "src/main.py" in result.error

    @pytest.mark.unit
    def test_docs_commit_with_test_files_fails(self) -> None:
        """Docs commit with test files should fail."""
        files = ["docs/guide.md", "tests/test_main.py"]
        result = verify_commit_files(files, "docs")
        assert result.is_valid is False

    @pytest.mark.unit
    def test_tdd_green_with_py_files_passes(self) -> None:
        """TDD green commit with .py files should pass."""
        files = ["src/module.py", "tests/test_module.py"]
        result = verify_commit_files(files, "tdd_green")
        assert result.is_valid is True

    @pytest.mark.unit
    def test_lint_fix_with_any_files_passes(self) -> None:
        """Lint fix commit allows any file types."""
        files = ["src/main.py", "src/utils.py"]
        result = verify_commit_files(files, "lint_fix")
        assert result.is_valid is True


class TestVerifyCommitMessage:
    """Tests for verify_commit_message function."""

    @pytest.mark.unit
    def test_message_with_emoji_prefix_passes(self) -> None:
        """Message with emoji prefix should pass."""
        message = "📝 docs: Add API documentation"
        result = verify_commit_message(message)
        assert result.is_valid is True

    @pytest.mark.unit
    def test_message_without_prefix_fails(self) -> None:
        """Message without type prefix should fail."""
        message = "Add some documentation"
        result = verify_commit_message(message)
        assert result.is_valid is False

    @pytest.mark.unit
    def test_message_with_task_reference_passes(self) -> None:
        """Message with task reference should pass."""
        message = "🧪 TDD: Create User model (TASK-123)"
        result = verify_commit_message(message)
        assert result.is_valid is True

    @pytest.mark.unit
    def test_empty_message_fails(self) -> None:
        """Empty message should fail."""
        message = ""
        result = verify_commit_message(message)
        assert result.is_valid is False


class TestVerifyTaskReference:
    """Tests for verify_task_reference function."""

    @pytest.mark.unit
    def test_message_with_matching_task_id_passes(self) -> None:
        """Message containing matching task ID should pass."""
        message = "📝 docs(TASK-123): Add documentation"
        result = verify_task_reference(message, "TASK-123")
        assert result.is_valid is True

    @pytest.mark.unit
    def test_message_with_wrong_task_id_fails(self) -> None:
        """Message with different task ID should fail."""
        message = "📝 docs(TASK-456): Add documentation"
        result = verify_task_reference(message, "TASK-123")
        assert result.is_valid is False
        assert "TASK-123" in result.error

    @pytest.mark.unit
    def test_message_without_task_id_fails(self) -> None:
        """Message without any task ID should fail."""
        message = "📝 docs: Add documentation"
        result = verify_task_reference(message, "TASK-123")
        assert result.is_valid is False


class TestVerifyOnlyDocsFilesChanged:
    """Tests for verify_only_docs_files_changed function."""

    @pytest.mark.unit
    def test_commit_with_only_md_files_passes(self) -> None:
        """Commit with only .md files should pass."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="README.md\ndocs/api.md\n",
            )
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is True
            assert result.check_name == "verify_only_docs_files_changed"

    @pytest.mark.unit
    def test_commit_with_multiple_doc_formats_passes(self) -> None:
        """Commit with .md, .txt, .rst, .adoc files should pass."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="README.md\nCHANGELOG.txt\ndocs/guide.rst\ncontrib.adoc\n",
            )
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is True

    @pytest.mark.unit
    def test_commit_with_python_files_fails(self) -> None:
        """Commit with .py files should fail."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="README.md\nsrc/main.py\n",
            )
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False
            assert "src/main.py" in result.message

    @pytest.mark.unit
    def test_commit_with_test_files_fails(self) -> None:
        """Commit with test files should fail."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="docs/guide.md\ntests/test_main.py\n",
            )
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False

    @pytest.mark.unit
    def test_commit_with_multiple_non_docs_files_fails(self) -> None:
        """Commit with multiple non-docs files should fail."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="README.md\nsrc/main.py\ntests/test.py\nconfig.yaml\n",
            )
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False
            assert "src/main.py" in result.message
            assert "tests/test.py" in result.message

    @pytest.mark.unit
    def test_git_command_failure_returns_failed_result(self) -> None:
        """Failed git command should return failed result."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False

    @pytest.mark.unit
    def test_git_command_timeout_returns_failed_result(self) -> None:
        """Git command timeout should return failed result."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 10)
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False
            assert "timed out" in result.message.lower()

    @pytest.mark.unit
    def test_git_command_exception_returns_failed_result(self) -> None:
        """Git command exception should return failed result."""
        commit_sha = "abc123def456"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")
            result = verify_only_docs_files_changed(commit_sha)
            assert result.passed is False

    @pytest.mark.unit
    def test_project_root_passed_to_git_command(self) -> None:
        """project_root should be passed to git command."""
        commit_sha = "abc123def456"
        project_root = "/path/to/project"
        with patch("jiro.core.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="README.md\n",
            )
            verify_only_docs_files_changed(commit_sha, project_root)
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == project_root


class TestVerifyCommitMessageFormat:
    """Tests for verify_commit_message_format function."""

    @pytest.mark.unit
    def test_message_with_emoji_and_task_and_type_passes(self) -> None:
        """Message with emoji, Task:, and Type: should pass."""
        message = "📝 docs: Update README\nTask: jiro-d8d\nType: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is True
        assert result.check_name == "verify_commit_message_format"

    @pytest.mark.unit
    def test_message_with_conventional_commit_and_task_and_type_passes(self) -> None:
        """Message with conventional commit, Task:, and Type: should pass."""
        message = "docs: Update API docs\nTask: jiro-d8d\nType: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is True

    @pytest.mark.unit
    def test_message_without_emoji_or_conventional_fails(self) -> None:
        """Message without emoji or conventional commit should fail."""
        message = "Update documentation\nTask: jiro-d8d\nType: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is False
        assert "emoji prefix" in result.message.lower() or "conventional" in result.message.lower()

    @pytest.mark.unit
    def test_message_without_task_reference_fails(self) -> None:
        """Message without Task: reference should fail."""
        message = "📝 docs: Update README\nType: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is False
        assert "task" in result.message.lower()

    @pytest.mark.unit
    def test_message_without_type_documentation_fails(self) -> None:
        """Message without Type: documentation should fail."""
        message = "📝 docs: Update README\nTask: jiro-d8d"
        result = verify_commit_message_format(message)
        assert result.passed is False
        assert "type: documentation" in result.message.lower()

    @pytest.mark.unit
    def test_empty_message_fails(self) -> None:
        """Empty message should fail."""
        message = ""
        result = verify_commit_message_format(message)
        assert result.passed is False

    @pytest.mark.unit
    def test_whitespace_only_message_fails(self) -> None:
        """Whitespace-only message should fail."""
        message = "   \n\t\n  "
        result = verify_commit_message_format(message)
        assert result.passed is False

    @pytest.mark.unit
    def test_message_task_reference_case_insensitive(self) -> None:
        """Task: reference should be case insensitive."""
        message = "📝 docs: Update README\ntask: jiro-d8d\nType: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is True

    @pytest.mark.unit
    def test_message_type_reference_case_insensitive(self) -> None:
        """Type: reference should be case insensitive."""
        message = "📝 docs: Update README\nTask: jiro-d8d\ntype: documentation"
        result = verify_commit_message_format(message)
        assert result.passed is True

    @pytest.mark.unit
    def test_message_with_all_valid_emoji_prefixes(self) -> None:
        """Message with any valid emoji prefix should pass."""
        valid_prefixes = ["📝", "🧪", "♻️", "🐛", "🔧", "🧹", "⚡"]
        for prefix in valid_prefixes:
            message = f"{prefix} some change\nTask: jiro-d8d\nType: documentation"
            result = verify_commit_message_format(message)
            assert result.passed is True, f"Failed for prefix {prefix}"


class TestVerifyTaskReferenceValid:
    """Tests for verify_task_reference_valid function."""

    @pytest.mark.unit
    def test_task_exists_and_in_progress_passes(self) -> None:
        """Task that exists and is in_progress should pass."""
        tracker = MagicMock()
        task = Task(
            id="jiro-d8d",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )
        tracker.get_task.return_value = task

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is True
        assert result.check_name == "verify_task_reference_valid"

    @pytest.mark.unit
    def test_task_exists_but_open_fails(self) -> None:
        """Task that exists but is open should fail."""
        tracker = MagicMock()
        task = Task(
            id="jiro-d8d",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )
        tracker.get_task.return_value = task

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False
        assert "open" in result.message

    @pytest.mark.unit
    def test_task_exists_but_blocked_fails(self) -> None:
        """Task that exists but is blocked should fail."""
        tracker = MagicMock()
        task = Task(
            id="jiro-d8d",
            title="Test task",
            task_type="task",
            status="blocked",
            created_at=datetime.now(),
        )
        tracker.get_task.return_value = task

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False

    @pytest.mark.unit
    def test_task_exists_but_closed_fails(self) -> None:
        """Task that exists but is closed should fail."""
        tracker = MagicMock()
        task = Task(
            id="jiro-d8d",
            title="Test task",
            task_type="task",
            status="closed",
            created_at=datetime.now(),
        )
        tracker.get_task.return_value = task

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False

    @pytest.mark.unit
    def test_task_not_found_raises_keyerror_returns_failed(self) -> None:
        """Task not found should return failed result."""
        tracker = MagicMock()
        tracker.get_task.side_effect = KeyError("Task not found")

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False
        assert "not found" in result.message.lower()

    @pytest.mark.unit
    def test_tracker_exception_returns_failed(self) -> None:
        """Tracker exception should return failed result."""
        tracker = MagicMock()
        tracker.get_task.side_effect = Exception("Connection error")

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False

    @pytest.mark.unit
    def test_result_includes_task_id_in_message(self) -> None:
        """Result message should include task ID."""
        tracker = MagicMock()
        task = Task(
            id="jiro-d8d",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )
        tracker.get_task.return_value = task

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert "jiro-d8d" in result.message

    @pytest.mark.unit
    def test_none_task_returns_failed(self) -> None:
        """None task should return failed result."""
        tracker = MagicMock()
        tracker.get_task.return_value = None

        result = verify_task_reference_valid("jiro-d8d", tracker)
        assert result.passed is False
