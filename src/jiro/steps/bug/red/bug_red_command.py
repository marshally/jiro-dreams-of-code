"""Bug red step command.

This command spawns a subagent to create a failing test that reproduces the bug.
The subagent is responsible for:
1. Creating a test that reproduces the bug
2. Running the test to verify it fails (proving the bug exists)
3. Marking the test with @pytest.mark.skip(reason="Bug red: awaiting fix")
4. Returning structured result with test details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.bug.red.bug_red_result import BugRedResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class BugRedCommand(Command):
    """Command to spawn a subagent that creates a failing bug reproduction test.

    The subagent will:
    - Create a test file (or add to existing test file)
    - Write a test case that reproduces the bug
    - Run the test to verify it fails (proves the bug exists)
    - Mark the test with @pytest.mark.skip
    - Return structured output with test details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = BugRedResult

    def execute(self, *, step: PlanStep, task: Task) -> BugRedResult:
        """Execute the bug red command.

        Spawns a subagent to create a failing test that reproduces the bug based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            BugRedResult with test details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "BugRedCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
