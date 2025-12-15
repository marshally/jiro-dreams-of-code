"""Verification for documentation step.

Verifies that the documentation step result meets the verification rules:
- Only .md files changed, OR
- Only docstring/comment changes in .py files (no code changes)

Uses the documentation change detection algorithm from STRONGLY_TYPED_COMMITS.md:
1. Run git diff --unified=0 to get only changed lines (no context)
2. For each changed file:
   a. If file is .md -> always valid documentation change
   b. If file is .py -> analyze changed lines using algorithm below
3. For Python files, classify each added/removed line:
   - COMMENT: line stripped starts with hash
   - DOCSTRING: line is inside triple-quoted string
   - WHITESPACE: line is empty or whitespace-only
   - CODE: anything else
4. For docstring detection:
   - Track state: inside_docstring = False
   - On line containing triple quotes:
     - If line has opening and closing quotes -> single-line docstring
     - Otherwise toggle inside_docstring state
   - Lines while inside_docstring = True are DOCSTRING
5. Verification:
   - PASSES if ALL changed lines are COMMENT, DOCSTRING, or WHITESPACE
   - FAILS if ANY changed line is CODE
"""

from __future__ import annotations

import subprocess
import time
from enum import Enum
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


class LineClassification(Enum):
    """Classification of a line in documentation verification."""

    COMMENT = "comment"
    DOCSTRING = "docstring"
    WHITESPACE = "whitespace"
    CODE = "code"


