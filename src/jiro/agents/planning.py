"""PlanningAgent for creating execution plans from tasks."""

import re

import structlog
import yaml

from jiro.agents.client import AgentClient
from jiro.core.execution_plan import (
    ExecutionPlanSchema,
    ExecutionStep,
    FileAction,
)
from jiro.trackers.interface import Task

logger = structlog.get_logger()


class PlanningAgent:
    """Agent that creates execution plans for development tasks.

    Takes a task and produces a structured plan with specific steps,
    files, and verification commands. Uses Claude as the underlying LLM
    via AgentClient.
    """

    def __init__(self, client: AgentClient) -> None:
        """Initialize PlanningAgent.

        Args:
            client: AgentClient instance for executing the agent.

        Raises:
            TypeError: If client is None.
        """
        if client is None:
            raise TypeError("client cannot be None")
        self.client = client

    async def plan(self, task: Task) -> ExecutionPlanSchema:
        """Create an execution plan for a task.

        Takes a task from the issue tracker and produces a structured
        execution plan with specific steps, files, and verification commands.

        Args:
            task: The Task to create a plan for.

        Returns:
            An ExecutionPlanSchema object containing all steps and verification details.

        Raises:
            ValueError: If the agent execution fails.
        """
        logger.info(
            "planning_agent_plan_start",
            task_id=task.id,
            title=task.title,
        )

        # Build the prompt with task context
        prompt = self._build_planning_prompt(task)

        # Execute the agent with the task prompt
        result = await self.client.execute(prompt)

        # Check for errors
        if not result.success:
            logger.error(
                "planning_agent_plan_failed",
                error=result.error,
                task_id=task.id,
            )
            raise ValueError(f"Agent execution failed: {result.error}")

        # Parse the output into an ExecutionPlanSchema
        execution_plan = self._parse_plan_from_output(result.output, task.id)

        # Calculate token usage
        estimated_tokens = result.tokens_after - result.tokens_before
        execution_plan.estimated_tokens = estimated_tokens

        logger.info(
            "planning_agent_plan_success",
            task_id=task.id,
            num_steps=len(execution_plan.steps),
            tokens_used=estimated_tokens,
        )

        return execution_plan

    def _build_planning_prompt(self, task: Task) -> str:
        """Build a prompt for planning a task.

        Args:
            task: The Task to create a prompt for.

        Returns:
            A formatted prompt for the planning agent.
        """
        # Valid step types matching commit types
        step_types = "docs, tdd_red, tdd_green, tdd_refactor, lint_fix, bug_fix, config, test_only, performance"

        prompt = f"""You are a planning agent that creates detailed execution plans for software development tasks.

## Task to Plan

Task ID: {task.id}
Title: {task.title}
Type: {task.task_type}
Status: {task.status}
Priority: {task.priority if task.priority else "Not specified"}

Description:
{task.description if task.description else "No description provided"}

Labels: {", ".join(task.labels) if task.labels else "None"}

## Your Task

Create a detailed execution plan for this task. Produce your response in YAML format with the following structure:

```yaml
task_id: "{task.id}"

steps:
  - description: "What this step accomplishes"
    step_type: "docs"  # One of: {step_types}
    files:
      - path: "src/path/to/file.py"
        action: "create"  # One of: create, modify, delete
        content_hints: "Brief description of what to add/change"
        location: "function name() or line 42"  # Optional: where in the file
    verification_command: "pytest tests/unit/test_file.py"  # Command to verify this step

  - description: "Second step"
    step_type: "tdd_red"
    files:
      - path: "tests/test_foo.py"
        action: "create"
        content_hints: "Add failing test for feature X"
    verification_command: "pytest tests/test_foo.py"
```

## Step Type Guidelines

- **docs**: Documentation-only changes (README, docstrings, comments)
- **tdd_red**: Write failing tests first (test file changes only)
- **tdd_green**: Implement minimal code to pass tests (source file changes)
- **tdd_refactor**: Refactor code while keeping tests passing
- **lint_fix**: Fix linting errors (single error per step)
- **bug_fix**: Fix a specific bug
- **config**: Configuration file changes
- **test_only**: Add tests to existing code
- **performance**: Optimization changes

## Definition of Done

Each step must be COMPLETE and SHIPPABLE on its own. This means:
- Tests pass
- Linting passes
- Code is documented (if public API)

NEVER create separate phases for testing, linting, or documentation. These are part of every task's definition of done, not separate steps.

**Anti-patterns to AVOID:**
- ❌ "Step 5: Write tests for features"
- ❌ "Step 6: Run linting and fix errors"
- ❌ "Step 7: Add documentation"
- ❌ A "testing phase" at the end
- ❌ A "linting phase" at the end
- ❌ A "documentation phase" at the end

**Correct patterns:**
- ✅ Each tdd_red step writes a failing test
- ✅ Each tdd_green step makes the test pass AND linting passes
- ✅ Documentation is added in the same step as the code it documents

## Guidelines

- Be specific about file paths (use exact, real paths)
- Each step should be small enough to complete in one commit
- Include test creation/modification as separate tdd_red steps
- Use tdd_green for implementation that makes tests pass
- Steps should be ordered logically
- Each step must have a verification_command that can be run
- For documentation tasks, use step_type: "docs"
- The files list should include ALL files that will be touched in that step

Generate the execution plan for this task now."""

        return prompt

    def _parse_plan_from_output(self, output: str, task_id: str) -> ExecutionPlanSchema:
        """Parse agent output into an ExecutionPlanSchema.

        Extracts the YAML-formatted plan from the agent's output and
        converts it into structured ExecutionPlanSchema.

        Args:
            output: The agent's text output containing the plan.
            task_id: The task ID for fallback reference.

        Returns:
            An ExecutionPlanSchema with parsed steps.

        Raises:
            ValueError: If the output doesn't contain valid YAML plan.
        """
        # Extract YAML block from output
        yaml_match = re.search(r"```yaml\s*(.*?)\s*```", output, re.DOTALL)
        yaml_content = yaml_match.group(1) if yaml_match else output

        # Parse YAML
        try:
            plan_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML from output: {str(e)}") from e

        if not plan_data:
            raise ValueError("Output doesn't contain a valid execution plan")

        # Extract task_id (use provided task_id if not in output)
        extracted_task_id = plan_data.get("task_id", task_id)

        # Parse steps into ExecutionStep objects
        steps = []
        steps_data = plan_data.get("steps", [])
        for step_data in steps_data:
            files = self._extract_files_from_step(step_data)
            step_type = step_data.get("step_type", "tdd_green")
            verification_command = step_data.get("verification_command")

            step = ExecutionStep(
                description=step_data.get("description", ""),
                step_type=step_type,
                files=files,
                verification_command=verification_command,
            )
            steps.append(step)

        if not steps:
            raise ValueError("Output doesn't contain any execution steps")

        return ExecutionPlanSchema(
            task_id=extracted_task_id,
            steps=steps,
        )

    def _extract_files_from_step(self, step_data: dict) -> list[FileAction]:
        """Extract FileAction objects from a step.

        Args:
            step_data: The step data dictionary.

        Returns:
            A list of FileAction objects from the step.
        """
        files = []
        files_data = step_data.get("files", [])

        if isinstance(files_data, list):
            for file_item in files_data:
                if isinstance(file_item, dict):
                    path = file_item.get("path")
                    if path:
                        action = file_item.get("action", "modify")
                        content_hints = file_item.get("content_hints")
                        location = file_item.get("location")
                        files.append(
                            FileAction(
                                path=path,
                                action=action,
                                content_hints=content_hints,
                                location=location,
                            )
                        )
                elif isinstance(file_item, str):
                    # Legacy format: just a path string
                    files.append(FileAction(path=file_item, action="modify"))

        return files
