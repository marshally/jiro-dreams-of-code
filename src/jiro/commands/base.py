"""Command ABC for step execution.

This module provides the abstract base class for all step commands.
Commands are responsible for spawning subagents to perform the actual work.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from jiro.results.base import Result
from jiro.steps.types import PlanStep
from jiro.trackers.interface import Task


class Command(ABC):
    """Base class for step commands that spawn subagents.

    Each step type has a corresponding Command subclass that knows how to:
    - Configure the tools available to the subagent
    - Define the expected output schema
    - Execute the command by spawning a subagent

    Class Attributes:
        tools: List of tool classes available to the subagent
        output_schema: Pydantic/dataclass model for structured output
    """

    tools: ClassVar[list[type]]
    output_schema: ClassVar[type]

    @abstractmethod
    async def execute(self, *, step: PlanStep, task: Task) -> Result:
        """Execute the command, spawning a subagent to do the work.

        Args:
            step: The plan step containing step type and planning context
            task: The task being executed

        Returns:
            A Result (or subclass) containing the outcome of the execution
        """
        ...
