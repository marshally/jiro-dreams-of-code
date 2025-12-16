"""Tests for DocumentationCommand class."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentConfig, AgentResult
from jiro.commands.base import Command
from jiro.steps.documentation.documentation_command import DocumentationCommand
from jiro.steps.documentation.documentation_result import DocumentationResult
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


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
    return Task(
        id="task-123",
        title="Update README",
        task_type="task",
        status="in_progress",
        created_at=datetime.now(),
        description="Improve the README documentation",
    )


@pytest.fixture
def sample_step():
    """Create a sample plan step."""
    return PlanStep(
        step_type=StepType.DOCUMENTATION,
        planning_context="Update the README.md file with installation instructions",
    )


class TestDocumentationCommandIsCommand:
    """Test that DocumentationCommand is a proper Command subclass."""

    @pytest.mark.unit
    def test_is_command_subclass(self):
        """DocumentationCommand should inherit from Command."""
        assert issubclass(DocumentationCommand, Command)

    @pytest.mark.unit
    def test_is_not_abc(self):
        """Should not be an abstract class (can be instantiated)."""
        client = MagicMock()
        client.config = MagicMock()
        cmd = DocumentationCommand(client)
        assert isinstance(cmd, DocumentationCommand)


class TestDocumentationCommandAttributes:
    """Test DocumentationCommand class attributes."""

    @pytest.mark.unit
    def test_has_output_schema(self, mock_client):
        """Should have output_schema set to DocumentationResult."""
        cmd = DocumentationCommand(mock_client)
        assert cmd.output_schema == DocumentationResult

    @pytest.mark.unit
    def test_has_tools(self, mock_client):
        """Should have tools attribute."""
        cmd = DocumentationCommand(mock_client)
        assert hasattr(cmd, "tools")
        assert isinstance(cmd.tools, list)

    @pytest.mark.unit
    def test_stores_client(self, mock_client):
        """Should store the client."""
        cmd = DocumentationCommand(mock_client)
        assert cmd.client == mock_client


class TestDocumentationCommandExecute:
    """Test DocumentationCommand.execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_documentation_result(
        self, mock_client, sample_task, sample_step
    ):
        """execute() should return DocumentationResult."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Updated README.md",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = DocumentationCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["README.md"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert isinstance(result, DocumentationResult)
            assert result.doc_files_changed == 1
            assert result.py_files_changed == 0
            assert Path("README.md") in result.changed_files

    @pytest.mark.asyncio
    async def test_execute_counts_py_files(self, mock_client, sample_task, sample_step):
        """execute() should count Python files with doc changes."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Added docstrings",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = DocumentationCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["src/foo.py", "src/bar.py"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.doc_files_changed == 0
            assert result.py_files_changed == 2

    @pytest.mark.asyncio
    async def test_execute_handles_mixed_files(self, mock_client, sample_task, sample_step):
        """execute() should count both markdown and Python files."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Updated docs",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = DocumentationCommand(mock_client)

        with patch.object(
            cmd, "_get_changed_files", return_value=["README.md", "src/foo.py", "docs/api.md"]
        ):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.doc_files_changed == 2  # README.md, docs/api.md
            assert result.py_files_changed == 1  # src/foo.py

    @pytest.mark.asyncio
    async def test_execute_raises_on_agent_failure(self, mock_client, sample_task, sample_step):
        """execute() should raise ValueError when agent fails."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="Agent error",
        )

        cmd = DocumentationCommand(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Documentation agent execution failed"):
            await cmd.execute(step=sample_step, task=sample_task)

    @pytest.mark.asyncio
    async def test_execute_tracks_tokens(self, mock_client, sample_task, sample_step):
        """execute() should track token usage."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Done",
            tokens_before=100,
            tokens_after=350,
            error=None,
        )

        cmd = DocumentationCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["README.md"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.tokens_in == 100
            assert result.tokens_out == 250  # 350 - 100

    @pytest.mark.asyncio
    async def test_execute_tracks_model(self, mock_client, sample_task, sample_step):
        """execute() should track subagent model used."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Done",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = DocumentationCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["README.md"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.subagent_type == "claude-3-haiku-20240307"


class TestDocumentationCommandBuildPrompt:
    """Test DocumentationCommand._build_documentation_prompt method."""

    @pytest.mark.unit
    def test_prompt_includes_task_id(self, mock_client, sample_task, sample_step):
        """Prompt should include task ID."""
        cmd = DocumentationCommand(mock_client)
        prompt = cmd._build_documentation_prompt(sample_step, sample_task)
        assert "task-123" in prompt

    @pytest.mark.unit
    def test_prompt_includes_task_title(self, mock_client, sample_task, sample_step):
        """Prompt should include task title."""
        cmd = DocumentationCommand(mock_client)
        prompt = cmd._build_documentation_prompt(sample_step, sample_task)
        assert "Update README" in prompt

    @pytest.mark.unit
    def test_prompt_includes_planning_context(self, mock_client, sample_task, sample_step):
        """Prompt should include planning context."""
        cmd = DocumentationCommand(mock_client)
        prompt = cmd._build_documentation_prompt(sample_step, sample_task)
        assert "installation instructions" in prompt

    @pytest.mark.unit
    def test_prompt_includes_documentation_rules(self, mock_client, sample_task, sample_step):
        """Prompt should include documentation rules."""
        cmd = DocumentationCommand(mock_client)
        prompt = cmd._build_documentation_prompt(sample_step, sample_task)
        assert "ONLY modify documentation" in prompt
        assert "DO NOT modify any code logic" in prompt


class TestDocumentationCommandGetChangedFiles:
    """Test DocumentationCommand._get_changed_files method."""

    @pytest.mark.unit
    def test_get_changed_files_success(self, mock_client):
        """_get_changed_files should return changed files."""
        cmd = DocumentationCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="README.md\nsrc/foo.py\n", returncode=0)

            files = cmd._get_changed_files()

            assert "README.md" in files
            assert "src/foo.py" in files

    @pytest.mark.unit
    def test_get_changed_files_empty(self, mock_client):
        """_get_changed_files should handle empty output."""
        cmd = DocumentationCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)

            files = cmd._get_changed_files()

            assert files == []

    @pytest.mark.unit
    def test_get_changed_files_handles_error(self, mock_client):
        """_get_changed_files should handle subprocess errors."""
        cmd = DocumentationCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            from subprocess import CalledProcessError

            mock_run.side_effect = CalledProcessError(1, "git")

            files = cmd._get_changed_files()

            assert files == []
