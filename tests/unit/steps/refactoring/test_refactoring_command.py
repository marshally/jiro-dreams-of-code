"""Tests for RefactoringCommand class."""

import pytest

from jiro.commands.base import Command
from jiro.steps.refactoring.refactoring_command import RefactoringCommand
from jiro.steps.refactoring.refactoring_result import RefactoringResult


class TestRefactoringCommandIsCommand:
    """Test that RefactoringCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """RefactoringCommand should inherit from Command."""
        assert issubclass(RefactoringCommand, Command)

    def test_can_instantiate(self):
        """Should be able to instantiate RefactoringCommand."""
        command = RefactoringCommand()
        assert isinstance(command, RefactoringCommand)


class TestRefactoringCommandAttributes:
    """Test RefactoringCommand attributes."""

    def test_has_tools_class_var(self):
        """Should have tools class variable."""
        assert hasattr(RefactoringCommand, "tools")
        assert isinstance(RefactoringCommand.tools, list)

    def test_has_output_schema(self):
        """Should have output_schema class variable set to RefactoringResult."""
        assert hasattr(RefactoringCommand, "output_schema")
        assert RefactoringCommand.output_schema is RefactoringResult


class TestRefactoringCommandExecute:
    """Test RefactoringCommand.execute method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError as placeholder."""
        command = RefactoringCommand()
        with pytest.raises(NotImplementedError, match="Subagent integration via Agent SDK"):
            command.execute(step=None, task=None)
