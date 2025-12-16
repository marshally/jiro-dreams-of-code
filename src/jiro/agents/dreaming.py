"""DreamingAgent for generating feature specifications from prompts."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

import structlog

from jiro.agents.client import AgentClient
from jiro.core.planner import (
    Spec,
    _extract_list_section,
    _extract_section,
    _extract_title,
)

logger = structlog.get_logger()

# Safety limit to prevent infinite loops - agent should signal ready well before this
MAX_INTERVIEW_QUESTIONS = 50


@dataclass
class InterviewMessage:
    """A message in the interview conversation.

    Attributes:
        role: Either "assistant" (agent question) or "user" (user answer).
        content: The message content.
    """

    role: Literal["assistant", "user"]
    content: str


@dataclass
class InterviewResult:
    """Result of the interview process.

    Attributes:
        spec: The generated specification.
        conversation: The full conversation history.
    """

    spec: Spec
    conversation: list[InterviewMessage]


class DreamingAgent:
    """Agent that generates feature specifications from natural language prompts.

    The dreaming agent takes a feature request or description and produces
    a structured specification following the Spec schema. It uses Claude
    as the underlying LLM via AgentClient.
    """

    def __init__(self, client: AgentClient) -> None:
        """Initialize DreamingAgent.

        Args:
            client: AgentClient instance for executing the agent.

        Raises:
            TypeError: If client is None.
        """
        if client is None:
            raise TypeError("client cannot be None")
        self.client = client

    async def dream(self, prompt: str) -> Spec:
        """Generate a feature specification from a prompt.

        Takes a natural language feature request or idea and produces a
        structured specification with title, overview, requirements,
        acceptance criteria, out of scope items, and optional technical notes.

        Args:
            prompt: The feature request or description to generate a spec from.

        Returns:
            A Spec object containing the generated specification.

        Raises:
            ValueError: If the agent execution fails.
        """
        logger.info(
            "dreaming_agent_dream_start",
            prompt=prompt,
        )

        # Execute the agent with the user's prompt
        result = await self.client.execute(prompt)

        # Check for errors
        if not result.success:
            logger.error(
                "dreaming_agent_dream_failed",
                error=result.error,
            )
            raise ValueError(f"Agent execution failed: {result.error}")

        # Parse the output into a Spec
        spec = self._parse_spec_from_output(result.output)

        logger.info(
            "dreaming_agent_dream_success",
            title=spec.title,
            num_requirements=len(spec.requirements),
            tokens_used=result.tokens_after - result.tokens_before,
        )

        return spec

    async def refine(self, spec: Spec, feedback: str) -> Spec:
        """Refine an existing specification based on feedback.

        Takes a current specification and user feedback, then generates
        an improved specification that incorporates the feedback.

        Args:
            spec: The current Spec to refine.
            feedback: User feedback or requirements for refinement.

        Returns:
            An updated Spec object with refinements applied.

        Raises:
            ValueError: If the agent execution fails.
        """
        logger.info(
            "dreaming_agent_refine_start",
            title=spec.title,
            feedback=feedback,
        )

        # Build a prompt for refinement
        refinement_prompt = self._build_refinement_prompt(spec, feedback)

        # Execute the agent
        result = await self.client.execute(refinement_prompt)

        # Check for errors
        if not result.success:
            logger.error(
                "dreaming_agent_refine_failed",
                error=result.error,
                title=spec.title,
            )
            raise ValueError(f"Agent execution failed: {result.error}")

        # Parse the refined specification
        refined_spec = self._parse_spec_from_output(result.output)

        logger.info(
            "dreaming_agent_refine_success",
            original_title=spec.title,
            refined_title=refined_spec.title,
            tokens_used=result.tokens_after - result.tokens_before,
        )

        return refined_spec

    def _parse_spec_from_output(self, output: str) -> Spec:
        """Parse agent output into a Spec object.

        Extracts the markdown-formatted specification from the agent's
        output and converts it into a Spec dataclass.

        Args:
            output: The agent's text output containing the specification.

        Returns:
            A Spec object parsed from the output.

        Raises:
            ValueError: If the output doesn't contain required sections.
        """
        # Extract title
        title = _extract_title(output)
        if not title:
            raise ValueError("Output doesn't contain a valid title (# Feature: ...)")

        # Extract sections
        overview = _extract_section(output, "Overview")
        if not overview:
            raise ValueError("Output doesn't contain an Overview section")

        requirements = _extract_list_section(output, "Requirements")
        if not requirements:
            raise ValueError("Output doesn't contain a Requirements section")

        acceptance_criteria = _extract_list_section(output, "Acceptance Criteria")
        if not acceptance_criteria:
            raise ValueError("Output doesn't contain an Acceptance Criteria section")

        out_of_scope = _extract_list_section(output, "Out of Scope")
        if not out_of_scope:
            raise ValueError("Output doesn't contain an Out of Scope section")

        # Technical notes are optional
        technical_notes = _extract_section(output, "Technical Notes")

        return Spec(
            title=title,
            overview=overview,
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
            out_of_scope=out_of_scope,
            technical_notes=technical_notes,
        )

    def _build_refinement_prompt(self, spec: Spec, feedback: str) -> str:
        """Build a prompt for refining an existing specification.

        Args:
            spec: The current specification.
            feedback: User feedback for refinement.

        Returns:
            A formatted prompt for the agent.
        """
        prompt = f"""You have the following feature specification that needs to be refined:

