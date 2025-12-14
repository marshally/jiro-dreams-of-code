"""Core type definitions for strongly typed commits.

This module provides the foundational types used throughout the step execution system:
- StepType: Enum of all supported step types
- PlanStep: Dataclass representing a step from the execution plan
- VerificationError: Exception raised when step verification fails
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class StepType(StrEnum):
    """Step types for strongly typed commits.

    Uses StrEnum so values are directly usable as strings without .value
    """

    TDD_RED = "tdd_red"
    TDD_GREEN = "tdd_green"
    TDD_REFACTOR = "tdd_refactor"
    BUG_RED = "bug_red"
    BUG_GREEN = "bug_green"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    LINT_FIX = "lint_fix"
    CONFIG = "config"
    TEST_ONLY = "test_only"
    PERFORMANCE = "performance"


@dataclass(frozen=True)
class PlanStep:
    """A single step from the execution plan.

    Kept minimal - additional fields can be added during implementation if needed.

    Attributes:
        step_type: The type of step to execute
        planning_context: Detailed instructions from planning agent
    """

    step_type: StepType
    planning_context: str


class VerificationError(Exception):
    """Raised when step verification fails.

    Causes immediate HALT - human intervention required.

    Attributes:
        step_type: The step type that failed verification
        rule_violated: Name of the rule that was violated
        expected: What was expected
        actual: What was actually found
        details: Additional details about the failure
    """

    def __init__(
        self,
        step_type: StepType,
        rule_violated: str,
        expected: Any,
        actual: Any,
        details: str,
    ):
        self.step_type = step_type
        self.rule_violated = rule_violated
        self.expected = expected
        self.actual = actual
        self.details = details
        super().__init__(
            f"Verification failed for {step_type}: {rule_violated}\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}\n"
            f"Details: {details}"
        )
