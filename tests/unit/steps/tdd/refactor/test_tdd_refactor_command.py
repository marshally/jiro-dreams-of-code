"""Tests for TddRefactorCommand class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.client import AgentClient
from jiro.commands.base import Command
from jiro.steps.tdd.refactor.tdd_refactor_command import TddRefactorCommand
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


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


class TestTddRefactorCommandInitialization:
    """Test initialization of TddRefactorCommand."""

    def test_can_instantiate_without_client(self):
        """Should be able to instantiate TddRefactorCommand without client."""
        cmd = TddRefactorCommand()
        assert isinstance(cmd, TddRefactorCommand)
        assert cmd.client is None

    def test_can_instantiate_with_client(self):
        """Should be able to instantiate TddRefactorCommand with client."""
        mock_client = MagicMock(spec=AgentClient)
        cmd = TddRefactorCommand(client=mock_client)
        assert isinstance(cmd, TddRefactorCommand)
        assert cmd.client is mock_client


class TestTddRefactorCommandExecute:
    """Test TddRefactorCommand.execute method."""

    @pytest.mark.asyncio
    async def test_execute_raises_without_client(self):
        """execute() should raise ValueError if client is not set."""
        cmd = TddRefactorCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_REFACTOR,
            planning_context="Refactor code to improve readability",
        )

        with pytest.raises(ValueError, match="AgentClient not configured"):
            await cmd.execute(step=step, task=task)

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_returns_tdd_refactor_result(self, mock_run):
        """execute() should return TddRefactorResult."""
        # Mock git diff
        mock_run.return_value = MagicMock(
            stdout="src/auth.py\n",
            stderr="",
            returncode=0,
        )

        # Mock client
        mock_client = MagicMock(spec=AgentClient)
        mock_client.config = MagicMock(model="claude-opus-4.5")
        mock_client.execute = AsyncMock(
            return_value=AgentResult(
                success=True,
                output="Refactored code by extracting method",
                tokens_before=100,
                tokens_after=200,
                error=None,
            )
        )

        cmd = TddRefactorCommand(client=mock_client)

        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_REFACTOR,
            planning_context="Refactor code to improve readability",
        )

        result = await cmd.execute(step=step, task=task)

        assert isinstance(result, TddRefactorResult)
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 100
        assert result.tokens_out == 100

    @pytest.mark.asyncio
    async def test_execute_raises_on_agent_failure(self):
        """execute() should raise ValueError if agent fails."""
        # Mock client with failed result
        mock_client = MagicMock(spec=AgentClient)
        mock_client.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                output="",
                tokens_before=100,
                tokens_after=100,
                error="Agent execution failed",
            )
        )

        cmd = TddRefactorCommand(client=mock_client)

        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_REFACTOR,
            planning_context="Refactor code",
        )

        with pytest.raises(ValueError, match="TDD refactor agent execution failed"):
            await cmd.execute(step=step, task=task)
