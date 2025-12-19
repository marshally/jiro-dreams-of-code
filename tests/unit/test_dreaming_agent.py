"""Tests for DreamingAgent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.dreaming import (
    MAX_INTERVIEW_QUESTIONS,
    DreamingAgent,
    InterviewMessage,
    InterviewResult,
)
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


class TestInterviewDataclasses:
    """Tests for interview-related dataclasses."""

    def test_interview_message_creation(self):
        """InterviewMessage should store role and content."""
        msg = InterviewMessage(role="assistant", content="What would you like to build?")
        assert msg.role == "assistant"
        assert msg.content == "What would you like to build?"

    def test_interview_message_user_role(self):
        """InterviewMessage should accept user role."""
        msg = InterviewMessage(role="user", content="A user auth system")
        assert msg.role == "user"
        assert msg.content == "A user auth system"

    def test_interview_result_creation(self):
        """InterviewResult should store spec and conversation."""
        spec = Spec(
            title="Test",
            overview="Test overview",
            requirements=["Req 1"],
            acceptance_criteria=["Criterion 1"],
            out_of_scope=["Item"],
        )
        conversation = [
            InterviewMessage(role="assistant", content="Question?"),
            InterviewMessage(role="user", content="Answer"),
        ]
        result = InterviewResult(spec=spec, conversation=conversation)
        assert result.spec == spec
        assert len(result.conversation) == 2


class TestDreamingAgentInterview:
    """Tests for DreamingAgent.interview() method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def valid_spec_output(self):
        """Return a valid spec output string."""
        return """# Feature: Test Feature

## Overview

This is a test feature.

## Requirements

- Requirement 1
- Requirement 2
- Requirement 3

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Out of Scope

- Out of scope 1
- Out of scope 2
"""

    @pytest.mark.asyncio
    async def test_interview_returns_result_on_ready_signal(self, mock_client, valid_spec_output):
        """interview() should return InterviewResult when agent signals ready."""
        # Arrange - first call returns question, second returns ready signal
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="What would you like to build?",
                tokens_before=100,
                tokens_after=150,
                error=None,
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nI have enough context for: User auth",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        user_inputs = iter(["A user authentication system"])

        # Act
        result = await agent.interview(lambda: next(user_inputs))

        # Assert
        assert isinstance(result, InterviewResult)
        assert isinstance(result.spec, Spec)
        assert len(result.conversation) == 2  # 1 question, 1 answer

    @pytest.mark.asyncio
    async def test_interview_asks_multiple_questions(self, mock_client, valid_spec_output):
        """interview() should ask multiple questions before generating spec."""
        # Arrange - 3 questions before ready
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 1?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True, output="Question 2?", tokens_before=150, tokens_after=200, error=None
            ),
            AgentResult(
                success=True, output="Question 3?", tokens_before=200, tokens_after=250, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=250,
                tokens_after=300,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=300,
                tokens_after=500,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        answers = iter(["Answer 1", "Answer 2", "Answer 3"])

        # Act
        result = await agent.interview(lambda: next(answers))

        # Assert
        assert len(result.conversation) == 6  # 3 questions, 3 answers

    @pytest.mark.asyncio
    async def test_interview_cancellation_with_quit(self, mock_client):
        """interview() should raise ValueError when user types quit."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="What would you like to build?",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="cancelled"):
            await agent.interview(lambda: "quit")

    @pytest.mark.asyncio
    async def test_interview_cancellation_with_exit(self, mock_client):
        """interview() should raise ValueError when user types exit."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="What would you like to build?",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="cancelled"):
            await agent.interview(lambda: "exit")

    @pytest.mark.asyncio
    async def test_interview_cancellation_with_slash_quit(self, mock_client):
        """interview() should raise ValueError when user types /quit."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="What would you like to build?",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="cancelled"):
            await agent.interview(lambda: "/quit")

    @pytest.mark.asyncio
    async def test_interview_handles_eof_error(self, mock_client):
        """interview() should raise ValueError on EOFError (Ctrl+D)."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="What would you like to build?",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        def raise_eof():
            raise EOFError()

        # Act & Assert
        with pytest.raises(ValueError, match="cancelled"):
            await agent.interview(raise_eof)

    @pytest.mark.asyncio
    async def test_interview_handles_keyboard_interrupt(self, mock_client):
        """interview() should raise ValueError on KeyboardInterrupt."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=True,
            output="What would you like to build?",
            tokens_before=100,
            tokens_after=150,
            error=None,
        )

        agent = DreamingAgent(mock_client)

        def raise_interrupt():
            raise KeyboardInterrupt()

        # Act & Assert
        with pytest.raises(ValueError, match="cancelled"):
            await agent.interview(raise_interrupt)

    @pytest.mark.asyncio
    async def test_interview_skips_empty_responses(self, mock_client, valid_spec_output):
        """interview() should skip empty user responses."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        inputs = iter(["", "", "Real answer"])  # Two empty responses, then real answer

        # Act
        result = await agent.interview(lambda: next(inputs))

        # Assert
        # Only the real answer should be in conversation
        user_messages = [m for m in result.conversation if m.role == "user"]
        assert len(user_messages) == 1
        assert user_messages[0].content == "Real answer"

    @pytest.mark.asyncio
    async def test_interview_max_questions_forces_generation(self, mock_client, valid_spec_output):
        """interview() should generate spec after MAX_INTERVIEW_QUESTIONS."""
        # Arrange - always return a question (never ready signal)
        # Need: 1 first question + (MAX-1) follow-up questions = MAX total
        # Then spec generation call
        question_responses = [
            AgentResult(
                success=True,
                output=f"Question {i}?",
                tokens_before=100 + i * 50,
                tokens_after=150 + i * 50,
                error=None,
            )
            for i in range(MAX_INTERVIEW_QUESTIONS)
        ]
        # Last call is for spec generation
        question_responses.append(
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=600,
                tokens_after=800,
                error=None,
            )
        )

        mock_client.execute.side_effect = question_responses

        agent = DreamingAgent(mock_client)
        answer_count = [0]

        def get_answer():
            answer_count[0] += 1
            return f"Answer {answer_count[0]}"

        # Act
        result = await agent.interview(get_answer)

        # Assert - should have generated spec even without ready signal
        assert isinstance(result.spec, Spec)

    @pytest.mark.asyncio
    async def test_interview_fails_on_client_error_first_question(self, mock_client):
        """interview() should raise ValueError if first question fails."""
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
        with pytest.raises(ValueError, match="Failed to start interview"):
            await agent.interview(lambda: "answer")

    @pytest.mark.asyncio
    async def test_interview_fails_on_client_error_mid_conversation(self, mock_client):
        """interview() should raise ValueError if client fails mid-conversation."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=False, output="", tokens_before=150, tokens_after=150, error="API Error"
            ),
        ]

        agent = DreamingAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="Interview failed"):
            await agent.interview(lambda: "answer")

    @pytest.mark.asyncio
    async def test_interview_calls_display_message(self, mock_client, valid_spec_output):
        """interview() should call display_message callback with agent messages."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 1?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        displayed_messages = []

        # Act
        await agent.interview(
            get_user_input=lambda: "answer",
            display_message=displayed_messages.append,
        )

        # Assert
        assert len(displayed_messages) == 1
        assert "Question 1?" in displayed_messages[0]

    @pytest.mark.unit
    def test_build_interview_prompt_includes_conversation(self, mock_client):
        """_build_interview_prompt() should include full conversation history."""
        # Arrange
        agent = DreamingAgent(mock_client)
        conversation = [
            InterviewMessage(role="assistant", content="What to build?"),
            InterviewMessage(role="user", content="Auth system"),
            InterviewMessage(role="assistant", content="What users?"),
            InterviewMessage(role="user", content="External customers"),
        ]

        # Act
        prompt = agent._build_interview_prompt(conversation)

        # Assert
        assert "What to build?" in prompt
        assert "Auth system" in prompt
        assert "What users?" in prompt
        assert "External customers" in prompt
        assert "[READY_TO_GENERATE]" in prompt  # Instructions included


