"""Tests for LintFixResult dataclass."""

from dataclasses import is_dataclass
from pathlib import Path

from jiro.results.base import Result
from jiro.steps.lint.fix.lint_fix_result import LintFixResult


class TestLintFixResultIsDataclass:
    """Test that LintFixResult is a proper dataclass."""

    def test_is_dataclass(self):
        """LintFixResult should be a dataclass."""
        assert is_dataclass(LintFixResult)

    def test_inherits_from_result(self):
        """LintFixResult should inherit from Result."""
        assert issubclass(LintFixResult, Result)


class TestLintFixResultCreation:
    """Test creating LintFixResult instances."""

    def test_create_with_all_fields(self):
        """Should create LintFixResult with all fields."""
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        assert result.changed_files == [Path("src/example.py")]
        assert result.error_code == "E501"
        assert result.filename == "src/example.py"

    def test_single_file_changed(self):
        """Should have exactly one file in changed_files."""
        result = LintFixResult(
            changed_files=[Path("src/utils.py")],
            error_code="W503",
            filename="src/utils.py",
        )

        assert len(result.changed_files) == 1
        assert result.changed_files[0] == Path("src/utils.py")


class TestLintFixResultSerialization:
    """Test serialization methods."""

    def test_as_dict(self):
        """Should convert to dictionary with Path as strings."""
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        data = result.as_dict()

        assert isinstance(data, dict)
        assert "changed_files" in data
        assert "error_code" in data
        assert "filename" in data
        # Check that paths are strings
        assert isinstance(data["changed_files"][0], str)

    def test_as_json(self):
        """Should serialize to JSON string."""
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        json_str = result.as_json()

        assert isinstance(json_str, str)
        assert "error_code" in json_str
        assert "E501" in json_str
        assert "example.py" in json_str

    def test_as_toon(self):
        """Should serialize to TOON format."""
        result = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        toon_str = result.as_toon()

        assert isinstance(toon_str, str)
        assert ";" in toon_str  # TOON uses semicolons
        assert "error_code=E501" in toon_str


class TestLintFixResultEquality:
    """Test equality comparisons."""

    def test_equal_results(self):
        """Should be equal with same values."""
        result1 = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        result2 = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        assert result1 == result2

    def test_different_error_code(self):
        """Should not be equal with different error codes."""
        result1 = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        result2 = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="W503",
            filename="src/example.py",
        )

        assert result1 != result2

    def test_different_filename(self):
        """Should not be equal with different filenames."""
        result1 = LintFixResult(
            changed_files=[Path("src/example.py")],
            error_code="E501",
            filename="src/example.py",
        )

        result2 = LintFixResult(
            changed_files=[Path("src/other.py")],
            error_code="E501",
            filename="src/other.py",
        )

        assert result1 != result2
