"""Tests for deterministic commit review checks."""

import pytest

from jiro.core.review import (
    verify_commit_files,
    verify_commit_message,
    verify_task_reference,
)


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
