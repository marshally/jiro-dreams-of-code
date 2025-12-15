"""Tests for DocumentationResult dataclass."""

from pathlib import Path

from jiro.results.base import Result
from jiro.steps.documentation.documentation_result import DocumentationResult


class TestDocumentationResultIsResult:
    """Test that DocumentationResult is a proper Result subclass."""

    def test_is_result_subclass(self):
        """DocumentationResult should inherit from Result."""
        assert issubclass(DocumentationResult, Result)

    def test_can_instantiate(self):
        """Should be able to instantiate DocumentationResult."""
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.5,
        )
        assert isinstance(result, DocumentationResult)
        assert result.doc_files_changed == 1
        assert result.py_files_changed == 0


class TestDocumentationResultAttributes:
    """Test DocumentationResult attributes."""

    def test_has_changed_files(self):
        """Should have changed_files attribute."""
        result = DocumentationResult(
            changed_files=[Path("README.md"), Path("docs/guide.md")],
            doc_files_changed=2,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert len(result.changed_files) == 2
        assert Path("README.md") in result.changed_files

    def test_counts_doc_and_python_files(self):
        """Should track doc and python file changes separately."""
        result = DocumentationResult(
            changed_files=[
                Path("README.md"),
                Path("src/module.py"),
            ],
            doc_files_changed=1,
            py_files_changed=1,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.doc_files_changed == 1
        assert result.py_files_changed == 1

    def test_subagent_metrics(self):
        """Should track subagent metrics."""
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=2.5,
        )
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 2.5


class TestDocumentationResultSerialization:
    """Test serialization methods inherited from Result."""

    def test_as_dict(self):
        """Should convert to dictionary."""
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        d = result.as_dict()
        assert isinstance(d, dict)
        assert d["doc_files_changed"] == 1
        assert d["changed_files"] == ["README.md"]

    def test_as_json(self):
        """Should convert to JSON."""
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=1,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        json_str = result.as_json()
        assert isinstance(json_str, str)
        assert "doc_files_changed" in json_str
        assert "1" in json_str
