"""Tests for BugGreenResult dataclass."""

from dataclasses import is_dataclass
from pathlib import Path

from jiro.results.base import Result
from jiro.steps.bug.green.bug_green_result import BugGreenResult


class TestBugGreenResultIsDataclass:
    """Test that BugGreenResult is a proper dataclass."""

    def test_is_dataclass(self):
        """BugGreenResult should be a dataclass."""
        assert is_dataclass(BugGreenResult)

    def test_inherits_from_result(self):
        """BugGreenResult should inherit from Result."""
        assert issubclass(BugGreenResult, Result)


class TestBugGreenResultCreation:
    """Test creating BugGreenResult instances."""

    def test_create_with_all_fields(self):
        """Should create BugGreenResult with all fields."""
        result = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_login_handles_empty_password",
            test_output="PASSED - 1 passed in 0.15s",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude-opus-4.5",
            subagent_prompt="Fix password validation in login function",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=15.5,
        )

        assert result.changed_files == [Path("src/auth.py")]
        assert result.test_specifier == "tests/test_auth.py::test_login_handles_empty_password"
        assert result.test_output == "PASSED - 1 passed in 0.15s"
        assert result.implementation_files == [Path("src/auth.py")]
        assert result.subagent_type == "claude-opus-4.5"
        assert result.subagent_prompt == "Fix password validation in login function"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 15.5

    def test_multiple_implementation_files(self):
        """Should support multiple implementation files in changed_files."""
        result = BugGreenResult(
            changed_files=[
                Path("src/auth.py"),
                Path("src/models/user.py"),
            ],
            test_specifier="tests/test_auth.py::test_example",
            test_output="PASSED",
            implementation_files=[
                Path("src/auth.py"),
                Path("src/models/user.py"),
            ],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert len(result.changed_files) == 2
        assert len(result.implementation_files) == 2


class TestBugGreenResultSerialization:
    """Test serialization methods."""

    def test_as_dict(self):
        """Should convert to dictionary with Path as strings."""
        result = BugGreenResult(
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

        data = result.as_dict()

        assert isinstance(data, dict)
        assert "changed_files" in data
        assert "test_specifier" in data
        assert "implementation_files" in data
        # Check that paths are strings
        assert isinstance(data["changed_files"][0], str)
        assert isinstance(data["implementation_files"][0], str)

    def test_as_json(self):
        """Should serialize to JSON string."""
        result = BugGreenResult(
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

        json_str = result.as_json()

        assert isinstance(json_str, str)
        assert "test_specifier" in json_str
        assert "test_example" in json_str
        assert "auth.py" in json_str

    def test_as_toon(self):
        """Should serialize to TOON format."""
        result = BugGreenResult(
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

        toon_str = result.as_toon()

        assert isinstance(toon_str, str)
        assert ";" in toon_str  # TOON uses semicolons
        assert "test_specifier=tests/test_auth.py::test_example" in toon_str


class TestBugGreenResultEquality:
    """Test equality comparisons."""

    def test_equal_results(self):
        """Should be equal with same values."""
        result1 = BugGreenResult(
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

        result2 = BugGreenResult(
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

        assert result1 == result2

    def test_different_test_specifier(self):
        """Should not be equal with different test specifiers."""
        result1 = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example1",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        result2 = BugGreenResult(
            changed_files=[Path("src/auth.py")],
            test_specifier="tests/test_auth.py::test_example2",
            test_output="PASSED",
            implementation_files=[Path("src/auth.py")],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        assert result1 != result2
