"""Tests for RefactoringResult dataclass."""

from pathlib import Path

from jiro.results.base import Result
from jiro.steps.refactoring.refactoring_result import RefactoringResult


class TestRefactoringResultIsResult:
    """Test that RefactoringResult is a proper Result subclass."""

    def test_is_result_subclass(self):
        """RefactoringResult should inherit from Result."""
        assert issubclass(RefactoringResult, Result)

    def test_can_instantiate(self):
        """Should be able to instantiate RefactoringResult."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )
        assert isinstance(result, RefactoringResult)


class TestRefactoringResultAttributes:
    """Test RefactoringResult attributes."""

    def test_has_changed_files(self):
        """Should have changed_files from base class."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py"), Path("src/models/user.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="extract_method",
            checksum="def456",
        )
        assert len(result.changed_files) == 2
        assert Path("src/auth.py") in result.changed_files

    def test_has_test_specifier(self):
        """Should have test_specifier."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )
        assert result.test_specifier == "tests/test_auth.py::test_login"

    def test_has_test_output(self):
        """Should have test_output."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED\nAll tests passed",
            refactoring_type="rename",
            checksum="abc123",
        )
        assert "PASSED" in result.test_output

    def test_has_refactoring_type(self):
        """Should have refactoring_type."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="extract_method",
            checksum="abc123",
        )
        assert result.refactoring_type == "extract_method"

    def test_has_checksum(self):
        """Should have checksum."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="xyz789",
        )
        assert result.checksum == "xyz789"


class TestRefactoringResultSerialization:
    """Test RefactoringResult serialization methods."""

    def test_as_dict(self):
        """Should convert to dict with Path as string."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )
        result_dict = result.as_dict()
        assert result_dict["changed_files"] == ["src/auth.py"]
        assert result_dict["test_specifier"] == "tests/test_auth.py::test_login"
        assert result_dict["refactoring_type"] == "rename"

    def test_as_json(self):
        """Should convert to JSON string."""
        result = RefactoringResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
        )
        json_str = result.as_json()
        assert "src/auth.py" in json_str
        assert "test_specifier" in json_str
        assert "rename" in json_str
