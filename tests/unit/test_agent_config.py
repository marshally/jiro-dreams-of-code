"""Tests for AgentConfig dataclass."""

import pytest

from jiro.agents.base import AgentConfig, AgentResult


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """AgentConfig should require model and system_prompt."""
        config = AgentConfig(
            model="claude-opus-4-20250514",
            system_prompt="You are a helpful assistant.",
        )
        assert config.model == "claude-opus-4-20250514"
        assert config.system_prompt == "You are a helpful assistant."

    @pytest.mark.unit
    def test_allowed_tools_defaults_to_empty_list(self) -> None:
        """allowed_tools should default to empty list."""
        config = AgentConfig(
            model="claude-opus-4-20250514",
            system_prompt="You are a helpful assistant.",
        )
        assert config.allowed_tools == []

    @pytest.mark.unit
    def test_permission_mode_defaults(self) -> None:
        """permission_mode should default to acceptEdits."""
        config = AgentConfig(
            model="claude-opus-4-20250514",
            system_prompt="You are a helpful assistant.",
        )
        assert config.permission_mode == "acceptEdits"

    @pytest.mark.unit
    def test_max_turns_defaults(self) -> None:
        """max_turns should default to 10."""
        config = AgentConfig(
            model="claude-opus-4-20250514",
            system_prompt="You are a helpful assistant.",
        )
        assert config.max_turns == 10

    @pytest.mark.unit
    def test_custom_allowed_tools(self) -> None:
        """allowed_tools should accept custom list."""
        config = AgentConfig(
            model="claude-3-5-haiku-20241022",
            system_prompt="Execute tasks.",
            allowed_tools=["Read", "Write", "Bash"],
        )
        assert config.allowed_tools == ["Read", "Write", "Bash"]

    @pytest.mark.unit
    def test_custom_permission_mode(self) -> None:
        """permission_mode should accept custom value."""
        config = AgentConfig(
            model="claude-3-5-haiku-20241022",
            system_prompt="Execute tasks.",
            permission_mode="bypassPermissions",
        )
        assert config.permission_mode == "bypassPermissions"

    @pytest.mark.unit
    def test_custom_max_turns(self) -> None:
        """max_turns should accept custom value."""
        config = AgentConfig(
            model="claude-3-5-haiku-20241022",
            system_prompt="Execute tasks.",
            max_turns=25,
        )
        assert config.max_turns == 25

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """AgentConfig should accept all fields."""
        config = AgentConfig(
            model="claude-sonnet-4-20250514",
            system_prompt="Review code changes.",
            allowed_tools=["Read", "Grep", "Glob"],
            permission_mode="plan",
            max_turns=5,
        )
        assert config.model == "claude-sonnet-4-20250514"
        assert config.system_prompt == "Review code changes."
        assert config.allowed_tools == ["Read", "Grep", "Glob"]
        assert config.permission_mode == "plan"
        assert config.max_turns == 5


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """AgentResult should require all core fields."""
        result = AgentResult(
            success=True,
            output="Task completed successfully.",
            tokens_before=1000,
            tokens_after=1500,
        )
        assert result.success is True
        assert result.output == "Task completed successfully."
        assert result.tokens_before == 1000
        assert result.tokens_after == 1500

    @pytest.mark.unit
    def test_error_defaults_to_none(self) -> None:
        """error should default to None."""
        result = AgentResult(
            success=True,
            output="Done.",
            tokens_before=500,
            tokens_after=800,
        )
        assert result.error is None

    @pytest.mark.unit
    def test_success_with_error(self) -> None:
        """AgentResult can have error even with success=False."""
        result = AgentResult(
            success=False,
            output="",
            tokens_before=1000,
            tokens_after=1200,
            error="Test failed with exit code 1",
        )
        assert result.success is False
        assert result.error == "Test failed with exit code 1"

    @pytest.mark.unit
    def test_tokens_delta(self) -> None:
        """tokens_after - tokens_before gives context delta."""
        result = AgentResult(
            success=True,
            output="Generated code.",
            tokens_before=5000,
            tokens_after=7500,
        )
        assert result.tokens_after - result.tokens_before == 2500
