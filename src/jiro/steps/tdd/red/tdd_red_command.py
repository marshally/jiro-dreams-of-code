"""TDD red step command.

This command spawns a subagent to create a failing test.
The subagent is responsible for:
1. Creating the failing test
2. Running the test to verify it fails
3. Marking the test with @pytest.mark.skip(reason="TDD red: awaiting implementation")
4. Returning structured result with test details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.red.tdd_red_result import TddRedResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class TddRedCommand(Command):
    """Command to spawn a subagent that creates a failing test.

    The subagent will:
    - Create a test file (or add to existing test file)
    - Write a failing test case
    - Run the test to verify it fails
    - Mark the test with @pytest.mark.skip
    - Return structured output with test details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = TddRedResult

    def execute(self, *, step: PlanStep, task: Task) -> TddRedResult:
        """Execute the TDD red command.

        Spawns a subagent to create a failing test based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddRedResult with test details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "TddRedCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
