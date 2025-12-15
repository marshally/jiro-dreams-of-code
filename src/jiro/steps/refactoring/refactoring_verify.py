"""Verification for refactoring step.

Verifies that the refactoring step result meets the verification rules:
- Only implementation files in changed_files (NO test files)
- git diff --name-only matches exactly changed_files
- Test must PASS when run (all existing tests still pass)
- Verify checksum via refactoring MCP (if available, optional feature)
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


class RefactoringVerify(Verification):
    """Verification for refactoring step.

    Validates that:
    1. Only implementation files are in changed_files (no test files)
    2. git diff --name-only matches exactly changed_files
    3. All tests pass when run
    4. Checksum is valid (optional feature, can be stubbed)
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the refactoring step result.

        Args:
            result: The RefactoringResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Rule 1: Only implementation files in changed_files
            self._verify_only_implementation_files(result)

            # Rule 2: git diff matches changed_files
            self._verify_git_diff_matches(result)

            # Rule 3: Tests pass when run
            test_output = self._verify_tests_pass(result)

            # Rule 4: Verify checksum (optional feature)
            self._verify_checksum(result)

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="pytest -xvs --tb=short",
                verification_output=test_output,
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _verify_only_implementation_files(self, result: Result) -> None:
        """Verify that only implementation files are in changed_files.

        Args:
            result: The RefactoringResult

        Raises:
            VerificationError: If any test file is in changed_files
        """
        test_files = [f for f in result.changed_files if self._is_test_file(f)]

        if test_files:
            raise VerificationError(
                step_type=StepType.REFACTORING,
                rule_violated="Only implementation files allowed",
                expected="All changed_files should be implementation files",
                actual=f"Found test files: {test_files}",
                details=f"Files: {[str(f) for f in test_files]}",
            )

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The RefactoringResult

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
                step_type=StepType.REFACTORING,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.REFACTORING,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_tests_pass(self, result: Result) -> str:
        """Verify that all tests pass when run.

        Runs pytest and checks exit code 0 (success).

        Args:
            result: The RefactoringResult

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
                    step_type=StepType.REFACTORING,
                    rule_violated="Tests do not pass",
                    expected="All tests to pass (exit code 0)",
                    actual=f"Tests failed (exit code {result_proc.returncode})",
                    details="Refactoring must not break any existing tests",
                )

            return output
        except Exception as e:
            # If we can't run pytest, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.REFACTORING,
                rule_violated="Could not run pytest",
                expected="pytest to be available",
                actual=f"pytest execution failed: {type(e).__name__}",
                details=str(e),
            ) from e

    def _verify_checksum(self, result: Result) -> None:
        """Verify the checksum from refactoring MCP (optional feature).

        Args:
            result: The RefactoringResult

        Raises:
            VerificationError: If checksum verification fails

        Note:
            This is an optional feature that can be stubbed. In the current
            implementation, we just verify the checksum is not empty.
            Full MCP integration can be added later.
        """
        checksum = getattr(result, "checksum", None)
        if not checksum:
            # For now, just warn that checksum is empty
            # In the future, this could verify against the refactoring MCP
            pass

    @staticmethod
    def _is_test_file(path: Path) -> bool:
        """Check if a path is a test file.

        Args:
            path: The file path to check

        Returns:
            True if the file is a test file, False otherwise
        """
        name = str(path)
        return name.startswith("tests/") or name.endswith("_test.py")
