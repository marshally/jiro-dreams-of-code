"""Tests for TestOnlyCommand class."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentResult
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

    def test_can_instantiate_with_client(self):
        """Should be able to instantiate TestOnlyCommand with client."""
        mock_client = MagicMock()
        command = TestOnlyCommand(mock_client)
        assert isinstance(command, TestOnlyCommand)
        assert command.client is mock_client

    def test_has_execute_method(self):
        """TestOnlyCommand should have execute method."""
        mock_client = MagicMock()
        command = TestOnlyCommand(mock_client)
        assert hasattr(command, "execute")
        assert callable(command.execute)


class TestTestOnlyCommandExecute:
    """Test TestOnlyCommand.execute() method."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """execute() should return TestOnlyResult on success."""
        # Mock client
        mock_client = AsyncMock()
        mock_config = MagicMock()
        mock_config.model = "claude-opus-4.5"
        mock_client.config = mock_config

        # Mock agent result
        agent_result = AgentResult(
            success=True,
            output="Tests added successfully",
            tokens_before=100,
            tokens_after=250,
            error=None,
        )
        mock_client.execute.return_value = agent_result

        # Create command
        command = TestOnlyCommand(mock_client)

        # Mock step and task
        mock_step = MagicMock()
        mock_step.planning_context = "Add test for parse_date function"
        mock_task = MagicMock()
        mock_task.id = "test-task-1"
        mock_task.title = "Test Task"
        mock_task.description = "Test description"

        # Mock git and pytest operations
        with patch("subprocess.run") as mock_run:
            # Mock git diff
            mock_diff = MagicMock()
            mock_diff.stdout = "tests/test_parse_date.py\n"
            mock_diff.returncode = 0

            # Mock pytest collect
            mock_collect = MagicMock()
            mock_collect.stdout = "tests/test_parse_date.py::test_parse_date\n"
            mock_collect.returncode = 0

            # Mock pytest run
            mock_pytest = MagicMock()
            mock_pytest.stdout = "test_parse_date PASSED\n"
            mock_pytest.stderr = ""
            mock_pytest.returncode = 0

            # Set up mock_run to return different values based on arguments
            def run_side_effect(*args, **kwargs):
                cmd = args[0]
                if "diff" in cmd:
                    return mock_diff
                elif "--collect-only" in cmd:
                    return mock_collect
                else:
                    return mock_pytest

            mock_run.side_effect = run_side_effect

            # Execute
            result = await command.execute(step=mock_step, task=mock_task)

            # Assert
            assert isinstance(result, TestOnlyResult)
            assert result.subagent_type == "claude-opus-4.5"
            assert result.tokens_in == 100
            assert result.tokens_out == 150
            assert len(result.changed_files) == 1
            assert result.changed_files[0] == Path("tests/test_parse_date.py")

    @pytest.mark.asyncio
    async def test_execute_agent_failure(self):
        """execute() should raise ValueError if agent fails."""
        # Mock client with failure
        mock_client = AsyncMock()
        agent_result = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="Agent execution failed",
        )
        mock_client.execute.return_value = agent_result

        # Create command
        command = TestOnlyCommand(mock_client)

        # Mock step and task
        mock_step = MagicMock()
        mock_step.planning_context = "Add test"
        mock_task = MagicMock()

        # Execute and expect error
        with pytest.raises(ValueError) as exc_info:
            await command.execute(step=mock_step, task=mock_task)
        assert "Test only agent execution failed" in str(exc_info.value)

    def test_build_test_only_prompt(self):
        """_build_test_only_prompt should return formatted prompt."""
        mock_client = MagicMock()
        command = TestOnlyCommand(mock_client)

        mock_step = MagicMock()
        mock_step.planning_context = "Add tests for parse_date function"
        mock_task = MagicMock()
        mock_task.id = "test-123"
        mock_task.title = "Add tests"
        mock_task.description = "Add unit tests"

        prompt = command._build_test_only_prompt(mock_step, mock_task)

        assert "test writing agent" in prompt
        assert "test-123" in prompt
        assert "Add tests" in prompt
        assert "tests/ directory" in prompt

    def test_get_test_specifier(self):
        """_get_test_specifier should extract test specifier from test file."""
        mock_client = MagicMock()
        command = TestOnlyCommand(mock_client)

        # Create temporary test file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_something():\n    pass\n")
            temp_file = f.name

        try:
            test_files = [Path(temp_file)]
            specifier = command._get_test_specifier(test_files)
            assert "::test_something" in specifier
        finally:
            import os

            os.unlink(temp_file)

    def test_get_test_specifier_no_files(self):
        """_get_test_specifier should raise ValueError if no test files."""
        mock_client = MagicMock()
        command = TestOnlyCommand(mock_client)

        with pytest.raises(ValueError) as exc_info:
            command._get_test_specifier([])
        assert "No test files found" in str(exc_info.value)
