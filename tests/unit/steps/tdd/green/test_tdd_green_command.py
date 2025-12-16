"""Tests for TddGreenCommand class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.client import AgentClient
from jiro.commands.base import Command
from jiro.steps.tdd.green.tdd_green_command import TddGreenCommand
from jiro.steps.tdd.green.tdd_green_result import TddGreenResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestTddGreenCommandIsCommand:
    """Test that TddGreenCommand is a proper Command subclass."""

    def test_is_command_subclass(self):
        """TddGreenCommand should inherit from Command."""
        assert issubclass(TddGreenCommand, Command)

    def test_is_not_abc(self):
        """TddGreenCommand should be concrete (not ABC)."""
        # If it's abstract, we can't instantiate it
        try:
            cmd = TddGreenCommand()
            assert isinstance(cmd, Command)
        except TypeError as e:
            pytest.fail(f"TddGreenCommand should be concrete, but got: {e}")


class TestTddGreenCommandClassAttributes:
    """Test class attributes."""

    def test_has_tools_attribute(self):
        """TddGreenCommand should have tools class attribute."""
        assert hasattr(TddGreenCommand, "tools")

    def test_has_output_schema_attribute(self):
        """TddGreenCommand should have output_schema class attribute."""
        assert hasattr(TddGreenCommand, "output_schema")

    def test_output_schema_is_tdd_green_result(self):
        """output_schema should be TddGreenResult."""
        assert TddGreenCommand.output_schema == TddGreenResult


class TestTddGreenCommandInitialization:
    """Test initialization of TddGreenCommand."""

    def test_can_instantiate_without_client(self):
        """Should be able to instantiate TddGreenCommand without client."""
        cmd = TddGreenCommand()
        assert isinstance(cmd, TddGreenCommand)
        assert cmd.client is None

    def test_can_instantiate_with_client(self):
        """Should be able to instantiate TddGreenCommand with client."""
        mock_client = MagicMock(spec=AgentClient)
        cmd = TddGreenCommand(client=mock_client)
        assert isinstance(cmd, TddGreenCommand)
        assert cmd.client is mock_client


class TestTddGreenCommandExecute:
    """Test the execute method."""

    @pytest.mark.asyncio
    async def test_execute_raises_without_client(self):
        """execute() should raise ValueError if client is not set."""
        cmd = TddGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass",
        )

        with pytest.raises(ValueError, match="AgentClient not configured"):
            await cmd.execute(step=step, task=task)

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_returns_tdd_green_result(self, mock_run):
        """execute() should return TddGreenResult."""
        # Mock git diff
        mock_run.return_value = MagicMock(
            stdout="src/auth.py\n",
            stderr="",
            returncode=0,
        )

        # Create mock client with async execute
        mock_client = MagicMock(spec=AgentClient)
        mock_client.config = MagicMock(model="claude-opus-4.5")
        mock_client.execute = AsyncMock(
            return_value=AgentResult(
                success=True,
                output="Implemented email validation",
                tokens_before=100,
                tokens_after=250,
                error=None,
            )
        )

        cmd = TddGreenCommand(client=mock_client)

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass in tests/test_auth.py::test_validate_email",
        )

        result = await cmd.execute(step=step, task=task)

        assert isinstance(result, TddGreenResult)
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 100
        assert result.tokens_out == 150  # 250 - 100

    @pytest.mark.asyncio
    async def test_execute_raises_when_agent_fails(self):
        """execute() should raise ValueError if agent execution fails."""
        # Create mock client that returns failure
        mock_client = MagicMock(spec=AgentClient)
        mock_client.config = MagicMock(model="claude-opus-4.5")
        mock_client.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                output="",
                tokens_before=100,
                tokens_after=100,
                error="Agent execution failed",
            )
        )

        cmd = TddGreenCommand(client=mock_client)

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass",
        )

        with pytest.raises(ValueError, match="TDD green agent execution failed"):
            await cmd.execute(step=step, task=task)

    def test_execute_has_keyword_only_arguments(self):
        """execute() should use keyword-only arguments."""
        cmd = TddGreenCommand()

        # Create minimal task and step
        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation to make test pass",
        )

        # Should require keyword arguments, not positional
        with pytest.raises(TypeError):
            cmd.execute(step, task)  # type: ignore[call-arg]


class TestTddGreenCommandPromptGeneration:
    """Test the _build_tdd_green_prompt method."""

    def test_prompt_includes_task_id(self):
        """Prompt should include task ID."""
        cmd = TddGreenCommand()

        task = Task(
            id="test-123",
            title="Implement auth",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation",
        )

        prompt = cmd._build_tdd_green_prompt(step, task)

        assert "test-123" in prompt
        assert "Implement auth" in prompt

    def test_prompt_includes_planning_context(self):
        """Prompt should include planning context."""
        cmd = TddGreenCommand()

        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement email validation with regex",
        )

        prompt = cmd._build_tdd_green_prompt(step, task)

        assert "Implement email validation with regex" in prompt

    def test_prompt_includes_green_rules(self):
        """Prompt should include TDD green rules."""
        cmd = TddGreenCommand()

        task = Task(
            id="test-1",
            title="Test task",
            task_type="task",
            status="open",
            created_at=datetime.now(),
        )

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement something",
        )

        prompt = cmd._build_tdd_green_prompt(step, task)

        assert "minimal code" in prompt
        assert "Do NOT modify the test file" in prompt
        assert "@pytest.mark.skip" in prompt


class TestTddGreenCommandExtractTestSpecifier:
    """Test the _extract_test_specifier method."""

    def test_extract_explicit_specifier_from_context(self):
        """Should extract explicit test specifier from planning context."""
        cmd = TddGreenCommand()

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Make tests/test_auth.py::test_validate_email pass",
        )

        specifier = cmd._extract_test_specifier(step, [])

        assert specifier == "tests/test_auth.py::test_validate_email"

    def test_extract_test_file_and_name_separately(self):
        """Should extract test file and name if specified separately."""
        cmd = TddGreenCommand()

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="In test_auth.py implement test_validate_email",
        )

        specifier = cmd._extract_test_specifier(step, [])

        assert "test_auth.py" in specifier
        assert "test_validate_email" in specifier

    def test_raises_when_no_test_specifier_found(self):
        """Should raise ValueError when test specifier cannot be extracted."""
        cmd = TddGreenCommand()

        step = PlanStep(
            step_type=StepType.TDD_GREEN,
            planning_context="Implement something without test info",
        )

        with pytest.raises(ValueError, match="Could not find test specifier"):
            cmd._extract_test_specifier(step, [])


class TestTddGreenCommandInstantiation:
    """Test instantiation of TddGreenCommand."""

    def test_can_instantiate(self):
        """Should be able to instantiate TddGreenCommand."""
        cmd = TddGreenCommand()
        assert isinstance(cmd, TddGreenCommand)
        assert isinstance(cmd, Command)

    def test_multiple_instances_are_independent(self):
        """Multiple instances should be independent."""
        cmd1 = TddGreenCommand()
        cmd2 = TddGreenCommand()
        assert cmd1 is not cmd2
