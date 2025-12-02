"""DreamingAgent for generating feature specifications from prompts."""

import structlog

from jiro.agents.client import AgentClient
from jiro.core.planner import (
    Spec,
    _extract_list_section,
    _extract_section,
    _extract_title,
)

logger = structlog.get_logger()


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