class TestDreamingAgentCheckpoint:
    """Tests for DreamingAgent.interview() checkpoint callback."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def valid_spec_output(self):
        """Return a valid spec output string."""
        return """# Feature: Test Feature

## Overview

This is a test feature.

## Requirements

- Requirement 1
- Requirement 2
- Requirement 3

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Out of Scope

- Out of scope 1
- Out of scope 2
"""

    @pytest.mark.asyncio
    async def test_checkpoint_called_after_first_question(self, mock_client, valid_spec_output):
        """on_checkpoint should be called after first agent question."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 1?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        checkpoints = []

        # Act
        await agent.interview(
            get_user_input=lambda: "answer",
            on_checkpoint=lambda conv: checkpoints.append(list(conv)),
        )

        # Assert - first checkpoint should have only the first question
        assert len(checkpoints) >= 1
        assert len(checkpoints[0]) == 1  # First question only
        assert checkpoints[0][0].role == "assistant"
        assert checkpoints[0][0].content == "Question 1?"

    @pytest.mark.asyncio
    async def test_checkpoint_called_after_user_response(self, mock_client, valid_spec_output):
        """on_checkpoint should be called after each user response."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 1?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        checkpoints = []

        # Act
        await agent.interview(
            get_user_input=lambda: "My answer",
            on_checkpoint=lambda conv: checkpoints.append(list(conv)),
        )

        # Assert - second checkpoint should include user response
        assert len(checkpoints) >= 2
        # First checkpoint: 1 assistant message
        # Second checkpoint: 1 assistant + 1 user message
        assert len(checkpoints[1]) == 2
        assert checkpoints[1][1].role == "user"
        assert checkpoints[1][1].content == "My answer"

    @pytest.mark.asyncio
    async def test_checkpoint_called_after_each_agent_response(
        self, mock_client, valid_spec_output
    ):
        """on_checkpoint should be called after each agent follow-up question."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 1?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True, output="Question 2?", tokens_before=150, tokens_after=200, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=200,
                tokens_after=250,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=250,
                tokens_after=450,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        answers = iter(["Answer 1", "Answer 2"])
        checkpoints = []

        # Act
        await agent.interview(
            get_user_input=lambda: next(answers),
            on_checkpoint=lambda conv: checkpoints.append(list(conv)),
        )

        # Assert - should have checkpoints for:
        # 1. After first question (1 msg)
        # 2. After first answer (2 msgs)
        # 3. After second question (3 msgs)
        # 4. After second answer (4 msgs)
        assert len(checkpoints) == 4
        assert len(checkpoints[2]) == 3  # Q1, A1, Q2
        assert checkpoints[2][2].role == "assistant"
        assert checkpoints[2][2].content == "Question 2?"

    @pytest.mark.asyncio
    async def test_checkpoint_not_called_without_callback(self, mock_client, valid_spec_output):
        """interview() should work without on_checkpoint callback."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)

        # Act - should not raise
        result = await agent.interview(get_user_input=lambda: "answer")

        # Assert
        assert isinstance(result, InterviewResult)


class TestDreamingAgentResume:
    """Tests for DreamingAgent.interview() resume functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def valid_spec_output(self):
        """Return a valid spec output string."""
        return """# Feature: Test Feature

## Overview

This is a test feature.

## Requirements

- Requirement 1
- Requirement 2
- Requirement 3

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Out of Scope

- Out of scope 1
- Out of scope 2
"""

    @pytest.mark.asyncio
    async def test_resume_skips_first_question(self, mock_client, valid_spec_output):
        """interview() with initial_conversation should skip first question."""
        # Arrange - only need follow-up responses, not first question
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        initial_conversation = [
            InterviewMessage(role="assistant", content="What to build?"),
            InterviewMessage(role="user", content="A todo app"),
        ]

        # Act
        await agent.interview(
            get_user_input=lambda: "More details",
            initial_conversation=initial_conversation,
        )

        # Assert - should not have called execute for first question
        # First call should be for follow-up, not first question
        assert mock_client.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_resume_preserves_conversation_history(self, mock_client, valid_spec_output):
        """interview() should preserve conversation from initial_conversation."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        initial_conversation = [
            InterviewMessage(role="assistant", content="What to build?"),
            InterviewMessage(role="user", content="A todo app"),
            InterviewMessage(role="assistant", content="What features?"),
            InterviewMessage(role="user", content="Add, delete tasks"),
        ]

        # Act
        result = await agent.interview(
            get_user_input=lambda: "Done",
            initial_conversation=initial_conversation,
        )

        # Assert - conversation should include initial messages plus new ones
        assert len(result.conversation) >= 4
        assert result.conversation[0].content == "What to build?"
        assert result.conversation[1].content == "A todo app"
        assert result.conversation[2].content == "What features?"
        assert result.conversation[3].content == "Add, delete tasks"

    @pytest.mark.asyncio
    async def test_resume_continues_question_count(self, mock_client, valid_spec_output):
        """interview() should continue question count from initial_conversation."""
        # Arrange - 2 questions already asked, ask 1 more
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question 3?", tokens_before=150, tokens_after=200, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=200,
                tokens_after=250,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=250,
                tokens_after=450,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        initial_conversation = [
            InterviewMessage(role="assistant", content="Question 1?"),
            InterviewMessage(role="user", content="Answer 1"),
            InterviewMessage(role="assistant", content="Question 2?"),
            InterviewMessage(role="user", content="Answer 2"),
        ]
        answers = iter(["Answer 3", "Answer 4"])

        # Act
        result = await agent.interview(
            get_user_input=lambda: next(answers),
            initial_conversation=initial_conversation,
        )

        # Assert - should have all questions and answers
        assistant_msgs = [m for m in result.conversation if m.role == "assistant"]
        assert len(assistant_msgs) == 3  # 2 initial + 1 new

    @pytest.mark.asyncio
    async def test_resume_with_empty_initial_conversation(self, mock_client, valid_spec_output):
        """interview() with empty initial_conversation should start fresh."""
        # Arrange - empty list means start fresh
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Question?", tokens_before=100, tokens_after=150, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)

        # Act
        await agent.interview(
            get_user_input=lambda: "answer",
            initial_conversation=[],
        )

        # Assert - should have asked first question
        assert mock_client.execute.call_count == 3  # First Q, follow-up, spec gen

    @pytest.mark.asyncio
    async def test_resume_does_not_modify_initial_conversation(
        self, mock_client, valid_spec_output
    ):
        """interview() should not modify the original initial_conversation list."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True, output="Follow-up?", tokens_before=150, tokens_after=200, error=None
            ),
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=200,
                tokens_after=250,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=250,
                tokens_after=450,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        initial_conversation = [
            InterviewMessage(role="assistant", content="Question?"),
            InterviewMessage(role="user", content="Answer"),
        ]
        original_length = len(initial_conversation)

        # Act
        answers = iter(["More", "Done"])
        await agent.interview(
            get_user_input=lambda: next(answers),
            initial_conversation=initial_conversation,
        )

        # Assert - original list should not be modified
        assert len(initial_conversation) == original_length

    @pytest.mark.asyncio
    async def test_resume_checkpoint_continues_from_initial(self, mock_client, valid_spec_output):
        """on_checkpoint should include initial_conversation in checkpoints."""
        # Arrange
        mock_client.execute.side_effect = [
            AgentResult(
                success=True,
                output="[READY_TO_GENERATE]\nReady",
                tokens_before=150,
                tokens_after=200,
                error=None,
            ),
            AgentResult(
                success=True,
                output=valid_spec_output,
                tokens_before=200,
                tokens_after=400,
                error=None,
            ),
        ]

        agent = DreamingAgent(mock_client)
        initial_conversation = [
            InterviewMessage(role="assistant", content="Question?"),
            InterviewMessage(role="user", content="Answer"),
        ]
        checkpoints = []

        # Act
        await agent.interview(
            get_user_input=lambda: "More",
            initial_conversation=initial_conversation,
            on_checkpoint=lambda conv: checkpoints.append(list(conv)),
        )

        # Assert - first checkpoint should include initial conversation plus new message
        assert len(checkpoints) >= 1
        # After user input, checkpoint should have 3 messages
        assert checkpoints[0][0].content == "Question?"
        assert checkpoints[0][1].content == "Answer"
