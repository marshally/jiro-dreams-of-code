"""Verification for test only step.

Verifies that the test only step result meets the verification rules:
- Only test files changed (test_ prefix or _test suffix, in tests/ directory)
- git diff --name-only matches exactly changed_files
- Tests must PASS when run
- Exactly one test per commit
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


class TestOnlyVerify(Verification):
    """Verification for test only step.

    Validates that:
    1. Only test files are in changed_files (test_ prefix or _test suffix, in tests/ directory)
    2. git diff --name-only matches exactly changed_files
    3. Tests pass when run (exit code 0)
    4. Exactly one test per commit
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the test only step result.

        Args:
            result: The TestOnlyResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Rule 1: Only test files in changed_files
            self._verify_only_test_files(result)

            # Rule 2: git diff matches changed_files
            self._verify_git_diff_matches(result)

            # Rule 3: Tests pass when run
            test_output = self._verify_tests_pass(result)

            # Rule 4: Exactly one test per commit
            self._verify_one_test_per_commit(result)

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="pytest -xvs --tb=short <test_specifier>",
                verification_output=test_output,
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _verify_only_test_files(self, result: Result) -> None:
        """Verify that only test files are in changed_files.

        Args:
            result: The TestOnlyResult

        Raises:
            VerificationError: If any non-test file is in changed_files
        """
        non_test_files = [f for f in result.changed_files if not self._is_test_file(f)]

        if non_test_files:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Only test files allowed",
                expected="All changed_files should be test files",
                actual=f"Found non-test files: {non_test_files}",
                details=f"Files: {[str(f) for f in non_test_files]}",
            )

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The TestOnlyResult

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
                step_type=StepType.TEST_ONLY,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_tests_pass(self, result: Result) -> str:
        """Verify that tests pass when run.

        Runs pytest and checks exit code 0 (success).

        Args:
            result: The TestOnlyResult

        Returns:
            The test output showing the passing tests

        Raises:
            VerificationError: If tests don't pass
        """
        # Get test specifier from result
        test_specifier = getattr(result, "test_specifier", None)
        if not test_specifier:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Missing test_specifier",
                expected="result.test_specifier to be set",
                actual="test_specifier is None or empty",
                details="Cannot verify tests without specifier",
            )

        # Run pytest to verify the tests pass
        try:
            result_proc = subprocess.run(
                ["python", "-m", "pytest", test_specifier, "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            output = result_proc.stdout + result_proc.stderr

            # If tests failed (exit code non-zero), that's a problem
            if result_proc.returncode != 0:
                raise VerificationError(
                    step_type=StepType.TEST_ONLY,
                    rule_violated="Tests do not pass",
                    expected="Tests to pass (exit code 0)",
                    actual=f"Tests failed (exit code {result_proc.returncode})",
                    details="All tests must pass in a test_only commit",
                )

            return output
        except Exception as e:
            # If we can't run pytest, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Could not run pytest",
                expected="pytest to be available",
                actual=f"pytest execution failed: {type(e).__name__}",
                details=str(e),
            ) from e

    def _verify_one_test_per_commit(self, result: Result) -> None:
        """Verify that exactly one test is added per commit.

        Args:
            result: The TestOnlyResult

        Raises:
            VerificationError: If more than one test is in the specifier
        """
        test_specifier = getattr(result, "test_specifier", None)
        if not test_specifier:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Missing test_specifier",
                expected="result.test_specifier to be set",
                actual="test_specifier is None or empty",
                details="Cannot verify test count without specifier",
            )

        # Count the number of :: separators - single test should have exactly one
        # Format: "path/to/test_file.py::test_name" (one ::)
        # Multiple tests would be: "path/to/test_file.py::test1 path/to/test_file.py::test2" (multiple spaces)
        test_parts = test_specifier.split()

        if len(test_parts) > 1:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Multiple tests in one commit",
                expected="Exactly one test per commit",
                actual=f"Found {len(test_parts)} tests in specifier",
                details=f"Specifier: {test_specifier}",
            )

        # Verify there's exactly one :: separator
        colon_count = test_specifier.count("::")
        if colon_count != 1:
            raise VerificationError(
                step_type=StepType.TEST_ONLY,
                rule_violated="Invalid test_specifier format",
                expected="test_specifier to contain exactly one '::' separator",
                actual=f"Found {colon_count} '::' separators",
                details="Format should be: 'path/to/test_file.py::test_name'",
            )

    @staticmethod
    def _is_test_file(path: Path) -> bool:
        """Check if a path is a test file.

        A test file must:
        1. Be in the tests/ directory OR
        2. Have test_ prefix or _test suffix

        Args:
            path: The file path to check

        Returns:
            True if the file is a test file, False otherwise
        """
        name = str(path)
        # Must be in tests/ directory
        if not name.startswith("tests/"):
            return False
        # And must have test_ prefix or _test suffix
        basename = Path(name).name
        return basename.startswith("test_") or basename.endswith("_test.py")
