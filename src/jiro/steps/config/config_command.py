"""Config step command.

This command spawns a subagent to modify configuration files.
The subagent is responsible for:
1. Modifying configuration files (.yaml, .toml, .json, .ini, etc.)
2. Ensuring only config files are changed
3. Running verification to confirm changes are config-only
4. Returning structured result with config change details
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.config.config_result import ConfigResult

if TYPE_CHECKING:
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class ConfigCommand(Command):
    """Command to spawn a subagent that modifies configuration files.

    The subagent will:
    - Modify configuration files based on planning context
    - Ensure all changes are config-only (no code changes)
    - Return structured output with config change details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = ConfigResult

    def execute(self, *, step: PlanStep, task: Task) -> ConfigResult:
        """Execute the config command.

        Spawns a subagent to modify configuration files based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            ConfigResult with config change details and subagent metrics

        Note:
            This is a placeholder implementation. Full subagent integration
            will be added when Agent SDK integration is ready.
        """
        # Placeholder implementation for now
        # TODO: Implement subagent spawning with Agent SDK
        raise NotImplementedError(
            "ConfigCommand.execute() is not yet implemented. "
            "Subagent integration via Agent SDK is pending."
        )