# Feature: {spec.title}

## Overview

{spec.overview}

## Requirements

{self._format_list(spec.requirements)}

## Acceptance Criteria

{self._format_list(spec.acceptance_criteria)}

## Out of Scope

{self._format_list(spec.out_of_scope)}

"""
        if spec.technical_notes:
            prompt += f"""## Technical Notes

{spec.technical_notes}

"""

        prompt += f"""Based on the following feedback, please refine and improve this specification:

{feedback}

Generate an improved specification in the same Markdown format, addressing the feedback while maintaining clear structure. Make sure to include all sections: Overview, Requirements, Acceptance Criteria, Out of Scope, and Technical Notes if applicable."""

        return prompt

    def _format_list(self, items: list[str]) -> str:
        """Format a list of items as markdown bullet points.

        Args:
            items: List of items to format.

        Returns:
            Markdown-formatted list.
        """
        return "\n".join(f"- {item}" for item in items)

    async def interview(
        self,
        get_user_input: Callable[[], str] | Callable[[], Awaitable[str]],
        display_message: Callable[[str], None] | None = None,
        on_thinking_start: Callable[[], None] | None = None,
        on_thinking_end: Callable[[], None] | None = None,
    ) -> InterviewResult:
        """Conduct interactive interview to gather requirements.

        The agent asks one question at a time, waits for user response,
        and continues until it has enough information to generate a spec.

        Args:
            get_user_input: Callable that returns user's response string.
                Can be sync or async. This allows for testing and different input sources.
            display_message: Optional callable to display agent messages.
                If not provided, messages are only logged.
            on_thinking_start: Optional callback called when agent starts processing.
            on_thinking_end: Optional callback called when agent finishes processing.

        Returns:
            InterviewResult containing the generated Spec and conversation history.

        Raises:
            ValueError: If interview is cancelled or cannot complete.
        """
        logger.info("interview_start")
        conversation: list[InterviewMessage] = []

        # Get first question from agent
        first_prompt = (
            "Start the interview by asking the user what they want to build. Ask only ONE question."
        )
        if on_thinking_start:
            on_thinking_start()
        result = await self.client.execute(first_prompt)
        if on_thinking_end:
            on_thinking_end()

        if not result.success:
            raise ValueError(f"Failed to start interview: {result.error}")

        agent_message = result.output.strip()
        conversation.append(InterviewMessage(role="assistant", content=agent_message))

        if display_message:
            display_message(agent_message)

        logger.info("interview_question", question_num=1, question=agent_message[:100])

        question_count = 1

        while question_count < MAX_INTERVIEW_QUESTIONS:
            # Get user response (handle both sync and async callables)
            try:
                input_result = get_user_input()
                if asyncio.iscoroutine(input_result):
                    user_response = await input_result
                else:
                    user_response = input_result
            except (EOFError, KeyboardInterrupt) as e:
                logger.info("interview_cancelled", reason="user_interrupt")
                raise ValueError("Interview cancelled by user") from e

            if not user_response:
                continue  # Skip empty responses

            if user_response.lower() in ["quit", "exit", "/quit"]:
                logger.info("interview_cancelled", reason="user_quit")
                raise ValueError("Interview cancelled by user")

            conversation.append(InterviewMessage(role="user", content=user_response))
            logger.info("interview_user_response", response=user_response[:100])

            # Get next agent response
            prompt = self._build_interview_prompt(conversation)
            if on_thinking_start:
                on_thinking_start()
            result = await self.client.execute(prompt)
            if on_thinking_end:
                on_thinking_end()

            if not result.success:
                raise ValueError(f"Interview failed: {result.error}")

            agent_message = result.output.strip()

            # Check for ready signal
            if "[READY_TO_GENERATE]" in agent_message:
                logger.info(
                    "interview_ready_to_generate",
                    question_count=question_count,
                )
                if on_thinking_start:
                    on_thinking_start()
                spec = await self._generate_spec_from_interview(conversation)
                if on_thinking_end:
                    on_thinking_end()
                return InterviewResult(spec=spec, conversation=conversation)

            conversation.append(InterviewMessage(role="assistant", content=agent_message))
            question_count += 1

            if display_message:
                display_message(agent_message)

            logger.info(
                "interview_question",
                question_num=question_count,
                question=agent_message[:100],
            )

        # Max questions reached - force generation
        logger.warning(
            "interview_max_questions_reached",
            max_questions=MAX_INTERVIEW_QUESTIONS,
        )
        if on_thinking_start:
            on_thinking_start()
        spec = await self._generate_spec_from_interview(conversation)
        if on_thinking_end:
            on_thinking_end()
        return InterviewResult(spec=spec, conversation=conversation)

    def _build_interview_prompt(self, conversation: list[InterviewMessage]) -> str:
        """Build prompt with conversation history for next turn.

        Args:
            conversation: The conversation history so far.

        Returns:
            A formatted prompt for the agent.
        """
        # Format conversation as context
        conv_text = "\n\n".join(
            f"**{'You' if msg.role == 'assistant' else 'User'}**: {msg.content}"
            for msg in conversation
        )

        return f"""You are conducting an interactive interview to gather requirements for a feature specification.

