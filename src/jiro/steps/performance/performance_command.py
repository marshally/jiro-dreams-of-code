"""Performance step command.

This command spawns a subagent to optimize code for performance.
The subagent is responsible for:
1. Analyzing code for performance optimization opportunities
2. Implementing optimizations
3. Ensuring all tests still pass
4. Returning structured result with performance details
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.performance.performance_result import PerformanceResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class PerformanceCommand(Command):
    """Command to spawn a subagent that optimizes code for performance.

    The subagent will:
    - Analyze code for performance optimization opportunities
    - Implement performance optimizations
    - Ensure all tests still pass after optimization
    - Return structured output with performance details and metrics
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = PerformanceResult

    def __init__(self, client: AgentClient | None = None) -> None:
        """Initialize PerformanceCommand.

        Args:
            client: Optional AgentClient for executing the performance agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> PerformanceResult:
        """Execute the performance command.

        Spawns a subagent to optimize code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            PerformanceResult with performance optimization details and subagent metrics

        Raises:
            ValueError: If the agent execution fails or client is not initialized.
        """
        if self.client is None:
            raise ValueError("PerformanceCommand requires an AgentClient to execute")

        start_time = time.monotonic()

        # Build prompt for performance agent
        prompt = self._build_performance_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Performance agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Run the test and capture output
        test_output = self._run_tests()
        test_specifier = self._get_test_specifier()

        return PerformanceResult(
            changed_files=[Path(f) for f in changed_files],
            test_specifier=test_specifier,
            test_output=test_output,
            benchmark_data=None,
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_performance_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the performance agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the performance agent.
        """
        return f"""You are a performance optimization agent. Your task is to optimize code for better performance
based on the following planning context.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or "No description"}

## Step Instructions
{step.planning_context}

## Rules
1. Focus on performance optimization:
   - Improve algorithmic efficiency
   - Optimize data structures
   - Reduce unnecessary computations
   - Cache/memoize expensive operations
   - Improve I/O efficiency
2. Ensure all existing tests still pass after optimization
3. DO NOT change the public API or behavior - only optimize implementation
4. Stage your changes with `git add` but do NOT commit
5. Make minimal, focused changes for the optimization

Execute the performance optimization now."""

    def _get_changed_files(self) -> list[str]:
        """Get list of changed files from git diff.

        Returns:
            List of file paths that have been modified.
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = output.stdout.strip().split("\n") if output.stdout.strip() else []
            return [f for f in files if f]  # Filter empty strings
        except subprocess.CalledProcessError:
            return []

    def _get_test_specifier(self) -> str:
        """Get the test specifier from pytest discovery.

        Returns:
            A pytest specifier string (e.g., "tests/test_perf.py::test_cache_speed").
        """
        # Find relevant test files
        try:
            output = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                check=False,
            )
            # Extract first test from collection
            lines = output.stdout.strip().split("\n")
            for line in lines:
                if "::" in line and line.strip():
                    return line.strip()
            return "tests/"  # Fallback to tests directory
        except Exception:
            return "tests/"

    def _run_tests(self) -> str:
        """Run tests and capture output.

        Returns:
            The test output showing passing tests.
        """
        try:
            result_proc = subprocess.run(
                ["python", "-m", "pytest", "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            return result_proc.stdout + result_proc.stderr
        except Exception:
            return ""
