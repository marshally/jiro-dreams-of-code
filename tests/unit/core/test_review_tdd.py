"""Tests for TDD phase review validation.

Tests the TDD review validator to ensure commits meet phase-specific requirements.
"""

from unittest.mock import MagicMock, patch

from jiro.core.review_tdd import TddReviewValidator
from jiro.steps.types import StepType


class TestTddReviewValidator:
    """Tests for TddReviewValidator."""

    @patch("subprocess.run")
    def test_validate_red_phase_only_test_files(self, mock_run: MagicMock) -> None:
        """Test that red phase validation checks for only test files."""
        # Mock git show output with only test files
        mock_run.return_value = MagicMock(
            stdout="tests/test_example.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_RED, "abc123")

        assert is_valid is True
        assert results["red_phase"] == "PASSED"

    @patch("subprocess.run")
    def test_validate_red_phase_rejects_implementation_files(self, mock_run: MagicMock) -> None:
        """Test that red phase rejects implementation files."""
        # Mock git show output with implementation file
        mock_run.return_value = MagicMock(
            stdout="src/example.py\ntests/test_example.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_RED, "abc123")

        assert is_valid is False
        assert "FAILED" in results["red_phase"]
        assert "src/example.py" in results["red_phase"]

    @patch("subprocess.run")
    def test_validate_green_phase_rejects_test_files(self, mock_run: MagicMock) -> None:
        """Test that green phase rejects test file changes."""
        # Mock git show output with test file
        mock_run.return_value = MagicMock(
            stdout="src/example.py\ntests/test_example.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_GREEN, "abc123")

        assert is_valid is False
        assert "FAILED" in results["green_phase"]
        assert "test_example.py" in results["green_phase"]

    @patch("subprocess.run")
    def test_validate_green_phase_only_implementation_files(self, mock_run: MagicMock) -> None:
        """Test that green phase allows only implementation files."""
        # Mock git show output with only implementation files
        mock_run.return_value = MagicMock(
            stdout="src/example.py\nsrc/module.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_GREEN, "abc123")

        assert is_valid is True
        assert results["green_phase"] == "PASSED"

    @patch("subprocess.run")
    def test_validate_refactor_phase_rejects_test_files(self, mock_run: MagicMock) -> None:
        """Test that refactor phase rejects test file changes."""
        # Mock git show output with test file
        mock_run.return_value = MagicMock(
            stdout="src/example.py\ntests/test_example.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_REFACTOR, "abc123")

        assert is_valid is False
        assert "FAILED" in results["refactor_phase"]
        assert "test_example.py" in results["refactor_phase"]

    @patch("subprocess.run")
    def test_validate_refactor_phase_only_implementation_files(self, mock_run: MagicMock) -> None:
        """Test that refactor phase allows only implementation files."""
        # Mock git show output with only implementation files
        mock_run.return_value = MagicMock(
            stdout="src/example.py\nsrc/refactored.py\n",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_REFACTOR, "abc123")

        assert is_valid is True
        assert results["refactor_phase"] == "PASSED"

    @patch("subprocess.run")
    def test_validate_handles_git_error(self, mock_run: MagicMock) -> None:
        """Test that validation handles git errors gracefully."""
        # Mock git command failure
        mock_run.side_effect = Exception("git not found")

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_RED, "abc123")

        assert is_valid is False
        assert "FAILED" in results["red_phase"]
        assert "Could not get changed files" in results["red_phase"]

    @patch("subprocess.run")
    def test_validate_empty_changeset(self, mock_run: MagicMock) -> None:
        """Test validation with empty changeset."""
        # Mock git show output with no files
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
        )

        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.TDD_RED, "abc123")

        # Empty changeset passes (no non-test files)
        assert is_valid is True
        assert results["red_phase"] == "PASSED"

    def test_validate_unknown_step_type(self) -> None:
        """Test validation with unknown step type."""
        is_valid, results = TddReviewValidator.validate_tdd_phase(StepType.DOCUMENTATION, "abc123")

        # Non-TDD steps have empty results but overall pass
        assert is_valid is True
