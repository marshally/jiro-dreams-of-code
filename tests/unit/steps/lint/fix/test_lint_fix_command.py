"""Tests for LintFixCommand class."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentResult
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

    def test_init_with_client(self):
        """LintFixCommand should accept an AgentClient."""
        client = MagicMock()
        cmd = LintFixCommand(client)
        assert cmd.client is client


class TestLintFixCommandExecution:
    """Test LintFixCommand execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """execute() should return LintFixResult on successful agent execution."""
        # Setup mocks
        client = AsyncMock()
        agent_result = AgentResult(
            success=True,
            output="Fixed E501 in src/test.py",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )
        client.execute.return_value = agent_result

        cmd = LintFixCommand(client)
        step = MagicMock()
        step.planning_context = "Fix E501 line too long"
        task = MagicMock()
        task.id = "test-1"
        task.title = "Fix lint error"
        task.description = "Fix a lint error"

        # Mock git diff to return a file
        with patch("jiro.steps.lint.fix.lint_fix_command.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="src/test.py\n",
                stderr="",
                returncode=0,
            )

            result = await cmd.execute(step=step, task=task)

        # Verify result
        assert isinstance(result, LintFixResult)
        assert len(result.changed_files) == 1
        assert result.changed_files[0] == Path("src/test.py")
        assert "E501" in result.error_code
        assert result.filename == "src/test.py"

    @pytest.mark.asyncio
    async def test_execute_agent_failure(self):
        """execute() should raise ValueError when agent fails."""
        # Setup mocks
        client = AsyncMock()
        agent_result = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="Agent execution failed",
        )
        client.execute.return_value = agent_result

        cmd = LintFixCommand(client)
        step = MagicMock()
        task = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            await cmd.execute(step=step, task=task)

        assert "Lint fix agent execution failed" in str(exc_info.value)

    def test_extract_error_code_valid(self):
        """_extract_error_code should find valid error codes."""
        output = "Fixed E501 in src/test.py"
        assert LintFixCommand._extract_error_code(output) == "E501"

        output = "Fixed W503 issue"
        assert LintFixCommand._extract_error_code(output) == "W503"

        output = "Fixed C901 complexity"
        assert LintFixCommand._extract_error_code(output) == "C901"

    def test_extract_error_code_not_found(self):
        """_extract_error_code should return 'unknown' if no code found."""
        output = "Fixed some issue"
        assert LintFixCommand._extract_error_code(output) == "unknown"

    def test_extract_filename_single_file(self):
        """_extract_filename should return single changed file."""
        output = "Fixed error"
        changed_files = ["src/test.py"]
        assert LintFixCommand._extract_filename(output, changed_files) == "src/test.py"

    def test_extract_filename_from_output(self):
        """_extract_filename should extract from output if multiple files."""
        output = "Fixed error in 'src/main.py'"
        changed_files = []
        assert LintFixCommand._extract_filename(output, changed_files) == "src/main.py"

    def test_extract_filename_unknown(self):
        """_extract_filename should return 'unknown' if not found."""
        output = "Fixed error"
        changed_files = []
        assert LintFixCommand._extract_filename(output, changed_files) == "unknown"
