"""Tests for BugRedVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.bug.red.bug_red_result import BugRedResult
from jiro.steps.bug.red.bug_red_verify import BugRedVerify
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification


class TestBugRedVerifyIsVerification:
    """Test that BugRedVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """BugRedVerify should inherit from Verification."""
        assert issubclass(BugRedVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate BugRedVerify."""
        verify = BugRedVerify()
        assert isinstance(verify, BugRedVerify)


class TestBugRedVerifyOnlyTestFiles:
    """Test the _verify_only_test_files rule."""

    def test_accepts_test_files(self):
        """Should accept files in tests/ directory."""
        verify = BugRedVerify()
        result = BugRedResult(
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
        verify = BugRedVerify()
        result = BugRedResult(
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
        verify = BugRedVerify()
        result = BugRedResult(
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
        verify = BugRedVerify()

        assert verify._is_test_file(Path("tests/test_auth.py"))
        assert verify._is_test_file(Path("tests/unit/test_login.py"))
        assert verify._is_test_file(Path("src/auth_test.py"))
        assert not verify._is_test_file(Path("src/auth.py"))
        assert not verify._is_test_file(Path("src/models/user.py"))


class TestBugRedVerifyGitDiff:
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

        verify = BugRedVerify()
        result = BugRedResult(
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

        verify = BugRedVerify()
        result = BugRedResult(
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


class TestBugRedVerifyTestFails:
    """Test the _verify_test_fails rule."""

    @patch("subprocess.run")
    def test_test_fails_proves_bug(self, mock_run):
        """Should accept test that fails (proving bug exists)."""
        # Mock pytest output showing test failed
        mock_run.return_value = MagicMock(
            stdout="FAILED tests/test_auth.py::test_example - assert None\n",
            stderr="",
            returncode=1,  # Non-zero means test failed
        )

        verify = BugRedVerify()
        result = BugRedResult(
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
        output = verify._verify_test_fails(result)
        assert "FAILED" in output

    @patch("subprocess.run")
    def test_test_passes_fails_verification(self, mock_run):
        """Should reject test that passes (bug doesn't exist)."""
        # Mock pytest output showing test passed
        mock_run.return_value = MagicMock(
            stdout="PASSED tests/test_auth.py::test_example\n",
            stderr="",
            returncode=0,  # Zero means test passed
        )

        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Test does not fail"):
            verify._verify_test_fails(result)

    def test_missing_test_specifier(self):
        """Should fail if test_specifier is missing."""
        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example",
            test_specifier="",  # Empty specifier
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Missing test_specifier"):
            verify._verify_test_fails(result)


class TestBugRedVerifySkipMarker:
    """Test the _verify_test_is_skipped rule."""

    def test_skip_marker_correct(self, tmp_path):
        """Should accept test with correct skip marker."""
        # Create a temporary test file
        test_file = tmp_path / "test_auth.py"
        test_file.write_text(
            """import pytest

@pytest.mark.skip(reason="Bug red: awaiting fix")
def test_login_bug():
    assert False
"""
        )

        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[test_file],
            test_file=test_file,
            test_name="test_login_bug",
            test_specifier="tests/test_auth.py::test_login_bug",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_test_is_skipped(result)

    def test_skip_marker_missing(self, tmp_path):
        """Should reject test without skip marker."""
        # Create a temporary test file without skip
        test_file = tmp_path / "test_auth.py"
        test_file.write_text(
            """import pytest

def test_login_bug():
    assert False
"""
        )

        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[test_file],
            test_file=test_file,
            test_name="test_login_bug",
            test_specifier="tests/test_auth.py::test_login_bug",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="not marked with @pytest.mark.skip"):
            verify._verify_test_is_skipped(result)

    def test_skip_marker_wrong_reason(self, tmp_path):
        """Should reject skip marker with wrong reason."""
        # Create a test file with wrong skip reason
        test_file = tmp_path / "test_auth.py"
        test_file.write_text(
            """import pytest

@pytest.mark.skip(reason="TDD red: awaiting implementation")
def test_login_bug():
    assert False
"""
        )

        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[test_file],
            test_file=test_file,
            test_name="test_login_bug",
            test_specifier="tests/test_auth.py::test_login_bug",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="not marked with @pytest.mark.skip"):
            verify._verify_test_is_skipped(result)

    def test_missing_test_file(self):
        """Should fail if test_file is missing."""
        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("nonexistent.py"),
            test_name="test_example",
            test_specifier="tests/test_auth.py::test_example",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="Could not read test file"):
            verify._verify_test_is_skipped(result)


class TestBugRedVerifyIntegration:
    """Integration tests for the verify method."""

    @patch("subprocess.run")
    def test_full_verification_success(self, mock_run, tmp_path):
        """Full verification should succeed with valid result."""
        # Create test file in a tests directory structure
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_bug.py"
        test_file.write_text(
            """import pytest

@pytest.mark.skip(reason="Bug red: awaiting fix")
def test_my_bug():
    assert False
"""
        )

        # Mock git diff and pytest
        mock_run.side_effect = [
            # git diff call - return relative path
            MagicMock(
                stdout="tests/test_bug.py\n",
                stderr="",
                returncode=0,
            ),
            # pytest call
            MagicMock(
                stdout="FAILED test::test_my_bug\n",
                stderr="",
                returncode=1,
            ),
        ]

        verify = BugRedVerify()
        result = BugRedResult(
            changed_files=[Path("tests/test_bug.py")],
            test_file=test_file,
            test_name="test_my_bug",
            test_specifier="tests/test_bug.py::test_my_bug",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = verify.verify(result=result)

        assert verification.success
        assert "FAILED" in verification.verification_output
