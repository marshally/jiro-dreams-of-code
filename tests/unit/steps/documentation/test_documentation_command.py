"""Tests for DocumentationCommand class."""

from jiro.commands.base import Command
from jiro.steps.documentation.documentation_command import DocumentationCommand
from jiro.steps.documentation.documentation_result import DocumentationResult


class TestDocumentationCommandIsCommand:
    """Test that DocumentationCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """DocumentationCommand should inherit from Command."""
        assert issubclass(DocumentationCommand, Command)

    def test_can_instantiate(self):
        """Should be able to instantiate DocumentationCommand."""
        cmd = DocumentationCommand()
        assert isinstance(cmd, DocumentationCommand)


class TestDocumentationCommandAttributes:
    """Test DocumentationCommand class attributes."""

    def test_has_output_schema(self):
        """Should have output_schema set to DocumentationResult."""
        cmd = DocumentationCommand()
        assert cmd.output_schema == DocumentationResult

    def test_has_tools(self):
        """Should have tools attribute."""
        cmd = DocumentationCommand()
        assert hasattr(cmd, "tools")
        assert isinstance(cmd.tools, list)


class TestDocumentationCommandExecute:
    """Test DocumentationCommand.execute method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError (placeholder)."""
        cmd = DocumentationCommand()
        try:
            cmd.execute(step=None, task=None)  # type: ignore
            raise AssertionError("Should have raised NotImplementedError")
        except NotImplementedError as e:
            assert "not yet implemented" in str(e)
            assert "Agent SDK" in str(e)
