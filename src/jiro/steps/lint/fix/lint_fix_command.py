"""Lint fix step command.

This command spawns a subagent to fix a lint error in a single file.
The subagent is responsible for:
1. Identifying the lint error
2. Applying the fix
3. Verifying the file passes lint
4. Returning structured result with error code and filename
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.lint.fix.lint_fix_result import LintFixResult

if TYPE_CHECKING:
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

    def execute(self, *, step: PlanStep, task: Task) -> LintFixResult:
        """Execute the lint fix command.

        Spawns a subagent to fix a lint error based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            LintFixResult with error code, filename, and changed files

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "LintFixCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
