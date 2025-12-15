"""Tests for TddGreenVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.tdd.green.tdd_green_result import TddGreenResult
from jiro.steps.tdd.green.tdd_green_verify import TddGreenVerify
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification, VerificationResult


class TestTddGreenVerifyIsVerification:
    """Test that TddGreenVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """TddGreenVerify should inherit from Verification."""
        assert issubclass(TddGreenVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate TddGreenVerify."""
        verify = TddGreenVerify()
        assert isinstance(verify, TddGreenVerify)


class TestTddGreenVerifyOnlyImplementationFiles:
    """Test the _verify_only_implementation_files rule."""

    def test_accepts_implementation_files(self):
        """Should accept files NOT in tests/ directory."""
        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_only_implementation_files(result)

    def test_rejects_test_files(self):
        """Should reject files in tests/ directory."""
        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("tests/test_auth.py")],  # Test file not allowed
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Only implementation files allowed"):
            verify._verify_only_implementation_files(result)

    def test_rejects_test_suffix_files(self):
        """Should reject files ending with _test.py."""
        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("src/auth_test.py")],  # Test file not allowed
            test_specifier="src/auth_test.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth_test.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Only implementation files allowed"):
            verify._verify_only_implementation_files(result)

    def test_is_test_file_helper(self):
        """Test the _is_test_file helper."""
        verify = TddGreenVerify()

        assert verify._is_test_file(Path("tests/test_auth.py"))
        assert verify._is_test_file(Path("tests/unit/test_login.py"))
        assert verify._is_test_file(Path("src/auth_test.py"))
        assert not verify._is_test_file(Path("src/auth.py"))
        assert not verify._is_test_file(Path("src/models/user.py"))


class TestTddGreenVerifyGitDiff:
    """Test the _verify_git_diff_matches rule."""

    @patch("subprocess.run")
    def test_git_diff_matches(self, mock_run):
        """Should pass when git diff matches changed_files."""
        # Mock git diff output
        mock_run.return_value = MagicMock(
            stdout="src/auth.py\n",
            stderr="",
            returncode=0,
        )

        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_git_diff_matches(result)

    @patch("subprocess.run")
    def test_git_diff_mismatch(self, mock_run):
        """Should fail when git diff doesn't match changed_files."""
        # Mock git diff output with different file
        mock_run.return_value = MagicMock(
            stdout="src/models/user.py\n",
            stderr="",
            returncode=0,
        )

        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="git diff does not match"):
            verify._verify_git_diff_matches(result)


class TestTddGreenVerifyTestPasses:
    """Test the _verify_test_passes rule."""

    def test_missing_test_specifier(self):
        """Should fail if test_specifier is missing."""
        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = None

        with pytest.raises(VerificationError, match="Missing test_specifier"):
            verify._verify_test_passes(result)

    @patch("subprocess.run")
    def test_test_fails_is_error(self, mock_run):
        """Should fail if test fails (exit code non-zero)."""
        # Mock pytest output showing test failed
        mock_run.return_value = MagicMock(
            stdout="FAILED test_example",
            stderr="",
            returncode=1,  # Failure = test failed = BAD for green step
        )

        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test_example"

        with pytest.raises(VerificationError, match="Test does not pass"):
            verify._verify_test_passes(result)

    @patch("subprocess.run")
    def test_test_passes_is_success(self, mock_run):
        """Should pass if test passes (exit code 0)."""
        # Mock pytest output showing test passed
        mock_run.return_value = MagicMock(
            stdout="PASSED test_example",
            stderr="",
            returncode=0,  # Success = test passed = GOOD for green step
        )

        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test_example"

        output = verify._verify_test_passes(result)
        assert "PASSED" in output


class TestTddGreenVerifySkipRemoved:
    """Test the _verify_skip_removed rule."""

    def test_missing_test_specifier(self):
        """Should fail if test_specifier is missing."""
        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = None

        with pytest.raises(VerificationError, match="Missing test_specifier"):
            verify._verify_skip_removed(result)

    def test_invalid_test_specifier_format(self):
        """Should fail if test_specifier doesn't contain '::'."""
        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py"  # Missing ::test_name

        with pytest.raises(VerificationError, match="Invalid test_specifier format"):
            verify._verify_skip_removed(result)

    def test_file_not_readable(self):
        """Should fail if file cannot be read."""
        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = "tests/nonexistent.py::test_example"

        with pytest.raises(VerificationError, match="Could not read test file"):
            verify._verify_skip_removed(result)

    def test_skip_marker_still_present(self, tmp_path):
        """Should fail if @pytest.mark.skip is still present."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            '@pytest.mark.skip(reason="TDD red: awaiting implementation")\n'
            "def test_example():\n"
            "    assert True\n"
        )

        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = f"{test_file}::test_example"

        with pytest.raises(VerificationError, match="still has @pytest.mark.skip"):
            verify._verify_skip_removed(result)

    def test_skip_marker_removed(self, tmp_path):
        """Should pass if @pytest.mark.skip has been removed."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_example():\n    assert True\n")

        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = f"{test_file}::test_example"

        # Should not raise
        verify._verify_skip_removed(result)

    def test_different_skip_marker_ok(self, tmp_path):
        """Should pass if skip marker is on different test."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            '@pytest.mark.skip(reason="TDD red: awaiting implementation")\n'
            "def test_other():\n"
            "    assert False\n"
            "\n"
            "def test_example():\n"
            "    assert True\n"
        )

        verify = TddGreenVerify()
        result = MagicMock()
        result.test_specifier = f"{test_file}::test_example"

        # Should not raise - skip is on test_other, not test_example
        verify._verify_skip_removed(result)


class TestTddGreenVerifyIntegration:
    """Integration tests for verify method."""

    @patch("subprocess.run")
    def test_verify_returns_verification_result(self, mock_run, tmp_path):
        """verify() should return VerificationResult on success."""
        # Setup test file
        full_path = tmp_path / "tests" / "test_auth.py"
        full_path.parent.mkdir(parents=True)
        full_path.write_text("def test_example():\n    assert True\n")

        # Mock git diff and pytest
        mock_run.side_effect = [
            # First call: git diff
            MagicMock(
                stdout="src/auth.py\n",
                stderr="",
                returncode=0,
            ),
            # Second call: pytest
            MagicMock(
                stdout="PASSED tests/test_auth.py::test_example",
                stderr="",
                returncode=0,  # Test passes (good for green)
            ),
        ]

        verify = TddGreenVerify()
        result = TddGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier=f"{full_path}::test_example",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = verify.verify(result=result)

        assert isinstance(verification, VerificationResult)
        assert verification.success is True
