"""Tests for TestOnlyVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.test.only.test_only_verify import TestOnlyVerify
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification


class TestTestOnlyVerifyIsVerification:
    """Test that TestOnlyVerify is a proper Verification."""

    def test_is_verification_subclass(self):
        """TestOnlyVerify should inherit from Verification."""
        assert issubclass(TestOnlyVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate TestOnlyVerify."""
        verify = TestOnlyVerify()
        assert isinstance(verify, TestOnlyVerify)

    def test_has_verify_method(self):
        """TestOnlyVerify should have verify method."""
        verify = TestOnlyVerify()
        assert hasattr(verify, "verify")
        assert callable(verify.verify)


class TestTestOnlyVerifyIsTestFile:
    """Test the _is_test_file helper method."""

    def test_test_file_with_test_prefix(self):
        """Should recognize files with test_ prefix in tests/ directory."""
        verify = TestOnlyVerify()
        assert verify._is_test_file(Path("tests/test_auth.py"))
        assert verify._is_test_file(Path("tests/test_utils.py"))

    def test_test_file_with_test_suffix(self):
        """Should recognize files with _test.py suffix in tests/ directory."""
        verify = TestOnlyVerify()
        assert verify._is_test_file(Path("tests/auth_test.py"))
        assert verify._is_test_file(Path("tests/utils_test.py"))

    def test_non_test_file_not_in_tests_dir(self):
        """Should reject files not in tests/ directory."""
        verify = TestOnlyVerify()
        assert not verify._is_test_file(Path("src/test_auth.py"))
        assert not verify._is_test_file(Path("test_auth.py"))

    def test_non_test_file_wrong_prefix(self):
        """Should reject files in tests/ dir without test_ prefix or _test suffix."""
        verify = TestOnlyVerify()
        assert not verify._is_test_file(Path("tests/auth.py"))
        assert not verify._is_test_file(Path("tests/utils.py"))

    def test_nested_test_directory(self):
        """Should recognize test files in nested tests/ directories."""
        verify = TestOnlyVerify()
        assert verify._is_test_file(Path("tests/unit/test_auth.py"))
        assert verify._is_test_file(Path("tests/integration/api_test.py"))


class TestTestOnlyVerifyOnlyTestFiles:
    """Test verification of only test files."""

    def test_only_test_files_passes(self):
        """Should pass when only test files are in changed_files."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.changed_files = [Path("tests/test_auth.py")]

        # Should not raise
        verify._verify_only_test_files(result)

    def test_multiple_test_files_passes(self):
        """Should pass with multiple test files."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.changed_files = [
            Path("tests/test_auth.py"),
            Path("tests/test_utils_test.py"),
        ]

        # Should not raise
        verify._verify_only_test_files(result)

    def test_non_test_file_fails(self):
        """Should fail if non-test file is in changed_files."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.changed_files = [
            Path("tests/test_auth.py"),
            Path("src/auth.py"),  # Non-test file
        ]

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_only_test_files(result)

        assert exc_info.value.step_type == StepType.TEST_ONLY
        assert "Only test files allowed" in exc_info.value.rule_violated

    def test_file_in_src_directory_fails(self):
        """Should fail if file is in src directory instead of tests."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.changed_files = [Path("src/test_auth.py")]

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_only_test_files(result)

        assert exc_info.value.step_type == StepType.TEST_ONLY


class TestTestOnlyVerifyOneTestPerCommit:
    """Test verification of one test per commit."""

    def test_single_test_passes(self):
        """Should pass with single test specifier."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test_new_validation"

        # Should not raise
        verify._verify_one_test_per_commit(result)

    def test_multiple_tests_fails(self):
        """Should fail with multiple test specifiers."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test1 tests/test_auth.py::test2"

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_one_test_per_commit(result)

        assert exc_info.value.step_type == StepType.TEST_ONLY
        assert "Multiple tests" in exc_info.value.rule_violated

    def test_missing_test_specifier_fails(self):
        """Should fail if test_specifier is missing."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.test_specifier = None

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_one_test_per_commit(result)

        assert exc_info.value.step_type == StepType.TEST_ONLY
        assert "Missing test_specifier" in exc_info.value.rule_violated

    def test_invalid_format_fails(self):
        """Should fail with invalid specifier format."""
        verify = TestOnlyVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py"  # Missing :: separator

        with pytest.raises(VerificationError) as exc_info:
            verify._verify_one_test_per_commit(result)

        assert exc_info.value.step_type == StepType.TEST_ONLY
        assert "Invalid test_specifier format" in exc_info.value.rule_violated


class TestTestOnlyVerifyIntegration:
    """Integration tests for full verification."""

    @patch("subprocess.run")
    def test_verify_success(self, mock_run):
        """Should succeed with valid result and git state."""
        # Mock git diff output
        mock_git_diff = MagicMock()
        mock_git_diff.stdout = "tests/test_new.py\n"
        mock_git_diff.returncode = 0

        # Mock pytest output
        mock_pytest = MagicMock()
        mock_pytest.stdout = "1 passed in 0.15s"
        mock_pytest.stderr = ""
        mock_pytest.returncode = 0

        def run_side_effect(*args, **kwargs):
            if "diff" in args[0]:
                return mock_git_diff
            elif "pytest" in args[0]:
                return mock_pytest
            return MagicMock()

        mock_run.side_effect = run_side_effect

        verify = TestOnlyVerify()
        result = MagicMock()
        result.changed_files = [Path("tests/test_new.py")]
        result.test_specifier = "tests/test_new.py::test_example"

        verification_result = verify.verify(result=result)

        assert verification_result.success
        assert "pytest" in verification_result.verification_command
