"""Verification for TDD green step.

Verifies that the TDD green step result meets the verification rules:
- Only implementation files in changed_files (NO test files)
- git diff --name-only matches exactly changed_files
- Test must PASS when run (without skip)
- @pytest.mark.skip decorator has been REMOVED from the test
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


class TddGreenVerify(Verification):
    """Verification for TDD green step.

    Validates that:
    1. Only implementation files are in changed_files (no test files)
    2. git diff --name-only matches exactly changed_files
    3. The test actually passes when run (with exit code 0)
    4. The @pytest.mark.skip decorator has been removed from the test
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the TDD green step result.

        Args:
            result: The TddGreenResult from command execution

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

            # Rule 3: Test passes when run
            test_output = self._verify_test_passes(result)

            # Rule 4: @pytest.mark.skip has been removed
            self._verify_skip_removed(result)

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="pytest -xvs --tb=short <test_specifier>",
                verification_output=test_output,
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _verify_only_implementation_files(self, result: Result) -> None:
        """Verify that only implementation files are in changed_files.

        Args:
            result: The TddGreenResult

        Raises:
            VerificationError: If any test file is in changed_files
        """
        test_files = [f for f in result.changed_files if self._is_test_file(f)]

        if test_files:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Only implementation files allowed",
                expected="All changed_files should be implementation files",
                actual=f"Found test files: {test_files}",
                details=f"Files: {[str(f) for f in test_files]}",
            )

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The TddGreenResult

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
                step_type=StepType.TDD_GREEN,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_test_passes(self, result: Result) -> str:
        """Verify that the test passes when run.

        Runs pytest and checks exit code 0 (success).

        Args:
            result: The TddGreenResult

        Returns:
            The test output showing the passing test

        Raises:
            VerificationError: If the test doesn't pass
        """
        # Get test specifier from result
        test_specifier = getattr(result, "test_specifier", None)
        if not test_specifier:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Missing test_specifier",
                expected="result.test_specifier to be set",
                actual="test_specifier is None or empty",
                details="Cannot verify test without specifier",
            )

        # Run pytest to verify the test passes
        try:
            result_proc = subprocess.run(
                ["python", "-m", "pytest", test_specifier, "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            output = result_proc.stdout + result_proc.stderr

            # If test failed (exit code non-zero), that's a problem
            if result_proc.returncode != 0:
                raise VerificationError(
                    step_type=StepType.TDD_GREEN,
                    rule_violated="Test does not pass",
                    expected="Test to pass (exit code 0)",
                    actual=f"Test failed (exit code {result_proc.returncode})",
                    details="A green test must pass to be correct",
                )

            return output
        except Exception as e:
            # If we can't run pytest, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Could not run pytest",
                expected="pytest to be available",
                actual=f"pytest execution failed: {type(e).__name__}",
                details=str(e),
            ) from e

    def _verify_skip_removed(self, result: Result) -> None:
        """Verify that @pytest.mark.skip has been removed from the test.

        Args:
            result: The TddGreenResult

        Raises:
            VerificationError: If @pytest.mark.skip is still present on the test
        """
        test_specifier = getattr(result, "test_specifier", None)
        if not test_specifier:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Missing test_specifier",
                expected="result.test_specifier to be set",
                actual="test_specifier is None or empty",
                details="Cannot verify skip removal without specifier",
            )

        # Extract test file and test name from specifier
        # Format: "path/to/test_file.py::test_name"
        if "::" not in test_specifier:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Invalid test_specifier format",
                expected="test_specifier to contain '::' separator",
                actual=f"test_specifier format: {test_specifier}",
                details="Expected format: 'path/to/test_file.py::test_name'",
            )

        test_file_str, test_name = test_specifier.rsplit("::", 1)
        test_file = Path(test_file_str)

        # Read the test file
        try:
            content = test_file.read_text()
        except Exception as e:
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Could not read test file",
                expected=f"Test file {test_file} to be readable",
                actual=f"File read failed: {type(e).__name__}",
                details=str(e),
            ) from e

        # Look for @pytest.mark.skip before the test function
        # Pattern: @pytest.mark.skip followed by def test_name
        pattern = (
            r"@pytest\.mark\.skip\s*\([^)]*\)\s*\n" r"\s*def\s+" + re.escape(test_name) + r"\s*\("
        )

        if re.search(pattern, content):
            raise VerificationError(
                step_type=StepType.TDD_GREEN,
                rule_violated="Test still has @pytest.mark.skip decorator",
                expected=f"@pytest.mark.skip to be removed from {test_name}",
                actual="Skip decorator found on test",
                details=f"Pattern matched: {pattern}",
            )

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
