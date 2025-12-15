"""Verification for performance step.

Verifies that the performance step result meets the verification rules:
- git diff --name-only matches exactly changed_files
- Tests must PASS when run (exit code 0)
- Performance optimization can touch any files (no restrictions)
"""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


class PerformanceVerify(Verification):
    """Verification for performance step.

    Validates that:
    1. git diff --name-only matches exactly changed_files
    2. All tests pass when run (exit code 0)
    3. No restrictions on which files can change (performance touches implementation, tests, config, etc.)
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the performance step result.

        Args:
            result: The PerformanceResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Rule 1: git diff matches changed_files
            self._verify_git_diff_matches(result)

            # Rule 2: Tests pass when run
            test_output = self._verify_tests_pass(result)

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="pytest -xvs --tb=short",
                verification_output=test_output,
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The PerformanceResult

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
                step_type=StepType.PERFORMANCE,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.PERFORMANCE,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_tests_pass(self, result: Result) -> str:
        """Verify that all tests pass when run.

        Runs pytest and checks exit code 0 (success).

        Args:
            result: The PerformanceResult

        Returns:
            The test output showing passing tests

        Raises:
            VerificationError: If tests don't pass
        """
        # Run pytest to verify tests pass
        try:
            result_proc = subprocess.run(
                ["python", "-m", "pytest", "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            output = result_proc.stdout + result_proc.stderr

            # If tests failed (exit code non-zero), that's a problem
            if result_proc.returncode != 0:
                raise VerificationError(
                    step_type=StepType.PERFORMANCE,
                    rule_violated="Tests do not pass",
                    expected="All tests to pass (exit code 0)",
                    actual=f"Tests failed (exit code {result_proc.returncode})",
                    details="Performance optimization must not break any existing tests",
                )

            return output
        except Exception as e:
            # If we can't run pytest, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.PERFORMANCE,
                rule_violated="Could not run pytest",
                expected="pytest to be available",
                actual=f"pytest execution failed: {type(e).__name__}",
                details=str(e),
            ) from e
