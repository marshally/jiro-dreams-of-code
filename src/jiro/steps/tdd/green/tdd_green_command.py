"""TDD green step command.

This command spawns a subagent to implement code that makes a test pass.
The subagent is responsible for:
1. Implementing the feature to make the failing test pass
2. Running the test to verify it passes (without skip decorator)
3. Returning structured result with implementation details
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.green.tdd_green_result import TddGreenResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
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

    def __init__(self, client: AgentClient | None = None) -> None:
        """Initialize TddGreenCommand.

        Args:
            client: AgentClient for executing the TDD green agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> TddGreenResult:
        """Execute the TDD green command.

        Spawns a subagent to implement code based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddGreenResult with implementation details and subagent metrics

        Raises:
            ValueError: If the agent execution fails or client is not set.
        """
        if self.client is None:
            raise ValueError("AgentClient not configured for TddGreenCommand")

        start_time = time.monotonic()

        # Build prompt for TDD green agent
        prompt = self._build_tdd_green_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"TDD green agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Extract test specifier from the planning context or agent output
        test_specifier = self._extract_test_specifier(step, changed_files)

        # Run the test to capture output
        test_output = self._run_test(test_specifier)

        return TddGreenResult(
            changed_files=[Path(f) for f in changed_files],
            test_specifier=test_specifier,
            test_output=test_output,
            implementation_files=[Path(f) for f in changed_files],
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_tdd_green_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the TDD green agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the TDD green agent.
        """
        return f"""You are a TDD (Test-Driven Development) agent. Your task is to implement code that makes a failing test pass.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or 'No description'}

## Step Instructions
{step.planning_context}

## Rules
1. Implement the minimal code necessary to make the test pass (no over-engineering)
2. Do NOT modify the test file - only implement code in production files
3. Remove @pytest.mark.skip decorator from the test
4. Ensure the test uses pytest syntax and runs with: python -m pytest <test_specifier> -xvs
5. Stage your changes with `git add` but do NOT commit
6. Return a summary of the implementation

Execute the TDD green step now."""

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

    def _extract_test_specifier(self, step: PlanStep, changed_files: list[str]) -> str:
        """Extract test specifier from planning context.

        Args:
            step: The plan step containing planning context
            changed_files: List of changed files from git

        Returns:
            Test specifier (e.g., "tests/test_auth.py::test_login")

        Raises:
            ValueError: If test specifier cannot be extracted
        """
        # Try to extract test specifier from planning context
        # Look for patterns like "tests/test_xxx.py::test_yyy"
        context = step.planning_context

        # Pattern 1: Look for explicit test specifier in context
        match = re.search(r"tests/[^\s:]+\.py::\w+", context)
        if match:
            return match.group(0)

        # Pattern 2: Look for test file and test name separately
        # Find all test_* patterns and use the longest match for test name
        test_match = re.search(r"test[_\w]*\.py", context)
        test_name_matches = list(re.finditer(r"test_\w+", context))

        if test_match and test_name_matches:
            test_file = test_match.group(0)
            # Use the longest match as it's likely the most specific test name
            test_name = max(test_name_matches, key=lambda m: len(m.group(0))).group(0)
            return f"tests/{test_file}::{test_name}"

        # If no explicit specifier found, look in git changes for test files
        test_files = [f for f in changed_files if f.startswith("tests/") and f.endswith(".py")]
        if not test_files:
            raise ValueError("Could not find test specifier in planning context or changed files")

        # Extract test name from test file if it exists
        try:
            test_file_path = Path(test_files[0])
            content = test_file_path.read_text()
            match = re.search(r"def\s+(test_\w+)\s*\(", content)
            if match:
                test_name = match.group(1)
                return f"{test_files[0]}::{test_name}"
        except Exception:
            pass

        raise ValueError(f"Could not extract test specifier from {test_files[0]}")

    def _run_test(self, test_specifier: str) -> str:
        """Run the test and capture output.

        Args:
            test_specifier: The pytest specifier (e.g., tests/test_auth.py::test_login)

        Returns:
            The output from running the test
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_specifier, "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error running test: {str(e)}"
