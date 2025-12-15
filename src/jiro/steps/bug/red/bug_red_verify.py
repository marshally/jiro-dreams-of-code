"""Verification for bug red step.

Verifies that the bug red step result meets the verification rules:
- Only test files in changed_files
- git diff --name-only matches exactly changed_files
- Test must fail when run (proves bug exists, without skip)
- Test is marked with @pytest.mark.skip
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


class BugRedVerify(Verification):
    """Verification for bug red step.

    Validates that:
    1. Only test files are in changed_files
    2. git diff --name-only matches exactly changed_files
    3. The test actually fails when run (proves the bug exists)
    4. The test is marked with @pytest.mark.skip
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the bug red step result.

        Args:
            result: The BugRedResult from command execution

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

            # Rule 3: Test fails when run (proves bug exists)
            test_output = self._verify_test_fails(result)

            # Rule 4: Test is marked with @pytest.mark.skip
            self._verify_test_is_skipped(result)

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
            result: The BugRedResult

        Raises:
            VerificationError: If any non-test file is in changed_files
        """
        non_test_files = [f for f in result.changed_files if not self._is_test_file(f)]

        if non_test_files:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Only test files allowed",
                expected="All changed_files should be test files",
                actual=f"Found non-test files: {non_test_files}",
                details=f"Files: {[str(f) for f in non_test_files]}",
            )

    def _verify_git_diff_matches(self, result: Result) -> None:
        """Verify git diff --name-only matches exactly changed_files.

        Args:
            result: The BugRedResult

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
                step_type=StepType.BUG_RED,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

        # Convert result.changed_files to relative paths
        result_files = {str(f) for f in result.changed_files}

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_test_fails(self, result: Result) -> str:
        """Verify that the test fails when run without skip.

        This proves the bug exists.

        Args:
            result: The BugRedResult

        Returns:
            The test output showing the failure

        Raises:
            VerificationError: If the test doesn't fail
        """
        # Get test specifier from result
        test_specifier = getattr(result, "test_specifier", None)
        if not test_specifier:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Missing test_specifier",
                expected="result.test_specifier to be set",
                actual="test_specifier is None or empty",
                details="Cannot verify test without specifier",
            )

        # Run pytest to verify the test fails
        try:
            result_proc = subprocess.run(
                ["python", "-m", "pytest", test_specifier, "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            output = result_proc.stdout + result_proc.stderr

            # If test passed (exit code 0), that's a problem - it means the bug doesn't exist
            if result_proc.returncode == 0:
                raise VerificationError(
                    step_type=StepType.BUG_RED,
                    rule_violated="Test does not fail",
                    expected="Test to fail (exit code non-zero)",
                    actual=f"Test passed (exit code {result_proc.returncode})",
                    details="A bug red test must fail to prove the bug exists",
                )

            return output
        except Exception as e:
            # If we can't run pytest, it's a verification error
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Could not run pytest",
                expected="pytest to be available",
                actual=f"pytest execution failed: {type(e).__name__}",
                details=str(e),
            ) from e

    def _verify_test_is_skipped(self, result: Result) -> None:
        """Verify that the test is marked with @pytest.mark.skip.

        Args:
            result: The BugRedResult

        Raises:
            VerificationError: If the test is not marked with @pytest.mark.skip
        """
        test_file = getattr(result, "test_file", None)
        if not test_file:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Missing test_file",
                expected="result.test_file to be set",
                actual="test_file is None",
                details="Cannot verify skip marker without test file",
            )

        # Read the test file
        try:
            content = test_file.read_text()
        except Exception as e:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Could not read test file",
                expected=f"Test file {test_file} to be readable",
                actual=f"File read failed: {type(e).__name__}",
                details=str(e),
            ) from e

        # Get test name from result
        test_name = getattr(result, "test_name", None)
        if not test_name:
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Missing test_name",
                expected="result.test_name to be set",
                actual="test_name is None",
                details="Cannot verify skip marker without test name",
            )

        # Look for the test function and @pytest.mark.skip before it
        # Pattern: @pytest.mark.skip followed by def test_name
        pattern = (
            r"@pytest\.mark\.skip\s*\([^)]*reason\s*=\s*[\"']Bug red:[^\"']*[\"'][^)]*\)\s*\n"
            r"\s*def\s+" + re.escape(test_name) + r"\s*\("
        )

        if not re.search(pattern, content):
            raise VerificationError(
                step_type=StepType.BUG_RED,
                rule_violated="Test is not marked with @pytest.mark.skip",
                expected=f'Test {test_name} to have @pytest.mark.skip(reason="Bug red: ...")',
                actual="Skip marker not found or incorrect",
                details=f"Pattern not found: {pattern}",
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
