"""TDD refactor step command.

This command spawns a subagent to refactor implementation code.
The subagent is responsible for:
1. Refactoring the implementation code (no test changes)
2. Ensuring all tests still pass
3. Returning structured result with refactoring details
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
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

    def __init__(self, client: AgentClient | None = None) -> None:
        """Initialize TddRefactorCommand.

        Args:
            client: AgentClient for executing the TDD refactor agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> TddRefactorResult:
        """Execute the TDD refactor command.

        Spawns a subagent to refactor code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddRefactorResult with refactoring details and subagent metrics

        Raises:
            ValueError: If the agent execution fails or client is not set.
        """
        if self.client is None:
            raise ValueError("AgentClient not configured for TddRefactorCommand")

        start_time = time.monotonic()

        # Build prompt for TDD refactor agent
        prompt = self._build_tdd_refactor_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"TDD refactor agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Run tests to verify they pass
        test_output = self._run_tests()

        # Extract refactoring type from agent output
        refactoring_type = self._extract_refactoring_type(result.output)

        # Generate checksum (placeholder for now - actual MCP integration later)
        checksum = self._generate_checksum(changed_files)

        return TddRefactorResult(
            changed_files=[Path(f) for f in changed_files],
            test_specifier="",  # Not needed for refactor step since all tests are run
            test_output=test_output,
            refactoring_type=refactoring_type,
            checksum=checksum,
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_tdd_refactor_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the TDD refactor agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the TDD refactor agent.
        """
        return f"""You are a TDD (Test-Driven Development) refactoring agent. Your task is to refactor implementation code to improve maintainability, readability, or performance while preserving all test behavior.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or "No description"}

## Step Instructions
{step.planning_context}

## Rules
1. Refactor ONLY implementation code - do NOT modify test files
2. Make behavior-neutral improvements (extract methods, rename variables, etc.)
3. DO NOT change any public APIs or behavior
4. Run tests to verify they still pass after refactoring
5. Stage your changes with `git add` but do NOT commit
6. Provide a summary of the refactoring improvements

Execute the TDD refactor step now."""

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

    def _run_tests(self) -> str:
        """Run all tests to verify refactoring doesn't break anything.

        Returns:
            The output from running the tests
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error running tests: {str(e)}"

    def _extract_refactoring_type(self, agent_output: str) -> str:
        """Extract the type of refactoring from agent output.

        Args:
            agent_output: The output from the refactor agent

        Returns:
            The refactoring type (e.g., "extract_method", "rename_variables")
        """
        # Look for common refactoring patterns in agent output
        patterns = [
            (r"extract.*method", "extract_method"),
            (r"rename.*variable", "rename_variables"),
            (r"consolidate.*duplicate", "consolidate_duplicates"),
            (r"simplif[y|ied]", "simplify"),
            (r"optimize.*performance", "optimize_performance"),
            (r"improve.*readability", "improve_readability"),
        ]

        for pattern, refactoring_type in patterns:
            if re.search(pattern, agent_output, re.IGNORECASE):
                return refactoring_type

        # Default to generic refactoring type
        return "code"

    def _generate_checksum(self, changed_files: list[str]) -> str:
        """Generate a checksum for refactored files (placeholder).

        Args:
            changed_files: List of changed files

        Returns:
            A checksum string (placeholder for MCP integration)
        """
        # In the future, this will call the refactoring MCP to verify
        # behavior is preserved. For now, we return a placeholder.
        # The checksum can be a hash of the file contents or MCP verification token.
        if not changed_files:
            return "no_changes"

        # Generate a simple placeholder checksum
        return f"refactor_verified_{len(changed_files)}_files"
