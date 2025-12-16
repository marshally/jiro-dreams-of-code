"""Tests for ExecutionAgent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.execution import (
    ExecutionAgent,
    ExecutionResult,
)
from jiro.core.execution_plan import ExecutionPlanSchema, ExecutionStep, FileAction


class TestExecutionAgentInitialization:
    """Tests for ExecutionAgent initialization."""

    @pytest.mark.unit
    def test_initialization_requires_client(self):
        """ExecutionAgent.__init__ should require client."""
        with pytest.raises(TypeError):
            ExecutionAgent(None)

    @pytest.mark.unit
    def test_initialization_success(self):
        """ExecutionAgent should initialize with client."""
        client = MagicMock()
        agent = ExecutionAgent(client)
        assert agent.client == client


class TestExecutionAgent:
    """Tests for the ExecutionAgent class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_plan(self):
        """Create a sample execution plan."""
        steps = [
            ExecutionStep(
                description="Create User model",
                step_type="tdd_green",
                files=[FileAction(path="src/models/user.py", action="create")],
                verification_command="pytest tests/test_user.py",
            ),
            ExecutionStep(
                description="Add authentication middleware",
                step_type="tdd_green",
                files=[FileAction(path="src/middleware/auth.py", action="create")],
                verification_command="pytest tests/test_auth.py",
            ),
        ]
        return ExecutionPlanSchema(
            task_id="task-123",
            steps=steps,
            estimated_tokens=300,
        )

    @pytest.mark.asyncio
    async def test_execute_follows_plan(self, mock_client, sample_plan):
        """execute() should follow the plan step by step."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Step completed successfully",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert result.plan_id == "task-123"
        assert result.total_steps == 2
        assert result.steps_completed == 2
        assert result.success is True
        assert len(result.step_results) == 2

    @pytest.mark.asyncio
    async def test_execute_stops_on_error(self, mock_client, sample_plan):
        """execute() should stop on first error."""
        # Arrange
        # First step succeeds, second fails
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="Step 1 completed",
                tokens_before=100,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=False,
                output="",
                tokens_before=200,
                tokens_after=200,
                error="File not found",
            ),
        ]

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        assert result.success is False
        assert result.steps_completed == 1
        assert result.total_steps == 2
        assert result.error is not None
        assert "File not found" in result.error
        # Should only have results for completed steps
        assert len(result.step_results) == 2

    @pytest.mark.asyncio
    async def test_execute_tracks_context_usage(self, mock_client, sample_plan):
        """execute() should track cumulative token usage."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="Step 1",
                tokens_before=100,
                tokens_after=250,
                error=None,
            ),
            AgentResult(
                success=True,
                output="Step 2",
                tokens_before=250,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        # Total tokens should be sum of all context tokens used
        assert result.total_tokens > 0
        # Should track from first token count to last
        assert result.total_tokens == 300  # 400 - 100

    @pytest.mark.asyncio
    async def test_execute_creates_step_results(self, mock_client, sample_plan):
        """execute() should create detailed step results."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="Created User model",
                tokens_before=100,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output="Created auth middleware",
                tokens_before=200,
                tokens_after=300,
                error=None,
            ),
        ]

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        assert len(result.step_results) == 2
        step_0 = result.step_results[0]
        assert step_0.step_index == 0
        assert step_0.success is True
        assert "User model" in step_0.output
        assert step_0.error is None

        step_1 = result.step_results[1]
        assert step_1.step_index == 1
        assert step_1.success is True
        assert "auth middleware" in step_1.output

    @pytest.mark.asyncio
    async def test_step_result_on_error(self, mock_client, sample_plan):
        """step_result should include error when step fails."""
        # Arrange
        error_msg = "Failed to create file"
        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error=error_msg,
        )

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        step = result.step_results[0]
        assert step.success is False
        assert step.error == error_msg

    @pytest.mark.asyncio
    async def test_execute_with_single_step(self, mock_client):
        """execute() should handle single-step plans."""
        # Arrange
        single_step_plan = ExecutionPlanSchema(
            task_id="task-single",
            steps=[
                ExecutionStep(
                    description="Single step",
                    step_type="tdd_green",
                    files=[FileAction(path="file.py", action="create")],
                )
            ],
            estimated_tokens=100,
        )

        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Completed",
            tokens_before=50,
            tokens_after=150,
            error=None,
        )

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(single_step_plan)

        # Assert
        assert result.total_steps == 1
        assert result.steps_completed == 1
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_result_has_required_fields(self, mock_client, sample_plan):
        """ExecutionResult should have all required fields."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Done",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        agent = ExecutionAgent(mock_client)

        # Act
        result = await agent.execute(sample_plan)

        # Assert
        assert hasattr(result, "plan_id")
        assert hasattr(result, "steps_completed")
        assert hasattr(result, "total_steps")
        assert hasattr(result, "success")
        assert hasattr(result, "step_results")
        assert hasattr(result, "total_tokens")
        assert hasattr(result, "error")
