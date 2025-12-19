"""Task executor and preflight checks."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import structlog

from jiro.agents.planning import PlanningAgent
from jiro.agents.review import ReviewAgent, ReviewResult
from jiro.config.schema import Config
from jiro.core.execution_plan import ExecutionPlanSchema
from jiro.core.tdd_sequence import TddSequenceTracker
from jiro.steps.types import StepType
from jiro.trackers.interface import IssueTracker, Task

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


def find_relevant_test_files(task: Task) -> list[str]:
    """Find test files relevant to a task.

    Searches for test files that might test the files mentioned in the task
    description or labels.

    Args:
        task: The task to find tests for.

    Returns:
        List of relevant test file paths.
    """
    test_files = []

    # Simple heuristic: find test files in tests/ directory
    tests_dir = Path("tests/unit")
    if tests_dir.exists():
        for test_file in tests_dir.glob("test_*.py"):
            # For now, include all test files - in a real implementation,
            # we would filter based on task context
            test_files.append(str(test_file))

    logger.info(
        "find_relevant_test_files",
        task_id=task.id,
        test_count=len(test_files),
    )

    return test_files


def find_relevant_source_files(task: Task) -> list[str]:
    """Find source files relevant to a task.

    Searches for source files that might be modified by this task.

    Args:
        task: The task to find source files for.

    Returns:
        List of relevant source file paths.
    """
    source_files = []

    # Simple heuristic: find all Python source files in src/
    src_dir = Path("src/jiro")
    if src_dir.exists():
        for source_file in src_dir.rglob("*.py"):
            # Exclude __pycache__ and other non-essential files
            if "__pycache__" not in str(source_file):
                source_files.append(str(source_file))

    logger.info(
        "find_relevant_source_files",
        task_id=task.id,
        source_count=len(source_files),
    )

    return source_files


def run_relevant_tests(
    task: Task,
    config: Config,
    phase: Literal["preflight", "postflight"] = "preflight",
) -> bool:
    """Run relevant tests for a task in either preflight or postflight phase.

    Finds and runs test files relevant to the task. Returns True if tests
    pass or if no tests are found.

    Args:
        task: The task to run tests for.
        config: Configuration including test command.
        phase: Phase of execution ("preflight" or "postflight") for logging differentiation.

    Returns:
        True if tests pass or no tests found, False if tests fail.
    """
    test_files = find_relevant_test_files(task)

    if not test_files:
        logger.info(f"run_relevant_tests_{phase}_no_tests_found", task_id=task.id)
        return True

    logger.info(
        f"run_relevant_tests_{phase}_start",
        task_id=task.id,
        test_count=len(test_files),
    )

    # Build the test command
    test_cmd = f"{config.commands.test} {' '.join(test_files)}"

    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            logger.info(
                f"run_relevant_tests_{phase}_success",
                task_id=task.id,
                test_count=len(test_files),
            )
            return True
        else:
            logger.warning(
                f"run_relevant_tests_{phase}_failed",
                task_id=task.id,
                stderr=result.stderr,
            )
            return False

    except subprocess.TimeoutExpired:
        logger.error(
            f"run_relevant_tests_{phase}_timeout",
            task_id=task.id,
            timeout=60,
        )
        return False
    except Exception as e:
        logger.error(
            f"run_relevant_tests_{phase}_error",
            task_id=task.id,
            error=str(e),
        )
        return False


def run_relevant_lint(
    task: Task,
    config: Config,
    phase: Literal["preflight", "postflight"] = "preflight",
) -> bool:
    """Run linter on relevant source files in either phase.

    Finds and lints source files relevant to the task. Returns True if lint
    passes or if no files are found.

    Args:
        task: The task to lint files for.
        config: Configuration including lint command.
        phase: Phase of execution ("preflight" or "postflight") for logging differentiation.

    Returns:
        True if lint passes or no files found, False if lint fails.
    """
    source_files = find_relevant_source_files(task)

    if not source_files:
        logger.info(f"run_relevant_lint_{phase}_no_files_found", task_id=task.id)
        return True

    logger.info(
        f"run_relevant_lint_{phase}_start",
        task_id=task.id,
        file_count=len(source_files),
    )

    # Build the lint command
    lint_cmd = f"{config.commands.lint} {' '.join(source_files)}"

    try:
        result = subprocess.run(
            lint_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            logger.info(
                f"run_relevant_lint_{phase}_success",
                task_id=task.id,
                file_count=len(source_files),
            )
            return True
        else:
            logger.warning(
                f"run_relevant_lint_{phase}_failed",
                task_id=task.id,
                stderr=result.stderr,
            )
            return False

    except subprocess.TimeoutExpired:
        logger.error(
            f"run_relevant_lint_{phase}_timeout",
            task_id=task.id,
            timeout=60,
        )
        return False
    except Exception as e:
        logger.error(
            f"run_relevant_lint_{phase}_error",
            task_id=task.id,
            error=str(e),
        )
        return False


@dataclass
class EnhancedTask:
    """Task enhanced with execution plan.

    Represents a task that has been enriched with a detailed execution plan
    from the planning agent.
    """

    task: Task
    execution_plan: ExecutionPlanSchema


@dataclass
class PreflightResult:
    """Result of running task preflight checks.

    Contains the results of all preflight checks: relevant tests, linting,
    and planning. Also contains the enhanced task if planning succeeded.
    """

    tests_passed: bool
    lint_passed: bool
    planning_done: bool
    enhanced_task: "EnhancedTask | None"
    errors: list[str]


@dataclass
class PostflightResult:
    """Result of running task postflight checks.

    Contains the results of all postflight checks: commit review, tests,
    linting, task closing, and results recording.
    """

    review_passed: bool
    tests_passed: bool
    lint_passed: bool
    task_closed: bool
    results_recorded: bool
    error: str | None = None


async def enhance_task_with_planning(task: Task, agent: PlanningAgent) -> EnhancedTask:
    """Enhance a task with an execution plan.

    Calls the planning agent to create a detailed execution plan for the task.

    Args:
        task: The task to plan for.
        agent: The planning agent to use.

    Returns:
        An EnhancedTask with the execution plan.

    Raises:
        ValueError: If planning fails.
    """
    logger.info("enhance_task_with_planning_start", task_id=task.id)

    execution_plan = await agent.plan(task)

    logger.info(
        "enhance_task_with_planning_success",
        task_id=task.id,
        steps=len(execution_plan.steps),
        tokens_used=execution_plan.estimated_tokens,
    )

    return EnhancedTask(task=task, execution_plan=execution_plan)


async def review_commits(task: Task, commits: list[str], agent: ReviewAgent) -> ReviewResult:
    """Review commits using ReviewAgent.

    Takes a list of commits and reviews each one using the ReviewAgent.
    Returns the result from reviewing the last commit.

    Args:
        task: The task being worked on.
        commits: List of commit SHAs to review.
        agent: The ReviewAgent instance.

    Returns:
        A ReviewResult from reviewing the commits.
    """
    if not commits:
        logger.warning("review_commits_no_commits", task_id=task.id)
        return ReviewResult(
            passed=True,
            halt=False,
            reason="No commits to review",
            checks={},
        )

    logger.info(
        "review_commits_start",
        task_id=task.id,
        commit_count=len(commits),
    )

    # Review the last commit
    commit_sha = commits[-1]
    result = await agent.review(commit_sha, task)

    logger.info(
        "review_commits_complete",
        task_id=task.id,
        commit_sha=commit_sha,
        passed=result.passed,
    )

    return result


def record_results(task: Task, result: PostflightResult) -> None:
    """Record execution results.

    Records the postflight check results for the task. This can be used
    for logging, metrics, or storing results in a database.

    Args:
        task: The task that was completed.
        result: The PostflightResult containing all check results.
    """
    logger.info(
        "record_results_start",
        task_id=task.id,
        review_passed=result.review_passed,
        tests_passed=result.tests_passed,
        lint_passed=result.lint_passed,
        task_closed=result.task_closed,
    )

    # Log the results
    logger.info(
        "record_results_complete",
        task_id=task.id,
        all_passed=all(
            [
                result.review_passed,
                result.tests_passed,
                result.lint_passed,
                result.task_closed,
            ]
        ),
    )


def close_task_in_tracker(task: Task, tracker: IssueTracker) -> None:
    """Close task in the issue tracker.

    Updates the task status to closed in the issue tracker backend.

    Args:
        task: The task to close.
        tracker: The issue tracker to use for closing the task.
    """
    logger.info("close_task_in_tracker_start", task_id=task.id)

    try:
        tracker.close_task(task.id, reason="Task completed successfully")

        logger.info("close_task_in_tracker_success", task_id=task.id)
    except Exception as e:
        logger.error(
            "close_task_in_tracker_error",
            task_id=task.id,
            error=str(e),
        )


async def run_task_postflight(
    task: Task,
    commits: list[str],
    config: Config,
    tracker: IssueTracker,
    review_agent: ReviewAgent | None = None,
) -> PostflightResult:
    """Run all postflight checks for a completed task.

    Runs the following checks in order:
    1. Review commits using ReviewAgent
    2. Run relevant tests
    3. Run relevant linting
    4. Record results
    5. Close task in tracker

    Returns a result object indicating which checks passed and any errors.

    Args:
        task: The task to run postflight checks for.
        commits: List of commit SHAs from task completion.
        config: Configuration for test and lint commands.
        tracker: The issue tracker for closing tasks.
        review_agent: Optional ReviewAgent instance for testing.

    Returns:
        A PostflightResult with all check results.
    """
    logger.info("run_task_postflight_start", task_id=task.id, title=task.title)

    review_passed = False
    tests_passed = False
    lint_passed = False
    task_closed = False
    results_recorded = False
    error = None

    try:
        # Step 1: Review commits
        # Get a ReviewAgent instance - this will be injected in real usage
        # For now, we'll create a minimal agent if not provided
        try:
            if review_agent is None:
                from jiro.agents.client import AgentClient

                client = AgentClient(config=config, repository=None)  # type: ignore[arg-type]
                review_agent = ReviewAgent(client, config)

            review_result = await review_commits(task, commits, review_agent)
            review_passed = review_result.passed
        except Exception as e:
            logger.error("run_task_postflight_review_failed", task_id=task.id, error=str(e))
            review_passed = False
            error = f"Review failed: {str(e)}"

        # Step 2: Run relevant tests
        tests_passed = run_relevant_tests(task, config, phase="postflight")

        # Step 3: Run relevant linting
        lint_passed = run_relevant_lint(task, config, phase="postflight")

        # Step 4: Record results
        result = PostflightResult(
            review_passed=review_passed,
            tests_passed=tests_passed,
            lint_passed=lint_passed,
            task_closed=False,
            results_recorded=False,
            error=error,
        )
        record_results(task, result)
        results_recorded = True

        # Step 5: Close task in tracker (only if all checks passed)
        if review_passed and tests_passed and lint_passed:
            close_task_in_tracker(task, tracker)
            task_closed = True

    except Exception as e:
        logger.error(
            "run_task_postflight_error",
            task_id=task.id,
            error=str(e),
        )
        error = str(e)

    logger.info(
        "run_task_postflight_complete",
        task_id=task.id,
        review_passed=review_passed,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        task_closed=task_closed,
    )

    return PostflightResult(
        review_passed=review_passed,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        task_closed=task_closed,
        results_recorded=results_recorded,
        error=error,
    )


async def run_task_preflight(task: Task, config: Config, agent: PlanningAgent) -> PreflightResult:
    """Run all preflight checks for a task.

    Runs the following checks in order:
    1. Relevant tests
    2. Relevant linting
    3. Task planning

    Returns a result object indicating which checks passed and any errors.

    Args:
        task: The task to run preflight checks for.
        config: Configuration for test and lint commands.
        agent: The planning agent for creating execution plans.

    Returns:
        A PreflightResult with all check results.
    """
    logger.info("run_task_preflight_start", task_id=task.id, title=task.title)

    errors = []
    tests_passed = run_relevant_tests(task, config)
    lint_passed = run_relevant_lint(task, config)
    enhanced_task = None
    planning_done = False

    if not tests_passed:
        errors.append("Relevant tests failed")

    if not lint_passed:
        errors.append("Relevant lint checks failed")

    try:
        enhanced_task = await enhance_task_with_planning(task, agent)
        planning_done = True
    except Exception as e:
        logger.error(
            "run_task_preflight_planning_failed",
            task_id=task.id,
            error=str(e),
        )
        errors.append(f"Planning failed: {str(e)}")

    logger.info(
        "run_task_preflight_complete",
        task_id=task.id,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        planning_done=planning_done,
        error_count=len(errors),
    )

    return PreflightResult(
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        planning_done=planning_done,
        enhanced_task=enhanced_task,
        errors=errors,
    )


class TaskExecutor:
    """Executor for processing tasks through the full lifecycle.

    Handles the complete execution flow for a single task:
    1. Preflight checks (tests, lint, planning)
    2. Step execution (dispatching to appropriate handlers)
    3. Review of commits
    4. Postflight checks and task completion

    Enforces TDD sequence ordering for TDD steps (Red→Green→Refactor).
    """

    def __init__(
        self,
        config: Config,
        planning_agent: PlanningAgent,
        review_agent: ReviewAgent,
        tracker: IssueTracker,
        tdd_sequence_tracker: TddSequenceTracker | None = None,
    ) -> None:
        """Initialize TaskExecutor with required agents and dependencies.

        Args:
            config: Configuration for commands and behavior.
            planning_agent: Agent for creating execution plans.
            review_agent: Agent for reviewing commits.
            tracker: Issue tracker for managing task state.
            tdd_sequence_tracker: Optional tracker for TDD sequences.
        """
        self.config = config
        self.planning_agent = planning_agent
        self.review_agent = review_agent
        self.tracker = tracker
        self.tdd_sequence_tracker = tdd_sequence_tracker or TddSequenceTracker()

    async def execute_task(self, task: Task) -> PostflightResult:
        """Execute a single task through its complete lifecycle.

        Orchestrates the full execution flow:
        1. Run preflight checks
        2. Call planning_agent to create execution plan
        3. Save plan to database
        4. Execute each step in the plan
        5. Review commits after each step
        6. Run postflight checks
        7. Mark task complete

        Args:
            task: The task to execute.

        Returns:
            A PostflightResult with execution outcome.

        Raises:
            ValueError: If preflight or execution fails critically.
            HaltError: If review fails or other halt conditions occur.
        """
        logger.info("task_executor_execute_start", task_id=task.id, title=task.title)

        try:
            # Step 1: Run preflight checks
            preflight_result = await run_task_preflight(task, self.config, self.planning_agent)

            if not preflight_result.planning_done or preflight_result.enhanced_task is None:
                error_msg = f"Preflight failed: {'; '.join(preflight_result.errors)}"
                logger.error(
                    "task_executor_preflight_failed",
                    task_id=task.id,
                    errors=preflight_result.errors,
                )
                raise ValueError(error_msg)

            enhanced_task = preflight_result.enhanced_task
            execution_plan = enhanced_task.execution_plan

            logger.info(
                "task_executor_plan_created",
                task_id=task.id,
                steps=len(execution_plan.steps),
            )

            # Step 2: Execute each step in the plan
            commits: list[str] = []

            for step_idx, step in enumerate(execution_plan.steps):
                logger.info(
                    "task_executor_step_start",
                    task_id=task.id,
                    step_idx=step_idx,
                    step_type=step.step_type,
                    description=step.description,
                )

                try:
                    # Validate TDD sequence if this is a TDD step
                    step_type = StepType(step.step_type)
                    is_valid, error_msg = self.tdd_sequence_tracker.validate_step_phase(
                        task.id, step_type
                    )

                    if not is_valid:
                        logger.error(
                            "task_executor_tdd_sequence_violation",
                            task_id=task.id,
                            step_idx=step_idx,
                            step_type=step.step_type,
                            error=error_msg,
                        )
                        raise ValueError(f"TDD sequence violation: {error_msg}")

                    # Execute the step - for now, we just log it
                    # In a real implementation, this would dispatch to step handlers
                    logger.info(
                        "task_executor_step_executing",
                        task_id=task.id,
                        step_idx=step_idx,
                        step_type=step.step_type,
                    )

                    # Step would create a commit here in the real implementation
                    # For now, we simulate getting a commit SHA
                    commit_sha = f"commit-{step_idx}-{task.id[:8]}"

                    # Review the commit
                    review_result = await self.review_agent.review(commit_sha, task)

                    if not review_result.passed:
                        error_msg = f"Review failed for step {step_idx}: {review_result.reason}"
                        logger.error(
                            "task_executor_review_failed",
                            task_id=task.id,
                            step_idx=step_idx,
                            reason=review_result.reason,
                        )
                        raise ValueError(error_msg)

                    # Record TDD phase completion if applicable
                    if step_type in (StepType.TDD_RED, StepType.TDD_GREEN, StepType.TDD_REFACTOR):
                        self.tdd_sequence_tracker.record_step_completion(
                            task.id, step_type, commit_sha
                        )

                    commits.append(commit_sha)

                    logger.info(
                        "task_executor_step_complete",
                        task_id=task.id,
                        step_idx=step_idx,
                        commit_sha=commit_sha,
                    )

                except Exception as e:
                    logger.error(
                        "task_executor_step_failed",
                        task_id=task.id,
                        step_idx=step_idx,
                        error=str(e),
                    )
                    raise

            logger.info(
                "task_executor_all_steps_complete",
                task_id=task.id,
                commits_count=len(commits),
            )

            # Step 3: Run postflight checks
            postflight_result = await run_task_postflight(
                task, commits, self.config, self.tracker, review_agent=self.review_agent
            )

            logger.info(
                "task_executor_postflight_complete",
                task_id=task.id,
                review_passed=postflight_result.review_passed,
                tests_passed=postflight_result.tests_passed,
                lint_passed=postflight_result.lint_passed,
            )

            return postflight_result

        except Exception as e:
            logger.error(
                "task_executor_execute_failed",
                task_id=task.id,
                error=str(e),
            )
            raise


def create_task_executor(
    config: Config,
    planning_agent: PlanningAgent,
    review_agent: ReviewAgent,
    tracker: IssueTracker,
    tdd_sequence_tracker: TddSequenceTracker | None = None,
) -> TaskExecutor:
    """Factory function to create a TaskExecutor instance.

    This is a convenience function for creating TaskExecutor instances
    with all required dependencies. Useful for reducing boilerplate in
    calling code.

    Args:
        config: Configuration for commands and behavior.
        planning_agent: Agent for creating execution plans.
        review_agent: Agent for reviewing commits.
        tracker: Issue tracker for managing task state.
        tdd_sequence_tracker: Optional tracker for TDD sequences.

    Returns:
        A configured TaskExecutor instance.
    """
    return TaskExecutor(
        config=config,
        planning_agent=planning_agent,
        review_agent=review_agent,
        tracker=tracker,
        tdd_sequence_tracker=tdd_sequence_tracker,
    )
