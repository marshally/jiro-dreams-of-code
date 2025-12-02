"""PlanningAgent for creating execution plans from tasks."""

import re
from dataclasses import dataclass

import structlog
import yaml

from jiro.agents.client import AgentClient
from jiro.trackers.interface import Task

logger = structlog.get_logger()


@dataclass
class PlanStep:
    """Represents a single step in an execution plan.

    Each step is independently verifiable and includes:
    - Description of what the step accomplishes
    - Files to be modified or created
    - Action type (create, modify, delete)
    - Verification command and expected output
    """

    description: str
    files: list[str]
    action: str


@dataclass
class ExecutionPlan:
    """Structured execution plan for a task.

    Contains all steps needed to complete a task, verification details,
    and context tracking for token usage.
    """

    task_id: str
    steps: list[PlanStep]
    verification_command: str
    estimated_tokens: int


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

    async def plan(self, task: Task) -> ExecutionPlan:
        """Create an execution plan for a task.

        Takes a task from the issue tracker and produces a structured
        execution plan with specific steps, files, and verification commands.

        Args:
            task: The Task to create a plan for.

        Returns:
            An ExecutionPlan object containing all steps and verification details.

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

        # Parse the output into an ExecutionPlan
        plan = self._parse_plan_from_output(result.output, task.id)

        # Calculate token usage
        estimated_tokens = result.tokens_after - result.tokens_before

        # Create the plan with token tracking
        execution_plan = ExecutionPlan(
            task_id=plan["task_id"],
            steps=plan["steps"],
            verification_command=plan["verification_command"],
            estimated_tokens=estimated_tokens,
        )

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
title: "{task.title}"
summary: "One-sentence summary of what will be done"

steps:
  - id: 1
    description: "What this step accomplishes"
    type: "create|modify|delete|test"
    files:
      - path: "src/path/to/file.py"
        action: "create|modify|delete"
    changes:
      - "Specific change description"
    verification:
      command: "pytest tests/unit/test_file.py"
      expected: "All tests pass"
    dependencies: []  # list of step IDs this depends on

  - id: 2
    description: "Second step"
    # ... more steps

verification:
  final_command: "pytest tests/ -v"
  acceptance_check: "How to verify all acceptance criteria are met"

risks:
  - description: "Potential issue"
    mitigation: "How to address it"

estimated_complexity: "low|medium|high"
```

## Guidelines

- Be specific about file paths (use exact, real paths)
- Each step should be small enough to complete in one commit
- Include test creation/modification in appropriate steps
- Consider edge cases and error handling
- Steps should be ordered by dependencies
- Verification commands should be concrete and runnable

Generate the execution plan for this task now."""

        return prompt

    def _parse_plan_from_output(self, output: str, task_id: str) -> dict:
        """Parse agent output into a plan dictionary.

        Extracts the YAML-formatted plan from the agent's output and
        converts it into structured data.

        Args:
            output: The agent's text output containing the plan.
            task_id: The task ID for fallback reference.

        Returns:
            A dictionary with task_id, steps, and verification_command.

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

        # Parse steps
        steps = []
        steps_data = plan_data.get("steps", [])
        for step_data in steps_data:
            files = self._extract_files_from_step(step_data)
            action = step_data.get("type", "modify")

            step = PlanStep(
                description=step_data.get("description", ""),
                files=files,
                action=action,
            )
            steps.append(step)

        if not steps:
            raise ValueError("Output doesn't contain any execution steps")

        # Extract verification command
        verification_data = plan_data.get("verification", {})
        final_command = verification_data.get("final_command", "pytest tests/ -v")

        return {
            "task_id": extracted_task_id,
            "steps": steps,
            "verification_command": final_command,
        }

    def _extract_files_from_step(self, step_data: dict) -> list[str]:
        """Extract file paths from a step.

        Args:
            step_data: The step data dictionary.

        Returns:
            A list of file paths from the step.
        """
        files = []
        files_data = step_data.get("files", [])

        if isinstance(files_data, list):
            for file_item in files_data:
                if isinstance(file_item, dict):
                    path = file_item.get("path")
                    if path:
                        files.append(path)
                elif isinstance(file_item, str):
                    files.append(file_item)

        return files
