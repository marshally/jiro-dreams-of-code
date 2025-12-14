"""Tests for TddRedCommand class."""

from datetime import datetime

import pytest

from jiro.commands.base import Command
from jiro.steps.tdd.red.tdd_red_command import TddRedCommand
from jiro.steps.tdd.red.tdd_red_result import TddRedResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestTddRedCommandIsCommand:
    """Test that TddRedCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """TddRedCommand should inherit from Command."""
        assert issubclass(TddRedCommand, Command)

    def test_is_not_abc(self):
        """TddRedCommand should be concrete (not ABC)."""
        # If it's abstract, we can't instantiate it
        try:
            cmd = TddRedCommand()
            assert isinstance(cmd, Command)
        except TypeError as e:
            pytest.fail(f"TddRedCommand should be concrete, but got: {e}")


class TestTddRedCommandClassAttributes:
    """Test class attributes."""

    def test_has_tools_attribute(self):
        """TddRedCommand should have tools class attribute."""
        assert hasattr(TddRedCommand, "tools")

    def test_has_output_schema_attribute(self):
        """TddRedCommand should have output_schema class attribute."""
        assert hasattr(TddRedCommand, "output_schema")

    def test_output_schema_is_tdd_red_result(self):
        """output_schema should be TddRedResult."""
        assert TddRedCommand.output_schema == TddRedResult


class TestTddRedCommandExecute:
    """Test the execute method."""

    def test_execute_raises_not_implemented(self):
        """execute() should raise NotImplementedError (placeholder)."""
        cmd = TddRedCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_RED,
            planning_context="Create a test for login validation",
        )

        with pytest.raises(NotImplementedError, match="not yet implemented"):
            cmd.execute(step=step, task=task)

    def test_execute_has_keyword_only_arguments(self):
        """execute() should use keyword-only arguments."""
        cmd = TddRedCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_RED,
            planning_context="Create a test for login validation",
        )

        # Should require keyword arguments, not positional
        with pytest.raises(TypeError):
            cmd.execute(step, task)  # type: ignore[call-arg]


class TestTddRedCommandInstantiation:
    """Test instantiation of TddRedCommand."""

    def test_can_instantiate(self):
        """Should be able to instantiate TddRedCommand."""
        cmd = TddRedCommand()
        assert isinstance(cmd, TddRedCommand)
        assert isinstance(cmd, Command)

    def test_multiple_instances_are_independent(self):
        """Multiple instances should be independent."""
        cmd1 = TddRedCommand()
        cmd2 = TddRedCommand()
        assert cmd1 is not cmd2
