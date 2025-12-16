"""Documentation step command.

This command spawns a subagent to improve documentation.
The subagent is responsible for:
1. Improving documentation in .md files or adding/updating docstrings/comments in code
2. Ensuring only documentation-related changes are made
3. Running verification to confirm changes are documentation-only
4. Returning structured result with documentation change details
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.documentation.documentation_result import DocumentationResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class DocumentationCommand(Command):
    """Command to spawn a subagent that improves documentation.

    The subagent will:
    - Improve existing documentation in .md files
    - Add or update docstrings and comments in Python files
    - Ensure all changes are documentation-only (no code changes)
    - Return structured output with documentation change details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = DocumentationResult

    def __init__(self, client: AgentClient) -> None:
        """Initialize DocumentationCommand.

        Args:
            client: AgentClient for executing the documentation agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> DocumentationResult:
        """Execute the documentation command.

        Spawns a subagent to improve documentation based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            DocumentationResult with documentation change details and subagent metrics

        Raises:
            ValueError: If the agent execution fails.
        """
        start_time = time.monotonic()

        # Build prompt for documentation agent
        prompt = self._build_documentation_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Documentation agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Categorize files
        doc_files = [f for f in changed_files if f.endswith(".md")]
        py_files = [f for f in changed_files if f.endswith(".py")]

        return DocumentationResult(
            changed_files=[Path(f) for f in changed_files],
            doc_files_changed=len(doc_files),
            py_files_changed=len(py_files),
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_documentation_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the documentation agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the documentation agent.
        """
        return f"""You are a documentation agent. Your task is to improve documentation
based on the following planning context.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or 'No description'}

## Step Instructions
{step.planning_context}

## Rules
1. ONLY modify documentation:
   - Markdown files (.md)
   - Docstrings in Python files (triple-quoted strings)
   - Comments in Python files (lines starting with #)
2. DO NOT modify any code logic
3. Follow the instructions exactly as specified
4. Stage your changes with `git add` but do NOT commit

Execute the documentation improvements now."""

    def _get_changed_files(self) -> list[str]:
        """Get list of changed files from git diff.

        Returns:
            List of file paths that have been modified.
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = output.stdout.strip().split("\n") if output.stdout.strip() else []
            return [f for f in files if f]  # Filter empty strings
        except subprocess.CalledProcessError:
            return []
