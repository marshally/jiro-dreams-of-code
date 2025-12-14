"""Tests for step type definitions."""

from enum import StrEnum

import pytest

from jiro.steps.types import PlanStep, StepType, VerificationError


class TestStepType:
    """Tests for StepType StrEnum."""

    def test_step_type_is_str_enum(self):
        """StepType should be a StrEnum."""
        assert issubclass(StepType, StrEnum)

    def test_all_eleven_step_types_exist(self):
        """All 11 step types should be defined."""
        expected = {
            "tdd_red",
            "tdd_green",
            "tdd_refactor",
            "bug_red",
            "bug_green",
            "refactoring",
            "documentation",
            "lint_fix",
            "config",
            "test_only",
            "performance",
        }
        actual = {member.value for member in StepType}
        assert actual == expected

    def test_step_type_values_usable_as_strings(self):
        """StepType values should be directly usable as strings."""
        # StrEnum allows direct string comparison without .value
        assert StepType.TDD_RED == "tdd_red"
        assert StepType.TDD_GREEN == "tdd_green"
        assert StepType.TDD_REFACTOR == "tdd_refactor"
        assert StepType.BUG_RED == "bug_red"
        assert StepType.BUG_GREEN == "bug_green"
        assert StepType.REFACTORING == "refactoring"
        assert StepType.DOCUMENTATION == "documentation"
        assert StepType.LINT_FIX == "lint_fix"
        assert StepType.CONFIG == "config"
        assert StepType.TEST_ONLY == "test_only"
        assert StepType.PERFORMANCE == "performance"

    def test_step_type_can_be_used_in_f_strings(self):
        """StepType should work in f-strings without .value."""
        step = StepType.TDD_RED
        assert f"Step type: {step}" == "Step type: tdd_red"


class TestPlanStep:
    """Tests for PlanStep dataclass."""

    def test_plan_step_has_required_fields(self):
        """PlanStep should have step_type and planning_context fields."""
        step = PlanStep(
            step_type=StepType.TDD_RED,
            planning_context="Write a failing test for login validation",
        )
        assert step.step_type == StepType.TDD_RED
        assert step.planning_context == "Write a failing test for login validation"

    def test_plan_step_is_dataclass(self):
        """PlanStep should be a dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(PlanStep)

    def test_plan_step_equality(self):
        """PlanStep instances with same values should be equal."""
        step1 = PlanStep(step_type=StepType.TDD_RED, planning_context="context")
        step2 = PlanStep(step_type=StepType.TDD_RED, planning_context="context")
        assert step1 == step2

    def test_plan_step_immutability(self):
        """PlanStep should be immutable (frozen)."""
        step = PlanStep(step_type=StepType.TDD_RED, planning_context="context")
        with pytest.raises(AttributeError):
            step.step_type = StepType.TDD_GREEN  # type: ignore[misc]


class TestVerificationError:
    """Tests for VerificationError exception."""

    def test_verification_error_is_exception(self):
        """VerificationError should be an Exception."""
        assert issubclass(VerificationError, Exception)

    def test_verification_error_stores_attributes(self):
        """VerificationError should store all passed attributes."""
        error = VerificationError(
            step_type=StepType.TDD_RED,
            rule_violated="only_test_files",
            expected=["tests/test_auth.py"],
            actual=["tests/test_auth.py", "src/auth.py"],
            details="Implementation file was modified during TDD red step",
        )
        assert error.step_type == StepType.TDD_RED
        assert error.rule_violated == "only_test_files"
        assert error.expected == ["tests/test_auth.py"]
        assert error.actual == ["tests/test_auth.py", "src/auth.py"]
        assert error.details == "Implementation file was modified during TDD red step"

    def test_verification_error_message_format(self):
        """VerificationError message should include all relevant info."""
        error = VerificationError(
            step_type=StepType.TDD_RED,
            rule_violated="only_test_files",
            expected=["tests/test_auth.py"],
            actual=["tests/test_auth.py", "src/auth.py"],
            details="Implementation file was modified",
        )
        message = str(error)
        assert "tdd_red" in message
        assert "only_test_files" in message
        assert "Expected" in message
        assert "Actual" in message
        assert "Details" in message

    def test_verification_error_can_be_raised_and_caught(self):
        """VerificationError should be raisable and catchable."""
        with pytest.raises(VerificationError) as exc_info:
            raise VerificationError(
                step_type=StepType.LINT_FIX,
                rule_violated="single_file",
                expected=1,
                actual=3,
                details="Multiple files were changed",
            )
        assert exc_info.value.step_type == StepType.LINT_FIX
