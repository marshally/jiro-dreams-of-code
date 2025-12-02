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

    @pytest.mark.asyncio
    async def test_dream_initialization_requires_client(self):
        """DreamingAgent.__init__ should require client."""
        # Act & Assert
        with pytest.raises(TypeError):
            DreamingAgent(None)

    @pytest.mark.asyncio
    async def test_dream_raises_error_without_title(self, mock_client):
        """dream() should raise error if output lacks title."""
        # Arrange
        mock_output = """## Overview

A feature overview.

## Requirements

- Requirement 1

## Acceptance Criteria

- [ ] Criterion 1

## Out of Scope

- Item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="valid title"):
            await agent.dream("Feature without title")

    @pytest.mark.asyncio
    async def test_dream_raises_error_without_overview(self, mock_client):
        """dream() should raise error if output lacks Overview section."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Requirements

- Requirement 1

## Acceptance Criteria

- [ ] Criterion 1

## Out of Scope

- Item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Overview section"):
            await agent.dream("Feature without overview")

    @pytest.mark.asyncio
    async def test_dream_raises_error_without_requirements(self, mock_client):
        """dream() should raise error if output lacks Requirements section."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Overview

A test overview.

## Acceptance Criteria

- [ ] Criterion 1

## Out of Scope

- Item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Requirements section"):
            await agent.dream("Feature without requirements")

    @pytest.mark.asyncio
    async def test_dream_raises_error_without_acceptance_criteria(self, mock_client):
        """dream() should raise error if output lacks Acceptance Criteria section."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Overview

A test overview.

## Requirements

- Requirement 1

## Out of Scope

- Item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Acceptance Criteria section"):
            await agent.dream("Feature without acceptance criteria")

    @pytest.mark.asyncio
    async def test_dream_raises_error_without_out_of_scope(self, mock_client):
        """dream() should raise error if output lacks Out of Scope section."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Overview

A test overview.

## Requirements

- Requirement 1

## Acceptance Criteria

- [ ] Criterion 1
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Out of Scope section"):
            await agent.dream("Feature without out of scope")

    @pytest.mark.asyncio
    async def test_dream_with_optional_technical_notes_missing(self, mock_client):
        """dream() should work when technical notes are missing (optional)."""
        # Arrange
        mock_output = """# Feature: Test Feature

## Overview

A test overview.

## Requirements

- Requirement 1

## Acceptance Criteria

- [ ] Criterion 1

## Out of Scope

- Item
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
        result = await agent.dream("Feature with optional technical notes")

        # Assert
        assert result.technical_notes is None
        assert result.title == "Test Feature"

    @pytest.mark.asyncio
    async def test_refine_calls_build_refinement_prompt(self, mock_client):
        """refine() should use _build_refinement_prompt to create prompt."""
        # Arrange
        initial_spec = Spec(
            title="Initial Feature",
            overview="This is the initial overview.",
            requirements=["Req 1"],
            acceptance_criteria=["Criterion 1"],
            out_of_scope=["Out of scope 1"],
        )

        refined_output = """# Feature: Refined Feature

## Overview

Refined overview.

## Requirements

- Requirement 1

## Acceptance Criteria

- [ ] Criterion 1

## Out of Scope

- Item
"""
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=refined_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act
        await agent.refine(initial_spec, "Make it better")

        # Assert
        # Verify that execute was called with a prompt containing refinement context
        assert mock_client.execute.called
        call_args = mock_client.execute.call_args[0][0]
        assert "Initial Feature" in call_args or "Refined Feature" in call_args

    @pytest.mark.unit
    def test_format_list(self, mock_client):
        """_format_list() should format items as markdown bullet points."""
        # Arrange
        agent = DreamingAgent(mock_client)
        items = ["Item 1", "Item 2", "Item 3"]

        # Act
        result = agent._format_list(items)

        # Assert
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result
        assert result.count("-") == 3

    @pytest.mark.unit
    def test_build_refinement_prompt_with_technical_notes(self, mock_client):
        """_build_refinement_prompt() should include technical notes when present."""
        # Arrange
        agent = DreamingAgent(mock_client)
        spec = Spec(
            title="Feature with Notes",
            overview="An overview",
            requirements=["Req 1"],
            acceptance_criteria=["Criterion 1"],
            out_of_scope=["Out of scope"],
            technical_notes="Some technical implementation details",
        )

        # Act
        prompt = agent._build_refinement_prompt(spec, "Add more details")

        # Assert
        assert "Feature with Notes" in prompt
        assert "Overview" in prompt
        assert "Requirements" in prompt
        assert "Acceptance Criteria" in prompt
        assert "Out of Scope" in prompt
        assert "Technical Notes" in prompt
        assert "Some technical implementation details" in prompt
        assert "Add more details" in prompt

    @pytest.mark.unit
    def test_build_refinement_prompt_without_technical_notes(self, mock_client):
        """_build_refinement_prompt() should work without technical notes."""
        # Arrange
        agent = DreamingAgent(mock_client)
        spec = Spec(
            title="Feature without Notes",
            overview="An overview",
            requirements=["Req 1"],
            acceptance_criteria=["Criterion 1"],
            out_of_scope=["Out of scope"],
        )

        # Act
        prompt = agent._build_refinement_prompt(spec, "Add more details")

        # Assert
        assert "Feature without Notes" in prompt
        assert "Overview" in prompt
        assert "Requirements" in prompt
        assert "Acceptance Criteria" in prompt
        assert "Out of Scope" in prompt
        # Should not include a dedicated Technical Notes section (without the spec.technical_notes value)
        # The prompt mentions "Technical Notes if applicable" but doesn't include it in the structure
        assert "## Technical Notes\n\n" not in prompt
