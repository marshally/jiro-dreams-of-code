"""Tests for ConfigCommand class."""

import pytest

from jiro.commands.base import Command
from jiro.steps.config.config_command import ConfigCommand
from jiro.steps.config.config_result import ConfigResult


class TestConfigCommandIsCommand:
    """Test that ConfigCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """ConfigCommand should inherit from Command."""
        assert issubclass(ConfigCommand, Command)

    def test_can_instantiate(self):
        """Should be able to instantiate ConfigCommand."""
        command = ConfigCommand()
        assert isinstance(command, ConfigCommand)


class TestConfigCommandAttributes:
    """Test ConfigCommand class attributes."""

    def test_has_tools_attribute(self):
        """Should have tools class variable."""
        assert hasattr(ConfigCommand, "tools")
        assert ConfigCommand.tools == []

    def test_has_output_schema_attribute(self):
        """Should have output_schema class variable."""
        assert hasattr(ConfigCommand, "output_schema")
        assert ConfigCommand.output_schema is ConfigResult


class TestConfigCommandExecute:
    """Test the execute method."""

    def test_execute_not_implemented(self):
        """execute() should raise NotImplementedError."""
        command = ConfigCommand()
        with pytest.raises(NotImplementedError):
            command.execute(step=None, task=None)
