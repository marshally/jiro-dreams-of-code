"""Commit for config step."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from jiro.commits.base import Commit, CommitResult
from jiro.steps.types import StepType, VerificationError

if TYPE_CHECKING:
    from jiro.results.base import Result
    from jiro.verifications.base import VerificationResult


class ConfigCommit(Commit):
    """Commit class for config step.

    Handles:
    - Staging the config files
    - Creating a git commit with ⚙️ emoji
    """

    def create(
        self,
        *,
        result: Result,
        verification: VerificationResult,
        e2e_time: float,
    ) -> CommitResult:
        """Create a git commit for the config step.

        Args:
            result: The ConfigResult from command execution
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
        config_files = getattr(result, "config_files_changed", 0)
        config_types = getattr(result, "config_types", [])

        # Format config types
        if config_types:
            types_str = ", ".join(sorted(set(config_types)))
            message = f"⚙️ Update configuration ({config_files} file{'s' if config_files != 1 else ''}: {types_str})"
        else:
            message = (
                f"⚙️ Update configuration ({config_files} file{'s' if config_files != 1 else ''})"
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
                step_type=StepType.CONFIG,
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
                step_type=StepType.CONFIG,
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
