"""TDD refactor step command.

This command spawns a subagent to refactor implementation code.
The subagent is responsible for:
1. Refactoring the implementation code (no test changes)
2. Ensuring all tests still pass
3. Returning structured result with refactoring details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class TddRefactorCommand(Command):
    """Command to spawn a subagent that refactors implementation code.

    The subagent will:
    - Refactor the implementation code to improve maintainability
    - Ensure all tests still pass after refactoring
    - Return structured output with refactoring details and metrics
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = TddRefactorResult

    def execute(self, *, step: PlanStep, task: Task) -> TddRefactorResult:
        """Execute the TDD refactor command.

        Spawns a subagent to refactor code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddRefactorResult with refactoring details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "TddRefactorCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
