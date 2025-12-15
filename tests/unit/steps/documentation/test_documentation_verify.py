"""Tests for DocumentationVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.documentation.documentation_result import DocumentationResult
from jiro.steps.documentation.documentation_verify import (
    DocumentationVerify,
    LineClassification,
)
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification


class TestDocumentationVerifyIsVerification:
    """Test that DocumentationVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """DocumentationVerify should inherit from Verification."""
        assert issubclass(DocumentationVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate DocumentationVerify."""
        verify = DocumentationVerify()
        assert isinstance(verify, DocumentationVerify)


class TestLineClassification:
    """Test the LineClassification enum."""

    def test_has_all_classifications(self):
        """Should have all required classifications."""
        assert LineClassification.COMMENT.value == "comment"
        assert LineClassification.DOCSTRING.value == "docstring"
        assert LineClassification.WHITESPACE.value == "whitespace"
        assert LineClassification.CODE.value == "code"


class TestDocumentationVerifyClassifyLine:
    """Test the _classify_line method."""

    def test_classify_whitespace(self):
        """Should classify empty lines as WHITESPACE."""
        verify = DocumentationVerify()
        assert verify._classify_line("") == LineClassification.WHITESPACE
        assert verify._classify_line("   ") == LineClassification.WHITESPACE
        assert verify._classify_line("\t") == LineClassification.WHITESPACE

    def test_classify_comment(self):
        """Should classify lines starting with # as COMMENT."""
        verify = DocumentationVerify()
        assert verify._classify_line("# This is a comment") == LineClassification.COMMENT
        assert verify._classify_line("    # Indented comment") == LineClassification.COMMENT
        assert verify._classify_line("#") == LineClassification.COMMENT

    def test_classify_docstring_double_quotes(self):
        """Should classify lines with triple quotes as DOCSTRING."""
        verify = DocumentationVerify()
        assert verify._classify_line('"""This is a docstring"""') == LineClassification.DOCSTRING
        assert (
            verify._classify_line('"""Multi-line docstring start') == LineClassification.DOCSTRING
        )
        assert verify._classify_line('"""') == LineClassification.DOCSTRING

    def test_classify_docstring_single_quotes(self):
        """Should classify lines with triple single quotes as DOCSTRING."""
        verify = DocumentationVerify()
        assert verify._classify_line("'''This is a docstring'''") == LineClassification.DOCSTRING
        assert (
            verify._classify_line("'''Multi-line docstring start") == LineClassification.DOCSTRING
        )

    def test_classify_code(self):
        """Should classify everything else as CODE."""
        verify = DocumentationVerify()
        assert verify._classify_line("x = 5") == LineClassification.CODE
        assert verify._classify_line("def foo():") == LineClassification.CODE
        assert verify._classify_line("return None") == LineClassification.CODE
        assert verify._classify_line('print("hello")') == LineClassification.CODE

    def test_classify_code_with_hash_in_string(self):
        """Should classify f-strings with # as CODE (not COMMENT)."""
        verify = DocumentationVerify()
        # # inside a string is not a comment
        assert verify._classify_line('msg = "value is #5"') == LineClassification.CODE


class TestDocumentationVerifyClassifyLinesWithState:
    """Test the _classify_lines_with_state method with docstring tracking."""

    def test_single_line_docstring(self):
        """Should handle single-line docstrings."""
        verify = DocumentationVerify()
        lines = ['"""Single line docstring"""']
        result = verify._classify_lines_with_state(lines)
        assert result == [LineClassification.DOCSTRING]

    def test_multiline_docstring(self):
        """Should track docstring state across multiple lines."""
        verify = DocumentationVerify()
        lines = [
            '"""Start of docstring',
            "This is inside the docstring",
            '"""',
        ]
        result = verify._classify_lines_with_state(lines)
        assert result == [
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,
        ]

    def test_code_before_and_after_docstring(self):
        """Should correctly classify code before and after docstrings."""
        verify = DocumentationVerify()
        lines = [
            "def foo():",
            '    """Docstring"""',
            "    x = 5",
        ]
        result = verify._classify_lines_with_state(lines)
        assert result == [
            LineClassification.CODE,
            LineClassification.DOCSTRING,
            LineClassification.CODE,
        ]

    def test_comment_before_docstring(self):
        """Should correctly classify comments and docstrings."""
        verify = DocumentationVerify()
        lines = [
            "# This is a comment",
            '"""This is a docstring"""',
            "x = 5",
        ]
        result = verify._classify_lines_with_state(lines)
        assert result == [
            LineClassification.COMMENT,
            LineClassification.DOCSTRING,
            LineClassification.CODE,
        ]

    def test_empty_lines_in_docstring(self):
        """Should classify empty lines inside docstrings as DOCSTRING."""
        verify = DocumentationVerify()
        lines = [
            '"""Start',
            "",
            "Content",
            '"""',
        ]
        result = verify._classify_lines_with_state(lines)
        assert result == [
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,  # Empty inside docstring is DOCSTRING
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,
        ]

    def test_single_quotes_docstring(self):
        """Should handle single-quote docstrings."""
        verify = DocumentationVerify()
        lines = [
            "'''Start",
            "Content",
            "'''",
        ]
        result = verify._classify_lines_with_state(lines)
        assert result == [
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,
            LineClassification.DOCSTRING,
        ]


class TestDocumentationVerifyParseDiff:
    """Test the _parse_diff method."""

    def test_parse_added_lines(self):
        """Should extract added lines from diff."""
        verify = DocumentationVerify()
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+# New comment
 existing line
"""
        lines = verify._parse_diff(diff)
        assert "# New comment" in lines

    def test_parse_removed_lines(self):
        """Should extract removed lines from diff."""
        verify = DocumentationVerify()
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,2 @@
 existing line
-# Old comment
"""
        lines = verify._parse_diff(diff)
        assert "# Old comment" in lines

    def test_skip_diff_headers(self):
        """Should skip diff headers."""
        verify = DocumentationVerify()
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+# Comment
"""
        lines = verify._parse_diff(diff)
        assert "---" not in lines
        assert "+++" not in lines
        assert "@@" not in lines

    def test_parse_empty_diff(self):
        """Should handle empty diff."""
        verify = DocumentationVerify()
        lines = verify._parse_diff("")
        assert lines == []


class TestDocumentationVerifyMarkdownFile:
    """Test that .md files are always valid documentation."""

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_markdown_files_always_valid(self, mock_run):
        """Markdown files should always be accepted as documentation."""
        # Setup mock for git diff --name-only
        mock_result = MagicMock()
        mock_result.stdout = "README.md\nDOC.md"
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
        result = DocumentationResult(
            changed_files=[Path("README.md"), Path("DOC.md")],
            doc_files_changed=2,
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        # Should not raise
        verify._verify_git_diff_matches(result, ["README.md", "DOC.md"])


class TestDocumentationVerifyPythonFile:
    """Test documentation-only change verification for Python files."""

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_python_file_with_comment_changes(self, mock_run):
        """Should accept Python files with only comment changes."""
        # Setup mock for git diff
        mock_result = MagicMock()
        mock_result.stdout = """--- a/module.py
+++ b/module.py
@@ -1,3 +1,4 @@
+# New comment explaining the function
 def foo():
"""
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
        # Should not raise
        verify._verify_python_file_is_doc_only("module.py")

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_python_file_with_docstring_changes(self, mock_run):
        """Should accept Python files with only docstring changes."""
        mock_result = MagicMock()
        mock_result.stdout = """--- a/module.py
+++ b/module.py
@@ -1,3 +1,4 @@
 def foo():
+    '''New docstring'''
"""
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
        # Should not raise
        verify._verify_python_file_is_doc_only("module.py")

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_python_file_with_code_changes_fails(self, mock_run):
        """Should reject Python files with code changes."""
        mock_result = MagicMock()
        mock_result.stdout = """--- a/module.py
+++ b/module.py
@@ -1,3 +1,4 @@
+x = 5
 def foo():
"""
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
        with pytest.raises(VerificationError, match="Code line found"):
            verify._verify_python_file_is_doc_only("module.py")


class TestDocumentationVerifyIntegration:
    """Integration tests for the full verify method."""

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_verify_markdown_only_changes(self, mock_run):
        """Should verify markdown-only documentation changes."""
        # Setup mock for git diff --name-only
        mock_result = MagicMock()
        mock_result.stdout = "README.md"
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
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

        verification = verify.verify(result=result)
        assert verification.success is True
        assert "1" in verification.verification_output

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_verify_python_doc_changes(self, mock_run):
        """Should verify Python docstring/comment changes."""
        # First call: git diff --name-only
        # Second call: git diff --unified=0 for the .py file
        call_results = [
            MagicMock(stdout="module.py"),  # git diff --name-only
            MagicMock(
                stdout="""--- a/module.py
+++ b/module.py
@@ -1,3 +1,4 @@
+# Comment
 def foo():
"""
            ),  # git diff --unified=0 module.py
        ]
        mock_run.side_effect = call_results

        verify = DocumentationVerify()
        result = DocumentationResult(
            changed_files=[Path("module.py")],
            doc_files_changed=0,
            py_files_changed=1,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification = verify.verify(result=result)
        assert verification.success is True

    @patch("jiro.steps.documentation.documentation_verify.subprocess.run")
    def test_verify_mismatched_file_counts(self, mock_run):
        """Should fail if reported file counts don't match actual."""
        mock_result = MagicMock()
        mock_result.stdout = "README.md"
        mock_run.return_value = mock_result

        verify = DocumentationVerify()
        result = DocumentationResult(
            changed_files=[Path("README.md")],
            doc_files_changed=2,  # Wrong count!
            py_files_changed=0,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError, match="count mismatch"):
            verify.verify(result=result)
