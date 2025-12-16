"""TDD phase-specific review validation.

This module provides validation checks for TDD phases that complement the
deterministic checks from jiro.core.review.
"""

import subprocess

import structlog

from jiro.steps.types import StepType

logger = structlog.get_logger()


class TddReviewValidator:
    """Validates TDD phase requirements during code review."""

    @staticmethod
    def validate_tdd_phase(step_type: StepType, commit_sha: str) -> tuple[bool, dict[str, str]]:
        """Validate that a commit meets TDD phase requirements.

        Args:
            step_type: The TDD step type
            commit_sha: The commit SHA to validate

        Returns:
            Tuple of (is_valid, validation_results)
        """
        results = {}

        if step_type == StepType.TDD_RED:
            results.update(TddReviewValidator._validate_red_phase(commit_sha))
        elif step_type == StepType.TDD_GREEN:
            results.update(TddReviewValidator._validate_green_phase(commit_sha))
        elif step_type == StepType.TDD_REFACTOR:
            results.update(TddReviewValidator._validate_refactor_phase(commit_sha))

        # Check if all validations passed
        all_passed = all(v == "PASSED" for k, v in results.items() if k != "commit_type")

        results["tdd_phase_validation"] = "PASSED" if all_passed else "FAILED"
        return all_passed, results

    @staticmethod
    def _validate_red_phase(commit_sha: str) -> dict[str, str]:
        """Validate red phase requirements.

        Red phase must:
        - Only modify test files
        - Have test that fails
        - Have test marked with @pytest.mark.skip

        Args:
            commit_sha: The commit SHA

        Returns:
            Dictionary of validation results
        """
        results = {"red_phase": "PASSED"}

        # Get changed files
        try:
            output = subprocess.run(
                ["git", "show", "--name-only", "--pretty=", commit_sha],
                capture_output=True,
                text=True,
                timeout=10,
            )
            changed_files = [f for f in output.stdout.strip().split("\n") if f]
        except Exception as e:
            results["red_phase"] = f"FAILED: Could not get changed files ({e})"
            return results

        # Check only test files changed
        non_test_files = [
            f for f in changed_files if not (f.startswith("tests/") or f.endswith("_test.py"))
        ]
        if non_test_files:
            results["red_phase"] = f"FAILED: Non-test files changed: {non_test_files}"

        return results

    @staticmethod
    def _validate_green_phase(commit_sha: str) -> dict[str, str]:
        """Validate green phase requirements.

        Green phase must:
        - Only modify implementation files (NO test files)
        - Have test that passes
        - Have @pytest.mark.skip removed

        Args:
            commit_sha: The commit SHA

        Returns:
            Dictionary of validation results
        """
        results = {"green_phase": "PASSED"}

        # Get changed files
        try:
            output = subprocess.run(
                ["git", "show", "--name-only", "--pretty=", commit_sha],
                capture_output=True,
                text=True,
                timeout=10,
            )
            changed_files = [f for f in output.stdout.strip().split("\n") if f]
        except Exception as e:
            results["green_phase"] = f"FAILED: Could not get changed files ({e})"
            return results

        # Check no test files changed
        test_files = [f for f in changed_files if f.startswith("tests/") or f.endswith("_test.py")]
        if test_files:
            results["green_phase"] = f"FAILED: Test files changed: {test_files}"

        return results

    @staticmethod
    def _validate_refactor_phase(commit_sha: str) -> dict[str, str]:
        """Validate refactor phase requirements.

        Refactor phase must:
        - Only modify implementation files (NO test files)
        - All tests must pass
        - Tests must have been passing before (no changes)

        Args:
            commit_sha: The commit SHA

        Returns:
            Dictionary of validation results
        """
        results = {"refactor_phase": "PASSED"}

        # Get changed files
        try:
            output = subprocess.run(
                ["git", "show", "--name-only", "--pretty=", commit_sha],
                capture_output=True,
                text=True,
                timeout=10,
            )
            changed_files = [f for f in output.stdout.strip().split("\n") if f]
        except Exception as e:
            results["refactor_phase"] = f"FAILED: Could not get changed files ({e})"
            return results

        # Check no test files changed
        test_files = [f for f in changed_files if f.startswith("tests/") or f.endswith("_test.py")]
        if test_files:
            results["refactor_phase"] = f"FAILED: Test files changed in refactor: {test_files}"

        return results
