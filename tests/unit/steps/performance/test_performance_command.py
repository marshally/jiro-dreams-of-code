"""Tests for PerformanceCommand."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentConfig, AgentResult
from jiro.commands.base import Command
from jiro.steps.performance.performance_command import PerformanceCommand
from jiro.steps.performance.performance_result import PerformanceResult
from jiro.steps.types import PlanStep, StepType


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


@pytest.fixture
def mock_client():
    """Create a mock AgentClient."""
    client = MagicMock()
    client.config = AgentConfig(model="claude-3-haiku-20240307", system_prompt="")
    client.execute = AsyncMock()
    return client


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return MagicMock(
        id="task-123",
        title="Optimize performance",
        task_type="task",
        status="in_progress",
        created_at=datetime.now(),
        description="Make code faster",
    )


@pytest.fixture
def sample_step():
    """Create a sample plan step."""
    return PlanStep(
        step_type=StepType.PERFORMANCE,
        planning_context="Optimize the cache lookup algorithm",
    )


class TestPerformanceCommandExecute:
    """Test PerformanceCommand execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_performance_result(self, mock_client, sample_task, sample_step):
        """execute() should return PerformanceResult."""
        # Setup
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Optimized cache lookup",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = PerformanceCommand(mock_client)

        # Patch subprocess calls
        with patch("jiro.steps.performance.performance_command.subprocess.run") as mock_run:
            # Mock git diff for changed files
            mock_run.return_value = MagicMock(stdout="src/cache.py\n", stderr="", returncode=0)

            result = await cmd.execute(step=sample_step, task=sample_task)

        # Assertions
        assert isinstance(result, PerformanceResult)
        assert result.test_specifier is not None
        assert result.subagent_type == "claude-3-haiku-20240307"
        assert result.tokens_in == 100
        assert result.tokens_out == 100  # 200 - 100

    @pytest.mark.asyncio
    async def test_execute_raises_on_agent_failure(self, mock_client, sample_task, sample_step):
        """execute() should raise ValueError when agent fails."""
        # Setup
        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="Agent execution failed",
        )

        cmd = PerformanceCommand(mock_client)

        # Assert
        with pytest.raises(ValueError) as exc_info:
            await cmd.execute(step=sample_step, task=sample_task)

        assert "Performance agent execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_builds_prompt(self, mock_client, sample_task, sample_step):
        """execute() should build and send prompt to agent."""
        # Setup
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Optimized",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = PerformanceCommand(mock_client)

        # Patch subprocess calls
        with patch("jiro.steps.performance.performance_command.subprocess.run"):
            await cmd.execute(step=sample_step, task=sample_task)

        # Verify prompt was sent to agent
        mock_client.execute.assert_called_once()
        prompt = mock_client.execute.call_args[0][0]
        assert "task-123" in prompt
        assert "Optimize performance" in prompt
        assert "performance optimization" in prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_tracks_token_usage(self, mock_client, sample_task, sample_step):
        """execute() should track token usage."""
        # Setup
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Done",
            tokens_before=500,
            tokens_after=750,
            error=None,
        )

        cmd = PerformanceCommand(mock_client)

        # Patch subprocess calls
        with patch("jiro.steps.performance.performance_command.subprocess.run"):
            result = await cmd.execute(step=sample_step, task=sample_task)

        # Assertions
        assert result.tokens_in == 500
        assert result.tokens_out == 250  # 750 - 500
