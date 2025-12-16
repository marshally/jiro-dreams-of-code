"""Test only step command.

This command spawns a subagent to add tests to existing code.
The subagent is responsible for:
1. Adding a new test to the test suite
2. Running the test to verify it passes
3. Returning structured result with test details
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.test.only.test_only_result import TestOnlyResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
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

    def __init__(self, client: AgentClient) -> None:
        """Initialize TestOnlyCommand.

        Args:
            client: AgentClient for executing the test agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> TestOnlyResult:
        """Execute the test only command.

        Spawns a subagent to add tests based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TestOnlyResult with test details and subagent metrics

        Raises:
            ValueError: If the agent execution fails.
        """
        start_time = time.monotonic()

        # Build prompt for test agent
        prompt = self._build_test_only_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Test only agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Convert to Path objects
        changed_paths = [Path(f) for f in changed_files]

        # Run tests to verify they pass and get test output
        test_specifier = self._get_test_specifier(changed_paths)
        test_output = self._run_tests(test_specifier)

        return TestOnlyResult(
            changed_files=changed_paths,
            test_specifier=test_specifier,
            test_output=test_output,
            test_files=changed_paths,
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_test_only_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the test only agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the test agent.
        """
        return f"""You are a test writing agent. Your task is to add tests to existing code
based on the following planning context.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or 'No description'}

## Step Instructions
{step.planning_context}

## Rules
1. ONLY add test files:
   - Create files in tests/ directory with test_ prefix or _test suffix
   - Must be .py files
   - Add tests for existing functionality, don't modify production code
2. Create exactly ONE test per commit
3. Write tests that verify existing code works correctly
4. Ensure tests PASS when run
5. Stage your changes with `git add` but do NOT commit

Execute the test addition now."""

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

    def _get_test_specifier(self, test_files: list[Path]) -> str:
        """Get pytest specifier for the test files.

        The specifier format is: path/to/test_file.py::test_name

        Args:
            test_files: List of test file paths

        Returns:
            pytest specifier string
        """
        if not test_files:
            raise ValueError("No test files found")

        # For now, assume one test file and try to extract test name
        test_file = test_files[0]

        # Get the first test name from the file
        try:
            with open(test_file) as f:
                content = f.read()
                # Find first test function
                import re

                match = re.search(r"def (test_\w+)\(", content)
                if match:
                    test_name = match.group(1)
                    return f"{test_file}::{test_name}"
        except Exception:
            pass

        # Fallback: run pytest with collection to find tests
        try:
            output = subprocess.run(
                ["python", "-m", "pytest", str(test_file), "--collect-only", "-q"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Parse output to get test names
            lines = output.stdout.strip().split("\n")
            if lines:
                # pytest output format is like: "tests/test_file.py::test_name"
                first_test = lines[0].strip()
                if "::" in first_test:
                    return first_test
        except Exception:
            pass

        # Final fallback
        return f"{test_file}::test"

    def _run_tests(self, test_specifier: str) -> str:
        """Run tests and return output.

        Args:
            test_specifier: pytest specifier (e.g., "tests/test_file.py::test_name")

        Returns:
            Output from pytest

        Raises:
            ValueError: If tests fail
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_specifier, "-xvs", "--tb=short"],
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr

            if result.returncode != 0:
                raise ValueError(
                    f"Tests failed (exit code {result.returncode})\n\nOutput:\n{output}"
                )

            return output
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to run tests: {e.stderr}") from e
