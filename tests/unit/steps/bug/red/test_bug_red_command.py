"""Tests for BugRedCommand class."""

from datetime import datetime

import pytest

from jiro.commands.base import Command
from jiro.steps.bug.red.bug_red_command import BugRedCommand
from jiro.steps.bug.red.bug_red_result import BugRedResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestBugRedCommandIsCommand:
    """Test that BugRedCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """BugRedCommand should inherit from Command."""
        assert issubclass(BugRedCommand, Command)

    def test_is_not_abc(self):
        """BugRedCommand should be concrete (not ABC)."""
        # If it's abstract, we can't instantiate it
        try:
            cmd = BugRedCommand()
            assert isinstance(cmd, Command)
        except TypeError as e:
            pytest.fail(f"BugRedCommand should be concrete, but got: {e}")


class TestBugRedCommandClassAttributes:
    """Test class attributes."""

    def test_has_tools_attribute(self):
        """BugRedCommand should have tools class attribute."""
        assert hasattr(BugRedCommand, "tools")

    def test_has_output_schema_attribute(self):
        """BugRedCommand should have output_schema class attribute."""
        assert hasattr(BugRedCommand, "output_schema")

    def test_output_schema_is_bug_red_result(self):
        """output_schema should be BugRedResult."""
        assert BugRedCommand.output_schema == BugRedResult


class TestBugRedCommandExecute:
    """Test the execute method."""

    @pytest.mark.asyncio
    async def test_execute_requires_client(self):
        """execute() should raise ValueError if client is not set."""
        cmd = BugRedCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.BUG_RED,
            planning_context="Create a test to reproduce email validation bug",
        )

        with pytest.raises(ValueError, match="AgentClient not configured"):
            await cmd.execute(step=step, task=task)

    def test_execute_has_keyword_only_arguments(self):
        """execute() should use keyword-only arguments."""
        cmd = BugRedCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.BUG_RED,
            planning_context="Create a test to reproduce the bug",
        )

        # Should require keyword arguments, not positional
        with pytest.raises(TypeError):
            cmd.execute(step, task)  # type: ignore[call-arg]


class TestBugRedCommandInstantiation:
    """Test instantiation of BugRedCommand."""

    def test_can_instantiate(self):
        """Should be able to instantiate BugRedCommand."""
        cmd = BugRedCommand()
        assert isinstance(cmd, BugRedCommand)
        assert isinstance(cmd, Command)

    def test_multiple_instances_are_independent(self):
        """Multiple instances should be independent."""
        cmd1 = BugRedCommand()
        cmd2 = BugRedCommand()
        assert cmd1 is not cmd2
