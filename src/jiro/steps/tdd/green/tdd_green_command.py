"""TDD green step command.

This command spawns a subagent to implement code that makes a test pass.
The subagent is responsible for:
1. Implementing the feature to make the failing test pass
2. Running the test to verify it passes (without skip decorator)
3. Returning structured result with implementation details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.green.tdd_green_result import TddGreenResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class TddGreenCommand(Command):
    """Command to spawn a subagent that implements code to make test pass.

    The subagent will:
    - Implement the feature to make the failing test pass
    - Run the test to verify it passes
    - Return structured output with implementation details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = TddGreenResult

    def execute(self, *, step: PlanStep, task: Task) -> TddGreenResult:
        """Execute the TDD green command.

        Spawns a subagent to implement code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddGreenResult with implementation details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "TddGreenCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
