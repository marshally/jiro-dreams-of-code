"""Tests for TddRedResult dataclass."""

from dataclasses import is_dataclass
from pathlib import Path

from jiro.results.base import Result
from jiro.steps.tdd.red.tdd_red_result import TddRedResult


class TestTddRedResultIsDataclass:
    """Test that TddRedResult is a proper dataclass."""

    def test_is_dataclass(self):
        """TddRedResult should be a dataclass."""
        assert is_dataclass(TddRedResult)

    def test_inherits_from_result(self):
        """TddRedResult should inherit from Result."""
        assert issubclass(TddRedResult, Result)


class TestTddRedResultCreation:
    """Test creating TddRedResult instances."""

    def test_create_with_all_fields(self):
        """Should create TddRedResult with all fields."""
        result = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_login_validates_email",
            test_specifier="tests/test_auth.py::test_login_validates_email",
            test_output="FAILED - assert False\nExpected implementation",
            subagent_type="claude-opus-4.5",
            subagent_prompt="Create a failing test for email validation",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=15.5,
        )

        assert result.changed_files == [Path("tests/test_auth.py")]
        assert result.test_file == Path("tests/test_auth.py")
        assert result.test_name == "test_login_validates_email"
        assert result.test_specifier == "tests/test_auth.py::test_login_validates_email"
        assert result.test_output == "FAILED - assert False\nExpected implementation"
        assert result.subagent_type == "claude-opus-4.5"
        assert result.subagent_prompt == "Create a failing test for email validation"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 15.5

    def test_multiple_test_files(self):
        """Should support multiple test files in changed_files."""
        result = TddRedResult(
            changed_files=[
                Path("tests/test_auth.py"),
                Path("tests/test_login.py"),
            ],
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

        assert len(result.changed_files) == 2


class TestTddRedResultSerialization:
    """Test serialization methods."""

    def test_as_dict(self):
        """Should convert to dictionary with Path as strings."""
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

        data = result.as_dict()

        assert isinstance(data, dict)
        assert "changed_files" in data
        assert "test_file" in data
        assert "test_name" in data
        # Check that paths are strings
        assert isinstance(data["changed_files"][0], str)
        assert isinstance(data["test_file"], str)

    def test_as_json(self):
        """Should serialize to JSON string."""
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

        json_str = result.as_json()

        assert isinstance(json_str, str)
        assert "test_name" in json_str
        assert "test_example" in json_str
        assert "test_auth.py" in json_str

    def test_as_toon(self):
        """Should serialize to TOON format."""
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

        toon_str = result.as_toon()

        assert isinstance(toon_str, str)
        assert ";" in toon_str  # TOON uses semicolons
        assert "test_name=test_example" in toon_str


class TestTddRedResultEquality:
    """Test equality comparisons."""

    def test_equal_results(self):
        """Should be equal with same values."""
        result1 = TddRedResult(
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

        result2 = TddRedResult(
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

        assert result1 == result2

    def test_different_test_name(self):
        """Should not be equal with different test names."""
        result1 = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example1",
            test_specifier="tests/test_auth.py::test_example1",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        result2 = TddRedResult(
            changed_files=[Path("tests/test_auth.py")],
            test_file=Path("tests/test_auth.py"),
            test_name="test_example2",
            test_specifier="tests/test_auth.py::test_example2",
            test_output="FAILED",
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert result1 != result2
