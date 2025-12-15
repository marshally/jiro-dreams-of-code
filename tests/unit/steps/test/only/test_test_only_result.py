"""Tests for TestOnlyResult dataclass."""

from dataclasses import is_dataclass
from pathlib import Path

from jiro.results.base import Result
from jiro.steps.test.only.test_only_result import TestOnlyResult


class TestTestOnlyResultIsDataclass:
    """Test that TestOnlyResult is a proper dataclass."""

    def test_is_dataclass(self):
        """TestOnlyResult should be a dataclass."""
        assert is_dataclass(TestOnlyResult)

    def test_inherits_from_result(self):
        """TestOnlyResult should inherit from Result."""
        assert issubclass(TestOnlyResult, Result)


class TestTestOnlyResultCreation:
    """Test creating TestOnlyResult instances."""

    def test_create_with_all_fields(self):
        """Should create TestOnlyResult with all fields."""
        result = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_new_validation",
            test_output="PASSED - 1 passed in 0.15s",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude-opus-4.5",
            subagent_prompt="Add test for email validation",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=15.5,
        )

        assert result.changed_files == [Path("tests/test_auth.py")]
        assert result.test_specifier == "tests/test_auth.py::test_new_validation"
        assert result.test_output == "PASSED - 1 passed in 0.15s"
        assert result.test_files == [Path("tests/test_auth.py")]
        assert result.subagent_type == "claude-opus-4.5"
        assert result.subagent_prompt == "Add test for email validation"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 15.5

    def test_single_test_file(self):
        """Should support single test file in changed_files."""
        result = TestOnlyResult(
            changed_files=[Path("tests/test_utils.py")],
            test_specifier="tests/test_utils.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_utils.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert len(result.changed_files) == 1
        assert len(result.test_files) == 1


class TestTestOnlyResultSerialization:
    """Test serialization methods."""

    def test_as_dict(self):
        """Should convert to dictionary with Path as strings."""
        result = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        data = result.as_dict()

        assert isinstance(data, dict)
        assert "changed_files" in data
        assert "test_specifier" in data
        assert "test_files" in data
        # Check that paths are strings
        assert isinstance(data["changed_files"][0], str)
        assert isinstance(data["test_files"][0], str)

    def test_as_json(self):
        """Should serialize to JSON string."""
        result = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        json_str = result.as_json()

        assert isinstance(json_str, str)
        assert "test_specifier" in json_str
        assert "test_example" in json_str
        assert "test_auth.py" in json_str

    def test_as_toon(self):
        """Should serialize to TOON format."""
        result = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        toon_str = result.as_toon()

        assert isinstance(toon_str, str)
        assert ";" in toon_str  # TOON uses semicolons
        assert "test_specifier=tests/test_auth.py::test_example" in toon_str


class TestTestOnlyResultEquality:
    """Test equality comparisons."""

    def test_equal_results(self):
        """Should be equal with same values."""
        result1 = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        result2 = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert result1 == result2

    def test_different_test_specifier(self):
        """Should not be equal with different test specifiers."""
        result1 = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example1",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        result2 = TestOnlyResult(
            changed_files=[Path("tests/test_auth.py")],
            test_specifier="tests/test_auth.py::test_example2",
            test_output="PASSED",
            test_files=[Path("tests/test_auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert result1 != result2
