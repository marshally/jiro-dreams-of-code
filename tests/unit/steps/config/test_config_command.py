"""Tests for ConfigCommand class."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentConfig, AgentResult
from jiro.commands.base import Command
from jiro.steps.config.config_command import ConfigCommand
from jiro.steps.config.config_result import ConfigResult
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
        title="Update configuration",
        task_type="task",
        status="in_progress",
        created_at=datetime.now(),
        description="Update application configuration files",
    )


@pytest.fixture
def sample_step():
    """Create a sample plan step."""
    return PlanStep(
        step_type=StepType.CONFIG,
        planning_context="Update the application.yaml file with new settings",
    )


class TestConfigCommandIsCommand:
    """Test that ConfigCommand is a proper Command subclass."""

    @pytest.mark.unit
    def test_is_command_subclass(self):
        """ConfigCommand should inherit from Command."""
        assert issubclass(ConfigCommand, Command)

    @pytest.mark.unit
    def test_is_not_abc(self):
        """Should not be an abstract class (can be instantiated)."""
        client = MagicMock()
        client.config = MagicMock()
        cmd = ConfigCommand(client)
        assert isinstance(cmd, ConfigCommand)


class TestConfigCommandAttributes:
    """Test ConfigCommand class attributes."""

    @pytest.mark.unit
    def test_has_output_schema(self, mock_client):
        """Should have output_schema set to ConfigResult."""
        cmd = ConfigCommand(mock_client)
        assert cmd.output_schema == ConfigResult

    @pytest.mark.unit
    def test_has_tools(self, mock_client):
        """Should have tools attribute."""
        cmd = ConfigCommand(mock_client)
        assert hasattr(cmd, "tools")
        assert isinstance(cmd.tools, list)

    @pytest.mark.unit
    def test_stores_client(self, mock_client):
        """Should store the client."""
        cmd = ConfigCommand(mock_client)
        assert cmd.client == mock_client


class TestConfigCommandExecute:
    """Test the execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_config_result(self, mock_client, sample_task, sample_step):
        """execute() should return ConfigResult."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Updated application.yaml",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = ConfigCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["application.yaml"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert isinstance(result, ConfigResult)
            assert result.config_files_changed == 1
            assert Path("application.yaml") in result.changed_files

    @pytest.mark.asyncio
    async def test_execute_counts_config_files(self, mock_client, sample_task, sample_step):
        """execute() should count config files."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Updated configs",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = ConfigCommand(mock_client)

        with patch.object(
            cmd,
            "_get_changed_files",
            return_value=["config.yaml", "settings.json", ".env"],
        ):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.config_files_changed == 3

    @pytest.mark.asyncio
    async def test_execute_categorizes_config_types(self, mock_client, sample_task, sample_step):
        """execute() should categorize config file types."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="Updated configs",
            tokens_before=100,
            tokens_after=200,
            error=None,
        )

        cmd = ConfigCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["config.yaml", "settings.json"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert "yaml" in result.config_types
            assert "json" in result.config_types

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

        cmd = ConfigCommand(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Config agent execution failed"):
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

        cmd = ConfigCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["config.yaml"]):
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

        cmd = ConfigCommand(mock_client)

        with patch.object(cmd, "_get_changed_files", return_value=["config.yaml"]):
            # Act
            result = await cmd.execute(step=sample_step, task=sample_task)

            # Assert
            assert result.subagent_type == "claude-3-haiku-20240307"


class TestConfigCommandBuildPrompt:
    """Test ConfigCommand._build_config_prompt method."""

    @pytest.mark.unit
    def test_prompt_includes_task_id(self, mock_client, sample_task, sample_step):
        """Prompt should include task ID."""
        cmd = ConfigCommand(mock_client)
        prompt = cmd._build_config_prompt(sample_step, sample_task)
        assert "task-123" in prompt

    @pytest.mark.unit
    def test_prompt_includes_task_title(self, mock_client, sample_task, sample_step):
        """Prompt should include task title."""
        cmd = ConfigCommand(mock_client)
        prompt = cmd._build_config_prompt(sample_step, sample_task)
        assert "Update configuration" in prompt

    @pytest.mark.unit
    def test_prompt_includes_planning_context(self, mock_client, sample_task, sample_step):
        """Prompt should include planning context."""
        cmd = ConfigCommand(mock_client)
        prompt = cmd._build_config_prompt(sample_step, sample_task)
        assert "application.yaml" in prompt

    @pytest.mark.unit
    def test_prompt_includes_config_rules(self, mock_client, sample_task, sample_step):
        """Prompt should include config rules."""
        cmd = ConfigCommand(mock_client)
        prompt = cmd._build_config_prompt(sample_step, sample_task)
        assert "ONLY modify configuration files" in prompt
        assert "DO NOT modify any code files" in prompt


class TestConfigCommandGetChangedFiles:
    """Test ConfigCommand._get_changed_files method."""

    @pytest.mark.unit
    def test_get_changed_files_success(self, mock_client):
        """_get_changed_files should return changed files."""
        cmd = ConfigCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="config.yaml\nsettings.json\n", returncode=0)

            files = cmd._get_changed_files()

            assert "config.yaml" in files
            assert "settings.json" in files

    @pytest.mark.unit
    def test_get_changed_files_empty(self, mock_client):
        """_get_changed_files should handle empty output."""
        cmd = ConfigCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)

            files = cmd._get_changed_files()

            assert files == []

    @pytest.mark.unit
    def test_get_changed_files_handles_error(self, mock_client):
        """_get_changed_files should handle subprocess errors."""
        cmd = ConfigCommand(mock_client)

        with patch("subprocess.run") as mock_run:
            from subprocess import CalledProcessError

            mock_run.side_effect = CalledProcessError(1, "git")

            files = cmd._get_changed_files()

            assert files == []


class TestConfigCommandCategorizeConfigFiles:
    """Test ConfigCommand._categorize_config_files method."""

    @pytest.mark.unit
    def test_categorize_yaml_files(self, mock_client):
        """Should categorize .yaml and .yml files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["config.yaml", "settings.yml"])
        assert "yaml" in config_types

    @pytest.mark.unit
    def test_categorize_json_files(self, mock_client):
        """Should categorize .json files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["config.json"])
        assert "json" in config_types

    @pytest.mark.unit
    def test_categorize_toml_files(self, mock_client):
        """Should categorize .toml files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["pyproject.toml"])
        assert "toml" in config_types

    @pytest.mark.unit
    def test_categorize_ini_files(self, mock_client):
        """Should categorize .ini and .cfg files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["setup.cfg", "settings.ini"])
        assert "ini" in config_types

    @pytest.mark.unit
    def test_categorize_env_files(self, mock_client):
        """Should categorize .env files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files([".env"])
        assert "env" in config_types

    @pytest.mark.unit
    def test_categorize_dockerfile(self, mock_client):
        """Should categorize Dockerfile."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["Dockerfile"])
        assert "dockerfile" in config_types

    @pytest.mark.unit
    def test_categorize_makefile(self, mock_client):
        """Should categorize Makefile."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["Makefile"])
        assert "makefile" in config_types

    @pytest.mark.unit
    def test_categorize_docker_compose(self, mock_client):
        """Should categorize docker-compose files."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(["docker-compose.yaml"])
        assert "docker-compose" in config_types

    @pytest.mark.unit
    def test_categorize_multiple_types(self, mock_client):
        """Should categorize multiple config types."""
        cmd = ConfigCommand(mock_client)
        config_types = cmd._categorize_config_files(
            [
                "config.yaml",
                "settings.json",
                ".env",
                "Dockerfile",
                "setup.cfg",
            ]
        )
        assert "yaml" in config_types
        assert "json" in config_types
        assert "env" in config_types
        assert "dockerfile" in config_types
        assert "ini" in config_types
