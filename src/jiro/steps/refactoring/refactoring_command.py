"""Refactoring step command.

This command spawns a subagent to refactor implementation code via the
refactoring MCP.
The subagent is responsible for:
1. Refactoring the implementation code (no test changes)
2. Ensuring all tests still pass
3. Returning structured result with refactoring details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.refactoring.refactoring_result import RefactoringResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class RefactoringCommand(Command):
    """Command to spawn a subagent that refactors implementation code.

    The subagent will:
    - Call the refactoring MCP to refactor code
    - Ensure all tests still pass after refactoring
    - Return structured output with refactoring details and metrics
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = RefactoringResult

    def execute(self, *, step: PlanStep, task: Task) -> RefactoringResult:
        """Execute the refactoring command.

        Spawns a subagent to refactor code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            RefactoringResult with refactoring details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            with the refactoring MCP will be added when Agent SDK integration
            is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK and refactoring MCP
        raise NotImplementedError(
            "RefactoringCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK and refactoring MCP is pending."
        )
