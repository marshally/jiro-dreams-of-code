"""Task executor and preflight checks."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import structlog

from jiro.agents.planning import ExecutionPlan, PlanningAgent
from jiro.config.schema import Config
from jiro.trackers.interface import Task

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


def run_relevant_tests(task: Task, config: Config) -> bool:
    """Run relevant tests for a task.

    Finds and runs test files relevant to the task. Returns True if tests
    pass or if no tests are found.

    Args:
        task: The task to run tests for.
        config: Configuration including test command.

    Returns:
        True if tests pass or no tests found, False if tests fail.
    """
    test_files = find_relevant_test_files(task)

    if not test_files:
        logger.info("run_relevant_tests_no_tests_found", task_id=task.id)
        return True

    logger.info(
        "run_relevant_tests_start",
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
                "run_relevant_tests_success",
                task_id=task.id,
                test_count=len(test_files),
            )
            return True
        else:
            logger.warning(
                "run_relevant_tests_failed",
                task_id=task.id,
                stderr=result.stderr,
            )
            return False

    except subprocess.TimeoutExpired:
        logger.error(
            "run_relevant_tests_timeout",
            task_id=task.id,
            timeout=60,
        )
        return False
    except Exception as e:
        logger.error(
            "run_relevant_tests_error",
            task_id=task.id,
            error=str(e),
        )
        return False


def run_relevant_lint(task: Task, config: Config) -> bool:
    """Run linter on relevant source files.

    Finds and lints source files relevant to the task. Returns True if lint
    passes or if no files are found.

    Args:
        task: The task to lint files for.
        config: Configuration including lint command.

    Returns:
        True if lint passes or no files found, False if lint fails.
    """
    source_files = find_relevant_source_files(task)

    if not source_files:
        logger.info("run_relevant_lint_no_files_found", task_id=task.id)
        return True

    logger.info(
        "run_relevant_lint_start",
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
                "run_relevant_lint_success",
                task_id=task.id,
                file_count=len(source_files),
            )
            return True
        else:
            logger.warning(
                "run_relevant_lint_failed",
                task_id=task.id,
                stderr=result.stderr,
            )
            return False

    except subprocess.TimeoutExpired:
        logger.error(
            "run_relevant_lint_timeout",
            task_id=task.id,
            timeout=60,
        )
        return False
    except Exception as e:
        logger.error(
            "run_relevant_lint_error",
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
    execution_plan: ExecutionPlan


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
