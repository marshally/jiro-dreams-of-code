"""Test only step command.

This command spawns a subagent to add tests to existing code.
The subagent is responsible for:
1. Adding a new test to the test suite
2. Running the test to verify it passes
3. Returning structured result with test details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.test.only.test_only_result import TestOnlyResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class TestOnlyCommand(Command):
    """Command to spawn a subagent that adds tests to existing code.

    The subagent will:
    - Add a new test to the test suite
    - Run the test to verify it passes
    - Return structured output with test details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = TestOnlyResult

    def execute(self, *, step: PlanStep, task: Task) -> TestOnlyResult:
        """Execute the test only command.

        Spawns a subagent to add tests based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TestOnlyResult with test details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "TestOnlyCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
