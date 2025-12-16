"""Tests for BugGreenCommand class."""

from datetime import datetime

import pytest

from jiro.commands.base import Command
from jiro.steps.bug.green.bug_green_command import BugGreenCommand
from jiro.steps.bug.green.bug_green_result import BugGreenResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestBugGreenCommandIsCommand:
    """Test that BugGreenCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """BugGreenCommand should inherit from Command."""
        assert issubclass(BugGreenCommand, Command)

    def test_is_not_abc(self):
        """BugGreenCommand should be concrete (not ABC)."""
        # If it's abstract, we can't instantiate it
        try:
            cmd = BugGreenCommand()
            assert isinstance(cmd, Command)
        except TypeError as e:
            pytest.fail(f"BugGreenCommand should be concrete, but got: {e}")


class TestBugGreenCommandClassAttributes:
    """Test class attributes."""

    def test_has_tools_attribute(self):
        """BugGreenCommand should have tools class attribute."""
        assert hasattr(BugGreenCommand, "tools")

    def test_has_output_schema_attribute(self):
        """BugGreenCommand should have output_schema class attribute."""
        assert hasattr(BugGreenCommand, "output_schema")

    def test_output_schema_is_bug_green_result(self):
        """output_schema should be BugGreenResult."""
        assert BugGreenCommand.output_schema == BugGreenResult


class TestBugGreenCommandExecute:
    """Test the execute method."""

    @pytest.mark.asyncio
    async def test_execute_requires_client(self):
        """execute() should raise ValueError if client is not set."""
        cmd = BugGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.BUG_GREEN,
            planning_context="Fix the password validation bug to make test pass",
        )

        with pytest.raises(ValueError, match="AgentClient not configured"):
            await cmd.execute(step=step, task=task)

    def test_execute_has_keyword_only_arguments(self):
        """execute() should use keyword-only arguments."""
        cmd = BugGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.BUG_GREEN,
            planning_context="Fix the password validation bug to make test pass",
        )

        # Should require keyword arguments, not positional
        with pytest.raises(TypeError):
            cmd.execute(step, task)  # type: ignore[call-arg]


class TestBugGreenCommandInstantiation:
    """Test instantiation of BugGreenCommand."""

    def test_can_instantiate(self):
        """Should be able to instantiate BugGreenCommand."""
        cmd = BugGreenCommand()
        assert isinstance(cmd, BugGreenCommand)
        assert isinstance(cmd, Command)

    def test_multiple_instances_are_independent(self):
        """Multiple instances should be independent."""
        cmd1 = BugGreenCommand()
        cmd2 = BugGreenCommand()
        assert cmd1 is not cmd2
