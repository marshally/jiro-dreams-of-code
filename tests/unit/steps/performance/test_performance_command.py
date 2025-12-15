"""Tests for PerformanceCommand."""

import pytest

from jiro.commands.base import Command
from jiro.steps.performance.performance_command import PerformanceCommand
from jiro.steps.performance.performance_result import PerformanceResult


class TestPerformanceCommandIsCommand:
    """Test that PerformanceCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """PerformanceCommand should inherit from Command."""
        assert issubclass(PerformanceCommand, Command)

    def test_can_instantiate(self):
        """Should be able to instantiate PerformanceCommand."""
        cmd = PerformanceCommand()
        assert isinstance(cmd, PerformanceCommand)


class TestPerformanceCommandOutputSchema:
    """Test PerformanceCommand output schema configuration."""

    def test_output_schema_is_performance_result(self):
        """output_schema should be PerformanceResult."""
        cmd = PerformanceCommand()
        assert cmd.output_schema == PerformanceResult

    def test_output_schema_is_class_var(self):
        """output_schema should be defined as ClassVar."""
        assert hasattr(PerformanceCommand, "output_schema")


class TestPerformanceCommandTools:
    """Test PerformanceCommand tools configuration."""

    def test_tools_exists(self):
        """tools should be defined."""
        cmd = PerformanceCommand()
        assert hasattr(cmd, "tools")

    def test_tools_is_list(self):
        """tools should be a list."""
        cmd = PerformanceCommand()
        assert isinstance(cmd.tools, list)


class TestPerformanceCommandExecute:
    """Test PerformanceCommand execute method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError in placeholder."""
        cmd = PerformanceCommand()
        # Mock step and task - exact types don't matter for NotImplementedError check
        with pytest.raises(NotImplementedError):
            cmd.execute(step=None, task=None)

    def test_execute_error_message(self):
        """execute() should have meaningful error message."""
        cmd = PerformanceCommand()
        with pytest.raises(NotImplementedError) as exc_info:
            cmd.execute(step=None, task=None)
        assert "PerformanceCommand.execute()" in str(exc_info.value)
        assert "Agent SDK" in str(exc_info.value)
