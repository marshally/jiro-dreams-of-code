"""Tests for Result base dataclass."""

import json
from dataclasses import is_dataclass
from pathlib import Path

from jiro.results.base import Result


class TestResultDataclass:
    """Tests for Result dataclass basics."""

    def test_result_is_dataclass(self):
        """Result should be a dataclass."""
        assert is_dataclass(Result)

    def test_result_has_changed_files_field(self):
        """Result should have changed_files field."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert result.changed_files == [Path("src/foo.py")]

    def test_result_accepts_empty_changed_files(self):
        """Result should accept empty changed_files list."""
        result = Result(changed_files=[])
        assert result.changed_files == []

    def test_result_accepts_multiple_files(self):
        """Result should accept multiple files."""
        files = [Path("src/foo.py"), Path("src/bar.py"), Path("tests/test_foo.py")]
        result = Result(changed_files=files)
        assert result.changed_files == files


class TestResultAsDict:
    """Tests for Result.as_dict() method."""

    def test_as_dict_returns_dict(self):
        """as_dict() should return a dictionary."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert isinstance(result.as_dict(), dict)

    def test_as_dict_contains_changed_files(self):
        """as_dict() should contain changed_files key."""
        result = Result(changed_files=[Path("src/foo.py")])
        d = result.as_dict()
        assert "changed_files" in d

    def test_as_dict_paths_are_strings(self):
        """as_dict() should convert Path objects to strings."""
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        d = result.as_dict()
        assert d["changed_files"] == ["src/foo.py", "src/bar.py"]


class TestResultAsJson:
    """Tests for Result.as_json() method."""

    def test_as_json_returns_string(self):
        """as_json() should return a JSON string."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert isinstance(result.as_json(), str)

    def test_as_json_is_valid_json(self):
        """as_json() should return valid JSON."""
        result = Result(changed_files=[Path("src/foo.py")])
        parsed = json.loads(result.as_json())
        assert parsed["changed_files"] == ["src/foo.py"]

    def test_as_json_handles_empty_list(self):
        """as_json() should handle empty changed_files."""
        result = Result(changed_files=[])
        parsed = json.loads(result.as_json())
        assert parsed["changed_files"] == []


class TestResultAsToon:
    """Tests for Result.as_toon() method (TOON format for LLM efficiency)."""

    def test_as_toon_returns_string(self):
        """as_toon() should return a string."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert isinstance(result.as_toon(), str)

    def test_as_toon_contains_changed_files(self):
        """as_toon() should include changed files info."""
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        toon = result.as_toon()
        assert "src/foo.py" in toon
        assert "src/bar.py" in toon

    def test_as_toon_is_compact(self):
        """as_toon() should be more compact than JSON."""
        result = Result(changed_files=[Path("src/foo.py")])
        # TOON should not have JSON's verbose formatting
        toon = result.as_toon()
        assert '"' not in toon or toon.count('"') < result.as_json().count('"')


class TestResultAsHtml:
    """Tests for Result.as_html() method."""

    def test_as_html_returns_string(self):
        """as_html() should return a string."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert isinstance(result.as_html(), str)

    def test_as_html_contains_html_tags(self):
        """as_html() should contain HTML formatting."""
        result = Result(changed_files=[Path("src/foo.py")])
        html = result.as_html()
        assert "<" in html and ">" in html

    def test_as_html_includes_files(self):
        """as_html() should include file paths."""
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        html = result.as_html()
        assert "src/foo.py" in html
        assert "src/bar.py" in html


class TestResultStr:
    """Tests for Result.__str__() method."""

    def test_str_returns_string(self):
        """__str__() should return a string."""
        result = Result(changed_files=[Path("src/foo.py")])
        assert isinstance(str(result), str)

    def test_str_includes_changed_files(self):
        """__str__() should include changed files."""
        result = Result(changed_files=[Path("src/foo.py")])
        s = str(result)
        assert "src/foo.py" in s

    def test_str_is_human_readable(self):
        """__str__() should be human readable."""
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        s = str(result)
        # Should contain both files in some readable format
        assert "foo.py" in s
        assert "bar.py" in s


class TestResultInheritance:
    """Tests for Result as a base class for inheritance."""

    def test_result_can_be_subclassed(self):
        """Result should support subclassing."""
        from dataclasses import dataclass

        @dataclass
        class TddRedResult(Result):
            test_name: str

        result = TddRedResult(changed_files=[Path("tests/test_foo.py")], test_name="test_login")
        assert result.changed_files == [Path("tests/test_foo.py")]
        assert result.test_name == "test_login"

    def test_subclass_inherits_serialization(self):
        """Subclasses should inherit serialization methods."""
        from dataclasses import dataclass

        @dataclass
        class TddRedResult(Result):
            test_name: str

        result = TddRedResult(changed_files=[Path("tests/test_foo.py")], test_name="test_login")
        d = result.as_dict()
        assert "changed_files" in d
        assert "test_name" in d
        assert d["test_name"] == "test_login"
