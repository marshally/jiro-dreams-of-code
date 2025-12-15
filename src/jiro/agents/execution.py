"""ExecutionAgent for executing plans created by the planning agent."""

from dataclasses import dataclass

import structlog

from jiro.agents.client import AgentClient
from jiro.agents.planning import ExecutionPlan, PlanStep

logger = structlog.get_logger()


@dataclass
class StepResult:
    """Result from executing a single step in a plan.

    Tracks the step index, success status, output, and any errors
    that occurred during execution.
    """

    step_index: int
    success: bool
    output: str
    error: str | None = None


@dataclass
class ExecutionResult:
    """Result from executing a complete execution plan.

    Contains overall success status, count of completed steps,
    detailed results for each step, and cumulative token usage.
    """

    plan_id: str
    steps_completed: int
    total_steps: int
    success: bool
    step_results: list[StepResult]
    total_tokens: int
    error: str | None = None


class ExecutionAgent:
    """Agent that executes plans created by the planning agent.

    Takes an ExecutionPlan and mechanically implements each step,
    tracking context usage and stopping on any error. Uses the
    AgentClient to delegate work to Claude.
    """

    def __init__(self, client: AgentClient) -> None:
        """Initialize ExecutionAgent.

        Args:
            client: AgentClient instance for executing steps.

        Raises:
            TypeError: If client is None.
        """
        if client is None:
            raise TypeError("client cannot be None")
        self.client = client

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute a plan step by step.

        Takes an ExecutionPlan and executes each step in order,
        tracking token usage and stopping on any error.

        Args:
            plan: The ExecutionPlan to execute.

        Returns:
            An ExecutionResult containing step-by-step results
            and overall execution status.
        """
        logger.info(
            "execution_agent_execute_start",
            plan_id=plan.task_id,
            total_steps=len(plan.steps),
        )

        step_results: list[StepResult] = []
        total_tokens = 0
        steps_completed = 0
        error_message: str | None = None
        initial_tokens = 0
        final_tokens = 0

        for step_index, step in enumerate(plan.steps):
            logger.info(
                "execution_step_start",
                step_index=step_index,
                description=step.description,
            )

            # Build prompt for this step
            prompt = self._build_step_prompt(step, step_index, len(plan.steps))

            # Execute the step
            result = await self.client.execute(prompt)

            # Track tokens
            if step_index == 0:
                initial_tokens = result.tokens_before
            final_tokens = result.tokens_after

            # Create step result
            step_result = StepResult(
                step_index=step_index,
                success=result.success,
                output=result.output,
                error=result.error,
            )
            step_results.append(step_result)

            # Check for errors
            if not result.success:
                logger.error(
                    "execution_step_failed",
                    step_index=step_index,
                    error=result.error,
                )
                error_message = result.error
                break

            steps_completed += 1
            logger.info(
                "execution_step_completed",
                step_index=step_index,
            )

        # Calculate total tokens used
        total_tokens = final_tokens - initial_tokens if final_tokens > 0 else 0

        # Create execution result
        success = steps_completed == len(plan.steps) and error_message is None

        execution_result = ExecutionResult(
            plan_id=plan.task_id,
            steps_completed=steps_completed,
            total_steps=len(plan.steps),
            success=success,
            step_results=step_results,
            total_tokens=total_tokens,
            error=error_message,
        )

        logger.info(
            "execution_agent_execute_complete",
            plan_id=plan.task_id,
            success=success,
            steps_completed=steps_completed,
            total_tokens=total_tokens,
            error=error_message,
        )

        return execution_result

    def _build_step_prompt(self, step: PlanStep, step_index: int, total_steps: int) -> str:
        """Build a prompt for executing a single step.

        Args:
            step: The PlanStep to execute.
            step_index: The index of this step (0-based).
            total_steps: Total number of steps in the plan.

        Returns:
            A formatted prompt for executing the step.
        """
        prompt = f"""You are an execution agent executing step {step_index + 1} of {total_steps}.

Step Description: {step.description}

Files to Modify:
{chr(10).join(f"- {f}" for f in step.files)}

Action Type: {step.action}

Execute this step exactly as described. Do not deviate from the plan.
Report your progress clearly."""

        return prompt
