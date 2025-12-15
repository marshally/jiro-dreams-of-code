"""Verification for lint fix step.

Verifies that the lint fix step result meets the verification rules:
- Only one file in changed_files
- git diff --name-only matches exactly changed_files
- Lint passes on the file
"""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


class LintFixVerify(Verification):
    """Verification for lint fix step.

    Validates that:
    1. Only one file is in changed_files
    2. git diff --name-only matches exactly changed_files
    3. Lint passes on the fixed file
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the lint fix step result.

        Args:
            result: The LintFixResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Rule 1: Only one file in changed_files
            self._verify_single_file_changed(result)

            # Rule 2: git diff matches changed_files
            self._verify_git_diff_matches(result)

            # Rule 3: Lint passes on the file
            lint_output = self._verify_lint_passes(result)

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="python -m flake8 <file>",
                verification_output=lint_output,
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _verify_single_file_changed(self, result: Result) -> None:
        """Verify that only one file is in changed_files.

        Args:
            result: The LintFixResult

        Raises:
            VerificationError: If more than one file is changed
        """
        if len(result.changed_files) != 1:
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="Single file required",
                expected="len(changed_files) == 1",
                actual=f"len(changed_files) == {len(result.changed_files)}",
                details=f"Files: {[str(f) for f in result.changed_files]}",
            )

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The LintFixResult

        Raises:
            VerificationError: If git diff doesn't match changed_files
        """
        # Get unstaged changes from git
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_changes = set(output.stdout.strip().split("\n")) if output.stdout.strip() else set()
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_lint_passes(self, result: Result) -> str:
        """Verify that lint passes on the fixed file.

        Args:
            result: The LintFixResult

        Returns:
            The lint output

        Raises:
            VerificationError: If lint fails on the file
        """
        filename = getattr(result, "filename", None)
        if not filename:
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="Missing filename",
                expected="result.filename to be set",
                actual="filename is None or empty",
                details="Cannot verify lint without filename",
            )

        # Run flake8 to verify lint passes
        try:
            result_proc = subprocess.run(
                ["python", "-m", "flake8", filename],
                capture_output=True,
                text=True,
            )
            output = result_proc.stdout + result_proc.stderr

            # If flake8 failed (exit code non-zero), lint didn't pass
            if result_proc.returncode != 0:
                raise VerificationError(
                    step_type=StepType.LINT_FIX,
                    rule_violated="Lint does not pass",
                    expected=f"Lint to pass on {filename} (exit code 0)",
                    actual=f"Lint failed (exit code {result_proc.returncode})",
                    details=f"Lint output: {output}",
                )

            return f"Lint passed on {filename}\n{output}"
        except Exception as e:
            # If we can't run flake8, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="Could not run flake8",
                expected="flake8 to be available",
                actual=f"flake8 execution failed: {type(e).__name__}",
                details=str(e),
            ) from e
