"""Tests for TddGreenCommand class."""

from datetime import datetime

import pytest

from jiro.commands.base import Command
from jiro.steps.tdd.green.tdd_green_command import TddGreenCommand
from jiro.steps.tdd.green.tdd_green_result import TddGreenResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestTddGreenCommandIsCommand:
    """Test that TddGreenCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """TddGreenCommand should inherit from Command."""
        assert issubclass(TddGreenCommand, Command)

    def test_is_not_abc(self):
        """TddGreenCommand should be concrete (not ABC)."""
        # If it's abstract, we can't instantiate it
        try:
            cmd = TddGreenCommand()
            assert isinstance(cmd, Command)
        except TypeError as e:
            pytest.fail(f"TddGreenCommand should be concrete, but got: {e}")


class TestTddGreenCommandClassAttributes:
    """Test class attributes."""

    def test_has_tools_attribute(self):
        """TddGreenCommand should have tools class attribute."""
        assert hasattr(TddGreenCommand, "tools")

    def test_has_output_schema_attribute(self):
        """TddGreenCommand should have output_schema class attribute."""
        assert hasattr(TddGreenCommand, "output_schema")

    def test_output_schema_is_tdd_green_result(self):
        """output_schema should be TddGreenResult."""
        assert TddGreenCommand.output_schema == TddGreenResult


class TestTddGreenCommandExecute:
    """Test the execute method."""

    def test_execute_raises_not_implemented(self):
        """execute() should raise NotImplementedError (placeholder)."""
        cmd = TddGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass",
        )

        with pytest.raises(NotImplementedError, match="not yet implemented"):
            cmd.execute(step=step, task=task)

    def test_execute_has_keyword_only_arguments(self):
        """execute() should use keyword-only arguments."""
        cmd = TddGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass",
        )

        # Should require keyword arguments, not positional
        with pytest.raises(TypeError):
            cmd.execute(step, task)  # type: ignore[call-arg]


class TestTddGreenCommandInstantiation:
    """Test instantiation of TddGreenCommand."""

    def test_can_instantiate(self):
        """Should be able to instantiate TddGreenCommand."""
        cmd = TddGreenCommand()
        assert isinstance(cmd, TddGreenCommand)
        assert isinstance(cmd, Command)

    def test_multiple_instances_are_independent(self):
        """Multiple instances should be independent."""
        cmd1 = TddGreenCommand()
        cmd2 = TddGreenCommand()
        assert cmd1 is not cmd2
