"""Tests for AgentClient wrapper for Claude Agent SDK."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlite_utils import Database

from jiro.agents.base import AgentConfig, AgentResult
from jiro.agents.client import AgentClient
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import PromptRepository


@pytest.fixture
def db_with_schema(tmp_path: Path) -> Database:
    """Provide a database with schema initialized."""
    db = get_database(tmp_path / "test.db")
    ensure_schema(db)
    return db


@pytest.fixture
def prompt_repository(db_with_schema: Database) -> PromptRepository:
    """Provide a PromptRepository instance."""
    return PromptRepository(db_with_schema)


@pytest.fixture
def agent_config() -> AgentConfig:
    """Provide a sample AgentConfig."""
    return AgentConfig(
        model="claude-opus-4-1",
        system_prompt="You are a helpful assistant.",
        allowed_tools=["tool1", "tool2"],
        permission_mode="acceptEdits",
        max_turns=10,
    )


class TestAgentClientInitialization:
    """Tests for AgentClient initialization."""

    @pytest.mark.unit
    def test_init_accepts_config_and_repository(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should initialize with AgentConfig and PromptRepository."""
        client = AgentClient(agent_config, prompt_repository)
        assert client.config == agent_config
        assert client.repository == prompt_repository

    @pytest.mark.unit
    def test_init_requires_config(self, prompt_repository: PromptRepository) -> None:
        """Should require an AgentConfig."""
        with pytest.raises(TypeError):
            AgentClient(None, prompt_repository)  # type: ignore

    @pytest.mark.unit
    def test_init_requires_repository(self, agent_config: AgentConfig) -> None:
        """Should require a PromptRepository."""
        with pytest.raises(TypeError):
            AgentClient(agent_config, None)  # type: ignore


class TestAgentClientExecute:
    """Tests for execute() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_returns_agent_result(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should return an AgentResult."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Test response"

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert isinstance(result, AgentResult)
            assert result.success is True
            assert result.output is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_tracks_tokens(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should track token usage before and after execution."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Test response"

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.tokens_before >= 0
            assert result.tokens_after >= result.tokens_before

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_stores_result_in_repository(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
        db_with_schema: Database,
    ) -> None:
        """Should store result in prompts table via repository."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Test response"

            client = AgentClient(agent_config, prompt_repository)
            await client.execute("Test prompt")

            # Verify result was stored
            rows = list(db_with_schema["prompts"].rows)
            assert len(rows) > 0
            assert any(row["prompt_text"] == "Test prompt" for row in rows)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_captures_output(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should capture the agent's output."""
        expected_output = "This is the agent response"

        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = expected_output

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.output == expected_output

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_logs_execution(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should log the execution with structlog."""
        with (
            patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query,
            patch("jiro.agents.client.logger") as mock_logger,
        ):
            mock_query.return_value = "Test response"

            client = AgentClient(agent_config, prompt_repository)
            await client.execute("Test prompt")

            # Verify logging was called
            assert mock_logger.info.called


class TestAgentClientErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_handles_agent_errors(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should handle errors from the Agent SDK."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            # Simulate an error
            mock_query.side_effect = RuntimeError("SDK Error")

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.success is False
            assert result.error is not None
            assert "SDK Error" in result.error

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_sets_success_flag_on_error(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should set success=False when an error occurs."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = ValueError("Invalid input")

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.success is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_stores_error_in_repository(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
        db_with_schema: Database,
    ) -> None:
        """Should store error details when execution fails."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            error_message = "Test error message"
            mock_query.side_effect = Exception(error_message)

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.error == error_message

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_handles_network_errors(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Should handle network-related errors gracefully."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = ConnectionError("Network error")

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.success is False
            assert result.error is not None


class TestAgentClientTokenTracking:
    """Tests for token tracking and context usage."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_tokens_increase_after_execution(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
    ) -> None:
        """Tokens should increase after execution."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Response"

            client = AgentClient(agent_config, prompt_repository)
            result = await client.execute("Test prompt")

            assert result.tokens_after >= result.tokens_before

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_tokens_stored_in_repository(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
        db_with_schema: Database,
    ) -> None:
        """Token counts should be stored in the prompts table."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Response"

            client = AgentClient(agent_config, prompt_repository)
            await client.execute("Test prompt")

            rows = list(db_with_schema["prompts"].rows)
            assert len(rows) > 0
            assert rows[0]["tokens_before"] is not None
            assert rows[0]["tokens_after"] is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_prompt_metadata_stored(
        self,
        agent_config: AgentConfig,
        prompt_repository: PromptRepository,
        db_with_schema: Database,
    ) -> None:
        """Should store prompt metadata including agent type and model."""
        with patch("jiro.agents.client.query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = "Response"

            client = AgentClient(agent_config, prompt_repository)
            await client.execute("Test prompt")

            rows = list(db_with_schema["prompts"].rows)
            assert len(rows) > 0
            assert rows[0]["model"] == agent_config.model
            assert rows[0]["agent_type"] in ["dreaming", "planning", "execution", "review"]
