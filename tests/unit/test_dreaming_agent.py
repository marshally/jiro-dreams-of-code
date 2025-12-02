"""Tests for DreamingAgent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.dreaming import DreamingAgent
from jiro.core.planner import Spec


class TestDreamingAgent:
    """Tests for the DreamingAgent class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_dream_returns_spec(self, mock_client):
        """dream() should return a Spec object from prompt."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Overview

This is a test feature that does something useful.

## Requirements

- Requirement 1: First requirement
- Requirement 2: Second requirement
- Requirement 3: Third requirement

## Acceptance Criteria

- [ ] First criterion
- [ ] Second criterion
- [ ] Third criterion

## Out of Scope

- Out of scope item 1
- Out of scope item 2

## Technical Notes

Some technical notes here.
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act
        result = await agent.dream("Create a feature for user authentication")

        # Assert
        assert isinstance(result, Spec)
        assert result.title == "Test Feature"
        assert "test feature" in result.overview.lower()
        assert len(result.requirements) == 3
        assert len(result.acceptance_criteria) == 3
        assert len(result.out_of_scope) == 2
        assert result.technical_notes is not None

    @pytest.mark.asyncio
    async def test_dream_calls_client_with_prompt(self, mock_client):
        """dream() should call client.execute with proper prompt."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="# Feature: Test\n\n## Overview\nTest\n\n## Requirements\n- Req 1\n\n## Acceptance Criteria\n- [ ] Criterion\n\n## Out of Scope\n- Item",
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)
        user_prompt = "I need a dark mode feature"

        # Act
        await agent.dream(user_prompt)

        # Assert
        assert mock_client.execute.called
        call_args = mock_client.execute.call_args[0][0]
        assert "dark mode" in call_args.lower() or "feature" in call_args.lower()

    @pytest.mark.asyncio
    async def test_refine_returns_updated_spec(self, mock_client):
        """refine() should return an updated Spec with feedback applied."""
        # Arrange
        initial_spec = Spec(
            title="Initial Feature",
            overview="This is the initial overview.",
            requirements=["Req 1", "Req 2"],
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            out_of_scope=["Out of scope 1"],
        )

        refined_output = """# Feature: Improved Feature

## Overview

This is an improved overview based on feedback.

## Requirements

- Requirement 1: Updated requirement
- Requirement 2: Updated requirement
- Requirement 3: New requirement

## Acceptance Criteria

- [ ] Improved criterion 1
- [ ] Improved criterion 2

## Out of Scope

- Updated out of scope item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=refined_output,
            tokens_before=200,
            tokens_after=400,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act
        result = await agent.refine(initial_spec, "Make this more comprehensive")

        # Assert
        assert isinstance(result, Spec)
        assert result.title == "Improved Feature"
        assert "improved" in result.overview.lower()
        assert len(result.requirements) == 3

    @pytest.mark.asyncio
    async def test_dream_handles_failure(self, mock_client):
        """dream() should raise error when client returns failure."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="API Error",
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="API Error"):
            await agent.dream("Some prompt")

    @pytest.mark.asyncio
    async def test_refine_handles_failure(self, mock_client):
        """refine() should raise error when client returns failure."""
        # Arrange
        spec = Spec(
            title="Test",
            overview="Test overview",
            requirements=["Req 1"],
            acceptance_criteria=["Criterion"],
            out_of_scope=["Item"],
        )

        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="API Error",
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="API Error"):
            await agent.refine(spec, "Some feedback")

    @pytest.mark.asyncio
    async def test_dream_spec_has_all_required_fields(self, mock_client):
        """Generated spec should have all required fields."""
        # Arrange
        mock_output = """# Feature: Complete Feature

## Overview

A complete feature with all fields properly defined.

## Requirements

- Requirement 1
- Requirement 2

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Out of Scope

- Item not included

## Technical Notes

These are technical notes.
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act
        result = await agent.dream("A feature request")

        # Assert
        assert result.title
        assert result.overview
        assert result.requirements
        assert result.acceptance_criteria
        assert result.out_of_scope
        # technical_notes is optional