class DocumentationVerify(Verification):
    """Verification for documentation step.

    Validates that:
    1. Only .md files changed, OR
    2. Only documentation-related changes in .py files (no code changes)

    Uses the documentation change detection algorithm to classify each changed line
    in Python files and ensure they are only comments, docstrings, or whitespace.
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the documentation step result.

        Args:
            result: The DocumentationResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Get changed files from git
            changed_files = self._get_git_changed_files()

            # Verify changed files match result
            self._verify_git_diff_matches(result, changed_files)

            # Analyze each changed file
            doc_files_count = 0
            py_files_count = 0

            for file_path in changed_files:
                if file_path.endswith(".md"):
                    # Markdown files are always valid documentation
                    doc_files_count += 1
                elif file_path.endswith(".py"):
                    # Python files need line-by-line analysis
                    self._verify_python_file_is_doc_only(file_path)
                    py_files_count += 1
                else:
                    # Non-code, non-markdown files are rejected
                    raise VerificationError(
                        step_type=StepType.DOCUMENTATION,
                        rule_violated="Only .md and .py files allowed",
                        expected="Changed files to be .md or .py",
                        actual=f"Found file: {file_path}",
                        details=f"Unexpected file type: {file_path}",
                    )

            # Verify result counts match actual files
            if hasattr(result, "doc_files_changed") and result.doc_files_changed != doc_files_count:
                raise VerificationError(
                    step_type=StepType.DOCUMENTATION,
                    rule_violated="Documentation file count mismatch",
                    expected=f"doc_files_changed={doc_files_count}",
                    actual=f"doc_files_changed={result.doc_files_changed}",
                    details=f"Result reported {result.doc_files_changed} doc files but found {doc_files_count}",
                )

            if hasattr(result, "py_files_changed") and result.py_files_changed != py_files_count:
                raise VerificationError(
                    step_type=StepType.DOCUMENTATION,
                    rule_violated="Python file count mismatch",
                    expected=f"py_files_changed={py_files_count}",
                    actual=f"py_files_changed={result.py_files_changed}",
                    details=f"Result reported {result.py_files_changed} py files but found {py_files_count}",
                )

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="git diff --unified=0 + line classification",
                verification_output=f"Documentation changes verified: {doc_files_count} .md files, {py_files_count} .py files with doc-only changes",
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _get_git_changed_files(self) -> list[str]:
        """Get list of changed files from git diff.

        Returns:
            List of file paths that have changed

        Raises:
            VerificationError: If git diff fails
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_changes = output.stdout.strip().split("\n") if output.stdout.strip() else []
            return git_changes
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.DOCUMENTATION,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

    def _verify_git_diff_matches(self, result: Result, changed_files: list[str]) -> None:
        """Verify git diff matches result.changed_files.

        Args:
            result: The DocumentationResult
            changed_files: List of files from git diff

        Raises:
            VerificationError: If git diff doesn't match changed_files
        """
        result_files = {str(f) for f in result.changed_files}
        git_changes = set(changed_files)

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.DOCUMENTATION,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_python_file_is_doc_only(self, file_path: str) -> None:
        """Verify a Python file contains only documentation changes.

        Uses the documentation change detection algorithm to classify each changed
        line and ensure they are only comments, docstrings, or whitespace.

        Args:
            file_path: Path to the Python file

        Raises:
            VerificationError: If any changed line is CODE
        """
        # Get the diff for this file
        try:
            output = subprocess.run(
                ["git", "diff", "--unified=0", file_path],
                capture_output=True,
                text=True,
                check=True,
            )
            diff_output = output.stdout
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.DOCUMENTATION,
                rule_violated="Could not run git diff for file",
                expected=f"git diff to succeed for {file_path}",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Parse diff and get changed lines
        changed_lines = self._parse_diff(diff_output)

        # Classify each changed line
        for line in changed_lines:
            classification = self._classify_line(line)
            if classification == LineClassification.CODE:
                raise VerificationError(
                    step_type=StepType.DOCUMENTATION,
                    rule_violated="Code line found in documentation-only change",
                    expected="Only comments, docstrings, and whitespace",
                    actual=f"Found CODE line: {line}",
                    details=f"File {file_path} contains code changes, not just documentation",
                )

    def _parse_diff(self, diff_output: str) -> list[str]:
        """Parse git diff output and extract changed lines.

        Extracts lines that were added (+) or removed (-), excluding diff headers.

        Args:
            diff_output: Output from git diff --unified=0

        Returns:
            List of changed lines (without the +/- prefix)
        """
        lines = []
        for line in diff_output.split("\n"):
            # Skip diff headers and context
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            # Include added and removed lines
            if line.startswith("+") or line.startswith("-"):
                # Remove the +/- prefix and include the line
                lines.append(line[1:])
        return lines

    def _classify_line(self, line: str) -> LineClassification:
        """Classify a line as COMMENT, DOCSTRING, WHITESPACE, or CODE.

        Implements the documentation change detection algorithm.

        Args:
            line: The line to classify

        Returns:
            LineClassification enum value

        Note:
            This is a simple single-line classifier. For accurate docstring detection
            across multiple lines, use _classify_line_with_state() instead.
            This version provides a best-effort classification for individual lines.
        """
        stripped = line.strip()

        # WHITESPACE: empty or whitespace-only
        if not stripped:
            return LineClassification.WHITESPACE

        # COMMENT: starts with #
        if stripped.startswith("#"):
            return LineClassification.COMMENT

        # DOCSTRING: contains """ or '''
        if '"""' in stripped or "'''" in stripped:
            return LineClassification.DOCSTRING

        # CODE: anything else
        return LineClassification.CODE

    def _classify_lines_with_state(self, lines: list[str]) -> list[LineClassification]:
        """Classify multiple lines with state tracking for docstrings.

        Accurately detects docstrings by tracking whether we're inside a
        triple-quoted string. This is more accurate than single-line classification.

        Args:
            lines: List of lines to classify

        Returns:
            List of LineClassification values corresponding to input lines
        """
        classifications: list[LineClassification] = []
        inside_docstring = False
        docstring_delimiter = None  # Track which delimiter we're inside

        for line in lines:
            stripped = line.strip()

            # If we're inside a docstring, check for closing delimiter first
            if inside_docstring:
                if '"""' in stripped or "'''" in stripped:
                    delimiter = '"""' if '"""' in stripped else "'''"
                    if delimiter == docstring_delimiter:
                        # Closing the docstring
                        classifications.append(LineClassification.DOCSTRING)
                        inside_docstring = False
                        docstring_delimiter = None
                        continue
                # Inside docstring but no closing delimiter - could be empty line or content
                if not stripped:
                    # Empty lines inside docstring are still DOCSTRING
                    classifications.append(LineClassification.DOCSTRING)
                else:
                    classifications.append(LineClassification.DOCSTRING)
                continue

            # WHITESPACE: empty or whitespace-only (outside docstring)
            if not stripped:
                classifications.append(LineClassification.WHITESPACE)
                continue

            # COMMENT: starts with # (outside docstring)
            if stripped.startswith("#"):
                classifications.append(LineClassification.COMMENT)
                continue

            # Handle docstring delimiters (opening or single-line)
            if '"""' in stripped or "'''" in stripped:
                delimiter = '"""' if '"""' in stripped else "'''"
                count = stripped.count(delimiter)
                if count >= 2:
                    # Single-line docstring
                    classifications.append(LineClassification.DOCSTRING)
                else:
                    # Opening a multi-line docstring
                    classifications.append(LineClassification.DOCSTRING)
                    inside_docstring = True
                    docstring_delimiter = delimiter
                continue

            # CODE: anything else
            classifications.append(LineClassification.CODE)

        return classifications
