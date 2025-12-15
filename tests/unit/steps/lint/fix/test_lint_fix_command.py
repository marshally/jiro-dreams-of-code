"""Tests for LintFixCommand class."""

from jiro.commands.base import Command
from jiro.steps.lint.fix.lint_fix_command import LintFixCommand
from jiro.steps.lint.fix.lint_fix_result import LintFixResult


class TestLintFixCommandClass:
    """Test that LintFixCommand is properly defined."""

    def test_inherits_from_command(self):
        """LintFixCommand should inherit from Command."""
        assert issubclass(LintFixCommand, Command)

    def test_has_output_schema(self):
        """LintFixCommand should have output_schema set to LintFixResult."""
        assert LintFixCommand.output_schema == LintFixResult

    def test_has_tools_class_var(self):
        """LintFixCommand should have tools class variable."""
        assert hasattr(LintFixCommand, "tools")
        assert isinstance(LintFixCommand.tools, list)


class TestLintFixCommandExecution:
    """Test LintFixCommand execution."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError."""
        cmd = LintFixCommand()
        try:
            cmd.execute(step=None, task=None)
            raise AssertionError("Should raise NotImplementedError")
        except NotImplementedError as e:
            assert "not yet implemented" in str(e)
            assert "Agent SDK" in str(e)
