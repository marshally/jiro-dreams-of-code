"""Tests for TddRefactorCommand class."""

import pytest

from jiro.commands.base import Command
from jiro.steps.tdd.refactor.tdd_refactor_command import TddRefactorCommand
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult


class TestTddRefactorCommandIsCommand:
    """Test that TddRefactorCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """TddRefactorCommand should inherit from Command."""
        assert issubclass(TddRefactorCommand, Command)

    def test_can_instantiate(self):
        """Should be able to instantiate TddRefactorCommand."""
        command = TddRefactorCommand()
        assert isinstance(command, TddRefactorCommand)


class TestTddRefactorCommandAttributes:
    """Test TddRefactorCommand attributes."""

    def test_has_tools_class_var(self):
        """Should have tools class variable."""
        assert hasattr(TddRefactorCommand, "tools")
        assert isinstance(TddRefactorCommand.tools, list)

    def test_has_output_schema(self):
        """Should have output_schema class variable set to TddRefactorResult."""
        assert hasattr(TddRefactorCommand, "output_schema")
        assert TddRefactorCommand.output_schema is TddRefactorResult


class TestTddRefactorCommandExecute:
    """Test TddRefactorCommand.execute method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError as placeholder."""
        command = TddRefactorCommand()
        with pytest.raises(NotImplementedError, match="Subagent integration via Agent SDK"):
            command.execute(step=None, task=None)