Your goal is to create a specification detailed enough that a junior developer or Claude Haiku could implement it correctly without asking clarifying questions.

Here is the conversation so far:

{conv_text}

Based on the conversation, either:
1. Ask ONE follow-up question to gather more information, OR
2. If you are 95% confident you have complete information, respond with:

[READY_TO_GENERATE]
I have enough context to generate a specification for: <one-line summary>

Remember:
- Ask only ONE question at a time
- Build on the user's previous answers
- Cover ALL areas: core feature, users, data model, UI, business logic, edge cases, integrations, success criteria, constraints, scope boundaries
- Keep asking until you are 95% confident in completeness
- Don't assume - verify your understanding explicitly
- Think about what a junior developer would need to know"""

    async def _generate_spec_from_interview(self, conversation: list[InterviewMessage]) -> Spec:
        """Generate final spec from completed interview.

        Args:
            conversation: The full conversation history.

        Returns:
            A Spec object generated from the interview context.

        Raises:
            ValueError: If spec generation fails.
        """
        # Format conversation as context
        conv_text = "\n\n".join(
            f"**{'Assistant' if msg.role == 'assistant' else 'User'}**: {msg.content}"
            for msg in conversation
        )

        prompt = f"""Based on the following interview conversation, generate a complete feature specification.

## Interview Transcript

{conv_text}

## Instructions

Generate a specification in the exact Markdown format below. Include all sections:

# Feature: <Clear, descriptive title>

## Overview

<1-2 paragraphs explaining what the feature does and why it matters>

## Requirements

- <Specific, testable requirement 1>
- <Specific, testable requirement 2>
- <Specific, testable requirement 3>
(Include at least 3 requirements)

## Acceptance Criteria

- <Verifiable criterion 1>
- <Verifiable criterion 2>
- <Verifiable criterion 3>
(Include at least 3 criteria)

## Out of Scope

- <What is NOT included>
- <Another exclusion>
(Include at least 2 items)

## Technical Notes

<Optional: Implementation hints or constraints mentioned in the interview>"""

        logger.info("interview_generating_spec")
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Failed to generate spec from interview: {result.error}")

        spec = self._parse_spec_from_output(result.output)

        logger.info(
            "interview_spec_generated",
            title=spec.title,
            num_requirements=len(spec.requirements),
        )

        return spec
