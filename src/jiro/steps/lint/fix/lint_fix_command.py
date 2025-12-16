"""Lint fix step command.

This command spawns a subagent to fix a lint error in a single file.
The subagent is responsible for:
1. Identifying the lint error
2. Applying the fix
3. Verifying the file passes lint
4. Returning structured result with error code and filename
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.lint.fix.lint_fix_result import LintFixResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class LintFixCommand(Command):
    """Command to spawn a subagent that fixes a lint error.

    The subagent will:
    - Identify the specific lint error
    - Apply the fix to the file
    - Run the linter to verify the fix
    - Return structured output with error code and filename
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = LintFixResult

    def __init__(self, client: AgentClient) -> None:
        """Initialize LintFixCommand.

        Args:
            client: AgentClient for executing the lint fix agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> LintFixResult:
        """Execute the lint fix command.

        Spawns a subagent to fix a lint error based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            LintFixResult with error code, filename, and changed files

        Raises:
            ValueError: If the agent execution fails.
        """
        # Build prompt for lint fix agent
        prompt = self._build_lint_fix_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Lint fix agent execution failed: {result.error}")

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Extract error code and filename from the prompt context
        # These will be parsed from the planning_context or result
        error_code = self._extract_error_code(result.output)
        filename = self._extract_filename(result.output, changed_files)

        return LintFixResult(
            changed_files=[Path(f) for f in changed_files],
            error_code=error_code,
            filename=filename,
        )

    def _build_lint_fix_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the lint fix agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the lint fix agent.
        """
        return f"""You are a lint fix agent. Your task is to fix a lint error
based on the following planning context.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or 'No description'}

## Step Instructions
{step.planning_context}

## Rules
1. Fix only ONE lint error
2. Make minimal changes to fix the error
3. Verify the file passes linting after the fix
4. Stage your changes with `git add` but do NOT commit
5. Report the error code (e.g., E501, W503) and filename

Execute the lint fix now."""

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

    @staticmethod
    def _extract_error_code(output: str) -> str:
        """Extract error code from agent output.

        Looks for patterns like "E501", "W503", etc.

        Args:
            output: The agent output.

        Returns:
            The error code or "unknown" if not found.
        """
        # Look for standard error code patterns (e.g., E501, W503, C901)
        match = re.search(r"[EWC]\d{3}", output)
        if match:
            return match.group(0)
        return "unknown"

    @staticmethod
    def _extract_filename(output: str, changed_files: list[str]) -> str:
        """Extract filename from agent output or changed files.

        Args:
            output: The agent output.
            changed_files: List of changed files from git diff.

        Returns:
            The filename or "unknown" if not found.
        """
        # If we have exactly one changed file, use that
        if changed_files and len(changed_files) == 1:
            return changed_files[0]

        # Look for file paths in output
        paths = re.findall(r"['\"]?([a-zA-Z0-9_/\-.]+\.py)['\"]?", output)
        if paths:
            result = paths[0]
            if isinstance(result, str):
                return result

        return "unknown"
