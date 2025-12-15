"""Commit for documentation step."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from jiro.commits.base import Commit, CommitResult
from jiro.steps.types import StepType, VerificationError

if TYPE_CHECKING:
    from jiro.results.base import Result
    from jiro.verifications.base import VerificationResult


class DocumentationCommit(Commit):
    """Commit class for documentation step.

    Handles:
    - Staging the documentation files
    - Creating a git commit with 📝 emoji
    """

    def create(
        self,
        *,
        result: Result,
        verification: VerificationResult,
        e2e_time: float,
    ) -> CommitResult:
        """Create a git commit for the documentation step.

        Args:
            result: The DocumentationResult from command execution
            verification: The VerificationResult from verification
            e2e_time: Total end-to-end time in seconds

        Returns:
            CommitResult with commit SHA and message

        Raises:
            VerificationError: If staging or committing fails
        """
        # Stage the changed files
        self._stage_files(result)

        # Create commit message
        doc_files = getattr(result, "doc_files_changed", 0)
        py_files = getattr(result, "py_files_changed", 0)

        if doc_files > 0 and py_files > 0:
            message = f"📝 Improve documentation ({doc_files} markdown, {py_files} code files)"
        elif doc_files > 0:
            message = f"📝 Improve documentation ({doc_files} markdown file{'s' if doc_files != 1 else ''})"
        else:
            message = (
                f"📝 Improve code documentation ({py_files} file{'s' if py_files != 1 else ''})"
            )

        # Create the commit
        try:
            commit_output = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True,
            )
            # Extract SHA from commit output
            sha = self._extract_sha(commit_output.stdout)
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.DOCUMENTATION,
                rule_violated="Git commit failed",
                expected="git commit to succeed",
                actual=f"git commit returned {e.returncode}",
                details=f"stderr: {e.stderr}",
            ) from e

        return CommitResult(
            sha=sha,
            message=message,
        )

    def _stage_files(self, result: Result) -> None:
        """Stage the changed files.

        Args:
            result: The result containing changed_files

        Raises:
            VerificationError: If staging fails
        """
        try:
            for file_path in result.changed_files:
                subprocess.run(
                    ["git", "add", str(file_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.DOCUMENTATION,
                rule_violated="Could not stage files",
                expected="git add to succeed",
                actual=f"git add returned {e.returncode}",
                details=f"stderr: {e.stderr}",
            ) from e

    @staticmethod
    def _extract_sha(output: str) -> str:
        """Extract commit SHA from git commit output.

        Git output format: "[branch abc123] message\n"

        Args:
            output: The stdout from git commit

        Returns:
            The commit SHA

        Raises:
            ValueError: If SHA cannot be extracted
        """
        # Look for pattern [branch_name hash_value]
        match = re.search(r"\[.*?\s+([a-f0-9]+)\s*\]", output)
        if match:
            return match.group(1)
        # Fallback: try to parse first word after [
        if "[" in output:
            start = output.index("[") + 1
            end = output.index("]") if "]" in output else start + 40
            content = output[start:end].strip()
            # Take the last word which should be the hash
            parts = content.split()
            if parts:
                return parts[-1]
        raise ValueError(f"Could not extract SHA from output: {output}")
