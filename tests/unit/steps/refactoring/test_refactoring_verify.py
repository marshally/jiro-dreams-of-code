"""Tests for RefactoringVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.refactoring.refactoring_result import RefactoringResult
from jiro.steps.refactoring.refactoring_verify import RefactoringVerify
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification, VerificationResult


class TestRefactoringVerifyIsVerification:
    """Test that RefactoringVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """RefactoringVerify should inherit from Verification."""
        assert issubclass(RefactoringVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate RefactoringVerify."""
        verify = RefactoringVerify()
        assert isinstance(verify, RefactoringVerify)


class TestRefactoringVerifyOnlyImplementationFiles:
    """Test the _verify_only_implementation_files rule."""

    def test_accepts_implementation_files(self):
        """Should accept non-test implementation files."""
        verify = RefactoringVerify()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        # Should not raise
        verify._verify_only_implementation_files(result)

    def test_rejects_test_files(self):
        """Should reject test files."""
        verify = RefactoringVerify()
        result = RefactoringResult(
            changed_files=[Path("tests/test_auth.py")],  # Test file
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        with pytest.raises(VerificationError, match="Only implementation files allowed"):
            verify._verify_only_implementation_files(result)

    def test_rejects_test_suffix_files(self):
        """Should reject files ending with _test.py."""
        verify = RefactoringVerify()
        result = RefactoringResult(
            changed_files=[Path("src/auth_test.py")],  # Test suffix file
            test_specifier="src/auth_test.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        with pytest.raises(VerificationError, match="Only implementation files allowed"):
            verify._verify_only_implementation_files(result)

    def test_is_test_file_helper(self):
        """Test the _is_test_file helper."""
        verify = RefactoringVerify()

        assert verify._is_test_file(Path("tests/test_auth.py"))
        assert verify._is_test_file(Path("tests/unit/test_login.py"))
        assert verify._is_test_file(Path("src/auth_test.py"))
        assert not verify._is_test_file(Path("src/auth.py"))
        assert not verify._is_test_file(Path("src/models/user.py"))


class TestRefactoringVerifyGitDiff:
    """Test the _verify_git_diff_matches rule."""

    @patch("subprocess.run")
    def test_accepts_matching_git_diff(self, mock_run):
        """Should accept when git diff matches changed_files."""
        verify = RefactoringVerify()

        # Mock git diff output
        mock_result = MagicMock()
        mock_result.stdout = "src/auth.py\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        # Should not raise
        verify._verify_git_diff_matches(result)

    @patch("subprocess.run")
    def test_rejects_mismatched_git_diff(self, mock_run):
        """Should reject when git diff doesn't match changed_files."""
        verify = RefactoringVerify()

        # Mock git diff output with different files
        mock_result = MagicMock()
        mock_result.stdout = "src/other.py\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        with pytest.raises(VerificationError, match="git diff does not match changed_files"):
            verify._verify_git_diff_matches(result)

    @patch("subprocess.run")
    def test_git_diff_command_fails(self, mock_run):
        """Should handle git diff command failures."""
        verify = RefactoringVerify()

        # Mock git diff failure
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git", stderr="fatal: not a git repo")

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        with pytest.raises(VerificationError, match="Could not run git diff"):
            verify._verify_git_diff_matches(result)


class TestRefactoringVerifyTestsPass:
    """Test the _verify_tests_pass rule."""

    @patch("subprocess.run")
    def test_accepts_passing_tests(self, mock_run):
        """Should accept when tests pass."""
        verify = RefactoringVerify()

        # Mock pytest success
        mock_result = MagicMock()
        mock_result.stdout = "PASSED\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        # Should not raise
        output = verify._verify_tests_pass(result)
        assert "PASSED" in output

    @patch("subprocess.run")
    def test_rejects_failing_tests(self, mock_run):
        """Should reject when tests fail."""
        verify = RefactoringVerify()

        # Mock pytest failure
        mock_result = MagicMock()
        mock_result.stdout = "FAILED\n"
        mock_result.stderr = ""
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        with pytest.raises(VerificationError, match="Tests do not pass"):
            verify._verify_tests_pass(result)


class TestRefactoringVerifyChecksum:
    """Test the _verify_checksum rule."""

    def test_accepts_valid_checksum(self):
        """Should accept result with valid checksum."""
        verify = RefactoringVerify()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123def456",
        )

        # Should not raise
        verify._verify_checksum(result)

    def test_handles_empty_checksum(self):
        """Should handle empty checksum gracefully (optional feature)."""
        verify = RefactoringVerify()
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="",
        )

        # Should not raise - checksum is optional for now
        verify._verify_checksum(result)


class TestRefactoringVerifyIntegration:
    """Test the verify method integration."""

    @patch("subprocess.run")
    def test_verify_success(self, mock_run):
        """Should return VerificationResult on success."""
        verify = RefactoringVerify()

        # Mock git diff
        git_result = MagicMock()
        git_result.stdout = "src/auth.py\n"
        git_result.stderr = ""
        git_result.returncode = 0

        # Mock pytest
        pytest_result = MagicMock()
        pytest_result.stdout = "PASSED\n"
        pytest_result.stderr = ""
        pytest_result.returncode = 0

        mock_run.side_effect = [git_result, pytest_result]

        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )

        verification = verify.verify(result=result)
        assert isinstance(verification, VerificationResult)
        assert verification.success is True
        assert "PASSED" in verification.verification_output
