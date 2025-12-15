"""Tests for TestOnlyCommand class."""

import pytest

from jiro.commands.base import Command
from jiro.steps.test.only.test_only_command import TestOnlyCommand
from jiro.steps.test.only.test_only_result import TestOnlyResult


class TestTestOnlyCommandIsCommand:
    """Test that TestOnlyCommand is a proper Command."""

    def test_is_command_subclass(self):
        """TestOnlyCommand should inherit from Command."""
        assert issubclass(TestOnlyCommand, Command)

    def test_has_tools_class_var(self):
        """TestOnlyCommand should have tools ClassVar."""
        assert hasattr(TestOnlyCommand, "tools")

    def test_has_output_schema_class_var(self):
        """TestOnlyCommand should have output_schema ClassVar."""
        assert hasattr(TestOnlyCommand, "output_schema")

    def test_output_schema_is_test_only_result(self):
        """output_schema should be TestOnlyResult."""
        assert TestOnlyCommand.output_schema == TestOnlyResult


class TestTestOnlyCommandInstantiation:
    """Test creating TestOnlyCommand instances."""

    def test_can_instantiate(self):
        """Should be able to instantiate TestOnlyCommand."""
        command = TestOnlyCommand()
        assert isinstance(command, TestOnlyCommand)

    def test_has_execute_method(self):
        """TestOnlyCommand should have execute method."""
        command = TestOnlyCommand()
        assert hasattr(command, "execute")
        assert callable(command.execute)


class TestTestOnlyCommandExecute:
    """Test TestOnlyCommand.execute() method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError."""
        command = TestOnlyCommand()

        # Mock PlanStep and Task
        class MockPlanStep:
            step_type = "test_only"
            planning_context = "Add test"

        class MockTask:
            id = "test-task"

        with pytest.raises(NotImplementedError) as exc_info:
            command.execute(step=MockPlanStep(), task=MockTask())
        assert "not yet implemented" in str(exc_info.value)
