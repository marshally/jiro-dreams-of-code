"""Bug green step command.

This command spawns a subagent to implement code that fixes a bug.
The subagent is responsible for:
1. Implementing the fix to make the failing test pass
2. Running the test to verify it passes (without skip decorator)
3. Returning structured result with implementation details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.bug.green.bug_green_result import BugGreenResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class BugGreenCommand(Command):
    """Command to spawn a subagent that implements code to fix the bug.

    The subagent will:
    - Implement the fix to make the failing test pass
    - Run the test to verify it passes
    - Return structured output with implementation details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = BugGreenResult

    def execute(self, *, step: PlanStep, task: Task) -> BugGreenResult:
        """Execute the bug green command.

        Spawns a subagent to implement code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            BugGreenResult with implementation details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "BugGreenCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
