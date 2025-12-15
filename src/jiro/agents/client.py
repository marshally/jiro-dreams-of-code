"""AgentClient wrapper for Claude Agent SDK."""

import uuid
from datetime import datetime

import structlog
from claude_agent_sdk import query
from claude_agent_sdk.types import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
)

from jiro.agents.base import AgentConfig, AgentResult
from jiro.db.models import Prompt
from jiro.db.repository import PromptRepository

logger = structlog.get_logger()


class AgentClient:
    """Wrapper for Claude Agent SDK with context tracking and result storage.

    Provides a clean interface for executing agents while tracking token usage
    and storing results in the database for auditing and analysis.
    """

    def __init__(self, config: AgentConfig, repository: PromptRepository) -> None:
        """Initialize AgentClient.

        Args:
            config: Agent configuration.
            repository: PromptRepository for storing execution results.

        Raises:
            TypeError: If config or repository are None.
        """
        if config is None:
            raise TypeError("config cannot be None")
        if repository is None:
            raise TypeError("repository cannot be None")

        self.config = config
        self.repository = repository

    async def execute(self, prompt: str) -> AgentResult:
        """Execute an agent with the given prompt.

        Tracks token usage before and after execution, captures output,
        and stores results in the database for auditing.

        Args:
            prompt: The prompt to send to the agent.

        Returns:
            AgentResult containing success status, output, and token usage.
        """
        try:
            # Log execution start
            logger.info(
                "agent_execution_start",
                prompt=prompt,
                model=self.config.model,
            )

            # Track tokens before execution
            tokens_before = self._estimate_tokens(prompt)

            # Configure options for Claude Agent SDK
            options = ClaudeAgentOptions(
                model=self.config.model,
                system_prompt=self.config.system_prompt,
            )

            # Execute using Claude Agent SDK and collect text output
            output_parts: list[str] = []
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            output_parts.append(block.text)
                elif isinstance(message, ResultMessage) and message.result:
                    # ResultMessage indicates completion with result text
                    output_parts.append(message.result)

            output = "".join(output_parts)

            # Track tokens after execution
            tokens_after = tokens_before + self._estimate_tokens(output)

            # Log successful execution
            logger.info(
                "agent_execution_success",
                prompt=prompt,
                output_length=len(output),
                tokens_before=tokens_before,
                tokens_after=tokens_after,
            )

            # Create and store the result
            result = AgentResult(
                success=True,
                output=output,
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                error=None,
            )

            # Store in database
            self._store_result(prompt, result)

            return result

        except Exception as e:
            # Log the error
            error_message = str(e)
            logger.error(
                "agent_execution_error",
                prompt=prompt,
                error=error_message,
                error_type=type(e).__name__,
            )

            # Track tokens even on error
            tokens_before = self._estimate_tokens(prompt)
            tokens_after = tokens_before

            # Create error result
            result = AgentResult(
                success=False,
                output="",
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                error=error_message,
            )

            # Store error result
            self._store_result(prompt, result)

            return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text using rough heuristic.

        Args:
            text: The text to estimate tokens for.

        Returns:
            Estimated token count.
        """
        # Rough estimation: 1 token per 4 characters
        # In production, use the Anthropic token counter
        return max(1, len(text) // 4)

    def _store_result(self, prompt: str, result: AgentResult) -> None:
        """Store execution result in the database.

        Args:
            prompt: The prompt that was executed.
            result: The AgentResult to store.
        """
        try:
            prompt_record = Prompt(
                id=str(uuid.uuid4()),
                agent_type="execution",  # Default to execution agent
                prompt_text=prompt,
                model=self.config.model,
                tokens_before=result.tokens_before,
                tokens_after=result.tokens_after,
                created_at=datetime.now(),
                session_id=None,
                task_id=None,
            )

            self.repository.create(prompt_record)

            logger.info(
                "agent_result_stored",
                prompt_id=prompt_record.id,
                success=result.success,
            )
        except Exception as e:
            logger.error(
                "agent_result_storage_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
