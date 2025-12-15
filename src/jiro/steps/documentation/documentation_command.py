"""Documentation step command.

This command spawns a subagent to improve documentation.
The subagent is responsible for:
1. Improving documentation in .md files or adding/updating docstrings/comments in code
2. Ensuring only documentation-related changes are made
3. Running verification to confirm changes are documentation-only
4. Returning structured result with documentation change details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.documentation.documentation_result import DocumentationResult

if TYPE_CHECKING:
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

    def execute(self, *, step: PlanStep, task: Task) -> DocumentationResult:
        """Execute the documentation command.

        Spawns a subagent to improve documentation based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            DocumentationResult with documentation change details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "DocumentationCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
