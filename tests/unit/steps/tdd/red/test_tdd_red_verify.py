"""Tests for TddRedVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.tdd.red.tdd_red_result import TddRedResult
from jiro.steps.tdd.red.tdd_red_verify import TddRedVerify
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification, VerificationResult


class TestTddRedVerifyIsVerification:
    """Test that TddRedVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """TddRedVerify should inherit from Verification."""
        assert issubclass(TddRedVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate TddRedVerify."""
        verify = TddRedVerify()
        assert isinstance(verify, TddRedVerify)


class TestTddRedVerifyOnlyTestFiles:
    """Test the _verify_only_test_files rule."""

    def test_accepts_test_files(self):
        """Should accept files in tests/ directory."""
        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_only_test_files(result)

    def test_accepts_test_suffix_files(self):
        """Should accept files ending with _test.py."""
        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[Path("src/auth_test.py")],
            test_file=Path("src/auth_test.py"),
            test_name="test_example",
            test_specifier="src/auth_test.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_only_test_files(result)

    def test_rejects_non_test_files(self):
        """Should reject non-test files."""
        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[Path("src/auth.py")],  # Not a test file
            test_file=Path("src/auth.py"),
            test_name="test_example",
            test_specifier="src/auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Only test files allowed"):
            verify._verify_only_test_files(result)

    def test_is_test_file_helper(self):
        """Test the _is_test_file helper."""
        verify = TddRedVerify()

        assert verify._is_test_file(Path("tests/test_auth.py"))
        assert verify._is_test_file(Path("tests/unit/test_login.py"))
        assert verify._is_test_file(Path("src/auth_test.py"))
        assert not verify._is_test_file(Path("src/auth.py"))
        assert not verify._is_test_file(Path("src/models/user.py"))


class TestTddRedVerifyGitDiff:
    """Test the _verify_git_diff_matches rule."""

    @patch("subprocess.run")
    def test_git_diff_matches(self, mock_run):
        """Should pass when git diff matches changed_files."""
        # Mock git diff output
        mock_run.return_value = MagicMock(
            stdout="tests/test_auth.py\n",
            stderr="",
            returncode=0,
        )

        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
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
            stdout="tests/test_login.py\n",
            stderr="",
            returncode=0,
        )

        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="git diff does not match"):
            verify._verify_git_diff_matches(result)


class TestTddRedVerifyTestFails:
    """Test the _verify_test_fails rule."""

    def test_missing_test_specifier(self):
        """Should fail if test_specifier is missing."""
        verify = TddRedVerify()
        result = MagicMock()
        result.test_specifier = None

        with pytest.raises(VerificationError, match="Missing test_specifier"):
            verify._verify_test_fails(result)

    @patch("subprocess.run")
    def test_test_passes_is_error(self, mock_run):
        """Should fail if test passes (exit code 0)."""
        # Mock pytest output showing test passed
        mock_run.return_value = MagicMock(
            stdout="test passed\n",
            stderr="",
            returncode=0,  # Success = test passed = BAD for red step
        )

        verify = TddRedVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test_example"

        with pytest.raises(VerificationError, match="Test does not fail"):
            verify._verify_test_fails(result)

    @patch("subprocess.run")
    def test_test_fails_is_success(self, mock_run):
        """Should pass if test fails (non-zero exit code)."""
        # Mock pytest output showing test failed
        mock_run.return_value = MagicMock(
            stdout="FAILED test_example",
            stderr="",
            returncode=1,  # Failure = test failed = GOOD for red step
        )

        verify = TddRedVerify()
        result = MagicMock()
        result.test_specifier = "tests/test_auth.py::test_example"

        output = verify._verify_test_fails(result)
        assert "FAILED" in output


class TestTddRedVerifySkipMarker:
    """Test the _verify_test_is_skipped rule."""

    def test_missing_test_file(self, tmp_path):
        """Should fail if test_file is missing."""
        verify = TddRedVerify()
        result = MagicMock()
        result.test_file = None

        with pytest.raises(VerificationError, match="Missing test_file"):
            verify._verify_test_is_skipped(result)

    def test_missing_test_name(self, tmp_path):
        """Should fail if test_name is missing."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_example(): pass")

        verify = TddRedVerify()
        result = MagicMock()
        result.test_file = test_file
        result.test_name = None

        with pytest.raises(VerificationError, match="Missing test_name"):
            verify._verify_test_is_skipped(result)

    def test_file_not_readable(self):
        """Should fail if file cannot be read."""
        verify = TddRedVerify()
        result = MagicMock()
        result.test_file = Path("/nonexistent/file.py")
        result.test_name = "test_example"

        with pytest.raises(VerificationError, match="Could not read test file"):
            verify._verify_test_is_skipped(result)

    def test_skip_marker_present(self, tmp_path):
        """Should pass if @pytest.mark.skip is present."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            '@pytest.mark.skip(reason="TDD red: awaiting implementation")\n'
            "def test_example():\n"
            "    assert False\n"
        )

        verify = TddRedVerify()
        result = MagicMock()
        result.test_file = test_file
        result.test_name = "test_example"

        # Should not raise
        verify._verify_test_is_skipped(result)

    def test_skip_marker_missing(self, tmp_path):
        """Should fail if @pytest.mark.skip is missing."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_example():\n    assert False\n")

        verify = TddRedVerify()
        result = MagicMock()
        result.test_file = test_file
        result.test_name = "test_example"

        with pytest.raises(VerificationError, match="not marked with @pytest.mark.skip"):
            verify._verify_test_is_skipped(result)


class TestTddRedVerifyIntegration:
    """Integration tests for verify method."""

    @patch("subprocess.run")
    def test_verify_returns_verification_result(self, mock_run, tmp_path):
        """verify() should return VerificationResult on success."""
        # Setup test file - use relative path
        test_file = Path("tests/test_auth.py")
        full_path = tmp_path / "tests" / "test_auth.py"
        full_path.parent.mkdir(parents=True)
        full_path.write_text(
            '@pytest.mark.skip(reason="TDD red: awaiting implementation")\n'
            "def test_example():\n"
            "    assert False\n"
        )

        # Mock git diff and pytest
        mock_run.side_effect = [
            # First call: git diff
            MagicMock(
                stdout="tests/test_auth.py\n",
                stderr="",
                returncode=0,
            ),
            # Second call: pytest
            MagicMock(
                stdout="FAILED tests/test_auth.py::test_example",
                stderr="",
                returncode=1,  # Test fails (good for red)
            ),
        ]

        verify = TddRedVerify()
        result = TddRedResult(
            changed_files=[test_file],
            test_file=full_path,
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = verify.verify(result=result)

        assert isinstance(verification, VerificationResult)
        assert verification.success is True
