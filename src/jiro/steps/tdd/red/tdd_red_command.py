"""TDD red step command.

This command spawns a subagent to create a failing test.
The subagent is responsible for:
1. Creating the failing test
2. Running the test to verify it fails
3. Marking the test with @pytest.mark.skip(reason="TDD red: awaiting implementation")
4. Returning structured result with test details
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.tdd.red.tdd_red_result import TddRedResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
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

    def __init__(self, client: AgentClient | None = None) -> None:
        """Initialize TddRedCommand.

        Args:
            client: AgentClient for executing the TDD red agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> TddRedResult:
        """Execute the TDD red command.

        Spawns a subagent to create a failing test based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            TddRedResult with test details and subagent metrics

        Raises:
            ValueError: If the agent execution fails or client is not set.
        """
        if self.client is None:
            raise ValueError("AgentClient not configured for TddRedCommand")

        start_time = time.monotonic()

        # Build prompt for TDD red agent
        prompt = self._build_tdd_red_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"TDD red agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Extract test file and test name from the agent output
        test_file, test_name, test_specifier = self._extract_test_details(
            result.output, changed_files
        )

        # Run the test to capture output
        test_output = self._run_test(test_specifier)

        return TddRedResult(
            changed_files=[Path(f) for f in changed_files],
            test_file=test_file,
            test_name=test_name,
            test_specifier=test_specifier,
            test_output=test_output,
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_tdd_red_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the TDD red agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the TDD red agent.
        """
        return f"""You are a TDD (Test-Driven Development) agent. Your task is to create a failing test.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or "No description"}

## Step Instructions
{step.planning_context}

## Rules
1. Create a test file in the tests/ directory (e.g., tests/test_<feature>.py)
2. Write a test that WILL FAIL when executed (the implementation doesn't exist yet)
3. Include @pytest.mark.skip(reason="TDD red: awaiting implementation") above the test function
4. Ensure the test uses pytest syntax and runs with: python -m pytest <test_specifier> -xvs
5. Stage your changes with `git add` but do NOT commit
6. Include a summary comment in the test file with the test name and specifier

Execute the TDD red step now."""

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

    def _extract_test_details(
        self, agent_output: str, changed_files: list[str]
    ) -> tuple[Path, str, str]:
        """Extract test file, test name, and test specifier from agent output and files.

        Args:
            agent_output: The output from the agent
            changed_files: List of changed files from git

        Returns:
            Tuple of (test_file Path, test_name, test_specifier)

        Raises:
            ValueError: If test details cannot be extracted
        """
        # Find test files in changed_files
        test_files = [f for f in changed_files if f.startswith("tests/") and f.endswith(".py")]

        if not test_files:
            raise ValueError("No test files found in changed files")

        # Use the first test file
        test_file_path = Path(test_files[0])

        # Try to extract test name from agent output
        # Look for patterns like "test_xxx" in the output
        test_name = None

        # Pattern 1: Look for "def test_" in output
        match = re.search(r"def\s+(test_\w+)\s*\(", agent_output)
        if match:
            test_name = match.group(1)

        # Pattern 2: Look for "Test name: " pattern
        if not test_name:
            match = re.search(r"[Tt]est\s+name:?\s+(\w+)", agent_output)
            if match:
                test_name = match.group(1)

        # Pattern 3: Extract from file content
        if not test_name:
            try:
                content = test_file_path.read_text()
                match = re.search(r"def\s+(test_\w+)\s*\(", content)
                if match:
                    test_name = match.group(1)
            except Exception:
                pass

        if not test_name:
            raise ValueError("Could not extract test name from agent output or test file")

        # Build test specifier
        test_specifier = f"{test_files[0]}::{test_name}"

        return test_file_path, test_name, test_specifier

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
