"""Tests for LintFixVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from jiro.steps.lint.fix.lint_fix_result import LintFixResult
from jiro.steps.lint.fix.lint_fix_verify import LintFixVerify
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult


class TestLintFixVerifyClass:
    """Test that LintFixVerify is properly defined."""

    def test_inherits_from_verification(self):
        """LintFixVerify should inherit from Verification."""
        assert issubclass(LintFixVerify, Verification)


class TestLintFixVerifySingleFile:
    """Test single file verification rule."""

    def test_single_file_passes(self):
        """Should pass when exactly one file is changed."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Should not raise
        verify._verify_single_file_changed(result)

    def test_multiple_files_fails(self):
        """Should fail when multiple files are changed."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[
                Path("src/example.py"),
                Path("src/other.py"),
            ],
            error_code="E501",
            filename="src/example.py",
        )

        try:
            verify._verify_single_file_changed(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "Single file required" in e.rule_violated

    def test_no_files_fails(self):
        """Should fail when no files are changed."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[],
            error_code="E501",
            filename="src/example.py",
        )

        try:
            verify._verify_single_file_changed(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "Single file required" in e.rule_violated


class TestLintFixVerifyGitDiff:
    """Test git diff verification rule."""

    @patch("jiro.steps.lint.fix.lint_fix_verify.subprocess.run")
    def test_git_diff_matches(self, mock_run):
        """Should pass when git diff matches changed_files."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock git diff output
        mock_process = MagicMock()
        mock_process.stdout = "src/example.py\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Should not raise
        verify._verify_git_diff_matches(result)

    @patch("jiro.steps.lint.fix.lint_fix_verify.subprocess.run")
    def test_git_diff_mismatch(self, mock_run):
        """Should fail when git diff doesn't match changed_files."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock git diff output that doesn't match
        mock_process = MagicMock()
        mock_process.stdout = "src/other.py\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        try:
            verify._verify_git_diff_matches(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "git diff does not match" in e.rule_violated


class TestLintFixVerifyLintPasses:
    """Test lint passes verification rule."""

    @patch("jiro.steps.lint.fix.lint_fix_verify.subprocess.run")
    def test_lint_passes(self, mock_run):
        """Should pass when lint returns exit code 0."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock flake8 success
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        output = verify._verify_lint_passes(result)
        assert "Lint passed" in output
        assert "src/example.py" in output

    @patch("jiro.steps.lint.fix.lint_fix_verify.subprocess.run")
    def test_lint_fails(self, mock_run):
        """Should fail when lint returns non-zero exit code."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock flake8 failure
        mock_process = MagicMock()
        mock_process.stdout = "src/example.py:1:1: E501 line too long\n"
        mock_process.stderr = ""
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        try:
            verify._verify_lint_passes(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "Lint does not pass" in e.rule_violated

    def test_missing_filename(self):
        """Should fail when filename is missing."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="",
        )

        try:
            verify._verify_lint_passes(result)
            raise AssertionError("Should raise VerificationError")
        except VerificationError as e:
            assert e.step_type == StepType.LINT_FIX
            assert "Missing filename" in e.rule_violated


class TestLintFixVerifyIntegration:
    """Test full verification flow."""

    @patch("jiro.steps.lint.fix.lint_fix_verify.subprocess.run")
    def test_verify_success(self, mock_run):
        """Should return VerificationResult on success."""
        verify = LintFixVerify()
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        # Mock git diff success
        mock_git_process = MagicMock()
        mock_git_process.stdout = "src/example.py\n"
        mock_git_process.returncode = 0

        # Mock flake8 success
        mock_flake8_process = MagicMock()
        mock_flake8_process.stdout = ""
        mock_flake8_process.stderr = ""
        mock_flake8_process.returncode = 0

        mock_run.side_effect = [mock_git_process, mock_flake8_process]

        verification = verify.verify(result=result)

        assert isinstance(verification, VerificationResult)
        assert verification.success is True
        assert "flake8" in verification.verification_command
        assert verification.verification_time >= 0
