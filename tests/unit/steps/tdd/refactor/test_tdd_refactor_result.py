"""Tests for TddRefactorResult dataclass."""

from pathlib import Path

from jiro.results.base import Result
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult


class TestTddRefactorResultIsResult:
    """Test that TddRefactorResult is a proper Result subclass."""

    def test_is_result_subclass(self):
        """TddRefactorResult should inherit from Result."""
        assert issubclass(TddRefactorResult, Result)

    def test_can_instantiate(self):
        """Should be able to instantiate TddRefactorResult."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor this code",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert isinstance(result, TddRefactorResult)


class TestTddRefactorResultAttributes:
    """Test TddRefactorResult attributes."""

    def test_has_changed_files(self):
        """Should have changed_files from base class."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py"), Path("src/models/user.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="extract_method",
            checksum="def456",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert len(result.changed_files) == 2
        assert Path("src/auth.py") in result.changed_files

    def test_has_test_specifier(self):
        """Should have test_specifier."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert result.test_specifier == "tests/test_auth.py::test_login"

    def test_has_test_output(self):
        """Should have test_output."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED\nAll tests passed",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert "PASSED" in result.test_output

    def test_has_refactoring_type(self):
        """Should have refactoring_type."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="extract_method",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert result.refactoring_type == "extract_method"

    def test_has_checksum(self):
        """Should have checksum."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="xyz789",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        assert result.checksum == "xyz789"

    def test_has_subagent_metrics(self):
        """Should have subagent metrics."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor this code",
            tokens_in=5000,
            tokens_out=2500,
            subagent_time=25.3,
        )
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 5000
        assert result.tokens_out == 2500
        assert result.subagent_time == 25.3


class TestTddRefactorResultSerialization:
    """Test TddRefactorResult serialization methods."""

    def test_as_dict(self):
        """Should convert to dict with Path as string."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        result_dict = result.as_dict()
        assert result_dict["changed_files"] == ["src/auth.py"]
        assert result_dict["test_specifier"] == "tests/test_auth.py::test_login"
        assert result_dict["refactoring_type"] == "rename"

    def test_as_json(self):
        """Should convert to JSON string."""
        result = TddRefactorResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login",
            test_output="PASSED",
            refactoring_type="rename",
            checksum="abc123",
            subagent_type="claude-opus-4.5",
            subagent_prompt="refactor",
            tokens_in=1000,
            tokens_out=500,
            subagent_time=10.5,
        )
        json_str = result.as_json()
        assert "src/auth.py" in json_str
        assert "test_specifier" in json_str
        assert "rename" in json_str
