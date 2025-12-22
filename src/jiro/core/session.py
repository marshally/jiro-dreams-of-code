"""Session preflight checks for jiro workflow."""

import asyncio
import subprocess
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from jiro.agents.client import AgentClient
from jiro.agents.planning import PlanningAgent
from jiro.agents.review import ReviewAgent
from jiro.config.schema import Config
from jiro.core.executor import TaskExecutor
from jiro.db.models import Session, SessionStatus, TaskExecution
from jiro.db.repository import PromptRepository, SessionRepository, TaskExecutionRepository
from jiro.trackers.beads import BeadsTracker
from jiro.trackers.interface import Task

logger = structlog.get_logger()


class HaltError(Exception):
    """Exception raised when a session is halted.

    Raised when the session needs to stop execution due to a failure
    in review, execution, preflight, postflight checks, or other errors.
    """

    def __init__(self, reason: str) -> None:
        """Initialize HaltError.

        Args:
            reason: The reason the session was halted.
        """
        self.reason = reason
        super().__init__(f"Session halted: {reason}")


@dataclass
class CheckResult:
    """Result of a single preflight check.

    Attributes:
        name: The name of the check.
        passed: Whether the check passed.
        error: Error message if the check failed, None otherwise.
    """

    name: str
    passed: bool
    error: str | None = None


@dataclass
class CheckPhaseResult:
    """Base result for preflight/postflight phases.

    Attributes:
        passed: Whether all checks passed.
        checks: Dictionary mapping check names to CheckResult objects.
        errors: List of error messages from failed checks.
    """

    passed: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class PreflightResult(CheckPhaseResult):
    """Result of running all preflight checks.

    Inherits from CheckPhaseResult with fields for passed status,
    individual check results, and error messages.
    """


@dataclass
class PostflightResult(CheckPhaseResult):
    """Result of running all postflight checks.

    Inherits from CheckPhaseResult with fields for passed status,
    individual check results, and error messages.
    """


def check_git_clean() -> bool:
    """Check if the git working directory is clean.

    Returns:
        True if no uncommitted changes exist, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        # Empty output means clean working directory
        return result.stdout.strip() == ""
    except FileNotFoundError:
        # Git command not found
        return False


def check_correct_branch(config: Config) -> bool:
    """Check if currently on the correct branch.

    Args:
        config: Configuration object containing target branch info.

    Returns:
        True if on the correct branch, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False

        current_branch = result.stdout.strip()

        # Get target branch from config
        # If config has target_branch, use it; otherwise assume it's fine
        target_branch: str | None = getattr(config.preflight, "target_branch", None)
        if target_branch is None:
            # No target branch specified, so always pass
            return True

        return current_branch == target_branch
    except FileNotFoundError:
        # Git command not found
        return False


def check_up_to_date() -> bool:
    """Check if the local repository is up to date with origin.

    Performs git fetch and compares local HEAD with origin/HEAD.
    If there is no origin remote, the check passes (returns True).

    Returns:
        True if up to date with origin or no origin exists, False otherwise.
    """
    try:
        # Check if origin remote exists
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if remote_result.returncode != 0:
            # No origin remote, skip this check
            return True

        # Fetch latest from origin
        fetch_result = subprocess.run(
            ["git", "fetch"],
            capture_output=True,
            text=True,
            check=False,
        )
        if fetch_result.returncode != 0:
            return False

        # Get local HEAD SHA
        local_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if local_result.returncode != 0:
            return False

        local_sha = local_result.stdout.strip()

        # Get origin HEAD SHA
        origin_result = subprocess.run(
            ["git", "rev-parse", "origin/HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if origin_result.returncode != 0:
            return False

        origin_sha = origin_result.stdout.strip()

        return local_sha == origin_sha
    except FileNotFoundError:
        # Git command not found
        return False


def check_tests_pass(config: Config) -> tuple[bool, str | None]:
    """Check if all tests pass.

    Args:
        config: Configuration object containing test command.

    Returns:
        Tuple of (passed, error_output). error_output is None if passed.
    """
    try:
        test_command = config.commands.test
        result = subprocess.run(
            [test_command],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        # Exit code 0: all tests passed
        # Exit code 5: no tests collected (pytest) - treat as pass
        if result.returncode == 0 or result.returncode == 5:
            return True, None
        # Combine stderr and stdout for full error context
        output = result.stderr or result.stdout or "Tests failed (no output)"
        return False, output.strip()
    except Exception as e:
        return False, str(e)


def check_lint_pass(config: Config) -> tuple[bool, str | None]:
    """Check if linting passes.

    Args:
        config: Configuration object containing lint command.

    Returns:
        Tuple of (passed, error_output). error_output is None if passed.
    """
    try:
        lint_command = config.commands.lint
        result = subprocess.run(
            [lint_command],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        if result.returncode == 0:
            return True, None
        output = result.stderr or result.stdout or "Linting failed (no output)"
        return False, output.strip()
    except Exception as e:
        return False, str(e)


def run_check(
    name: str,
    check_fn: Callable[[], bool | tuple[bool, str | None]],
    error_message: str,
    checks: dict[str, CheckResult],
    errors: list[str],
) -> None:
    """Run a single check and record the result.

    Executes a check function and records the result in the checks dict.
    If the check fails or raises an exception, adds an error message to the errors list.

    Args:
        name: The name of the check.
        check_fn: Callable that performs the check and returns either a boolean
                  or a tuple of (passed, detailed_error).
        error_message: Default error message if the check fails.
        checks: Dictionary to store the CheckResult.
        errors: List to accumulate error messages.
    """
    try:
        result = check_fn()
        # Handle both bool and tuple return types
        if isinstance(result, tuple):
            passed, detailed_error = result
            actual_error = detailed_error if detailed_error else error_message
        else:
            passed = result
            actual_error = error_message

        checks[name] = CheckResult(
            name=name,
            passed=passed,
            error=None if passed else actual_error,
        )
        if not passed:
            errors.append(f"{name}: {actual_error}")
    except Exception as e:
        checks[name] = CheckResult(name=name, passed=False, error=str(e))
        errors.append(f"{name}: {str(e)}")


def run_preflight(config: Config) -> PreflightResult:
    """Run all preflight checks.

    Orchestrates all preflight checks and returns a comprehensive result
    with details about each check.

    Args:
        config: Configuration object with check settings.

    Returns:
        PreflightResult containing results of all checks and overall status.
    """
    checks: dict[str, CheckResult] = {}
    errors: list[str] = []

    # Run each preflight check
    run_check(
        "git_clean",
        check_git_clean,
        "Uncommitted changes detected",
        checks,
        errors,
    )
    run_check(
        "correct_branch",
        lambda: check_correct_branch(config),
        "Not on correct branch",
        checks,
        errors,
    )
    run_check(
        "up_to_date",
        check_up_to_date,
        "Not up to date with origin",
        checks,
        errors,
    )
    run_check(
        "tests_pass",
        lambda: check_tests_pass(config),
        "Tests failed",
        checks,
        errors,
    )
    run_check(
        "lint_pass",
        lambda: check_lint_pass(config),
        "Linting failed",
        checks,
        errors,
    )

    # Determine overall result
    all_passed = all(check.passed for check in checks.values())

    # Create result
    result = PreflightResult(passed=all_passed, checks=checks, errors=errors)

    # Log results
    logger.info(
        "preflight_checks_completed",
        passed=all_passed,
        checks={name: check.passed for name, check in checks.items()},
        errors=errors if errors else None,
    )

    return result


def run_full_tests(config: Config) -> bool:
    """Run the full test suite.

    Args:
        config: Configuration object containing test command.

    Returns:
        True if tests pass or no tests exist, False otherwise.
    """
    try:
        test_command = config.commands.test
        result = subprocess.run(
            [test_command],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        # Exit code 0: all tests passed
        # Exit code 5: no tests collected (pytest) - treat as pass for greenfield projects
        return result.returncode == 0 or result.returncode == 5
    except FileNotFoundError:
        # Test command not found
        return False


def run_full_lint(config: Config) -> bool:
    """Run the full linting suite.

    Args:
        config: Configuration object containing lint command.

    Returns:
        True if linting passes, False otherwise.
    """
    try:
        lint_command = config.commands.lint
        result = subprocess.run(
            [lint_command],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        # Lint command not found
        return False


def push_to_origin() -> bool:
    """Push the current branch to origin.

    If there is no origin remote, the check passes (returns True).

    Returns:
        True if push succeeds or no origin exists, False otherwise.
    """
    try:
        # Check if origin remote exists
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if remote_result.returncode != 0:
            # No origin remote, skip this check
            return True

        result = subprocess.run(
            ["git", "push", "origin", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        # Git command not found
        return False


def run_postflight(config: Config) -> PostflightResult:
    """Run all postflight checks.

    Orchestrates all postflight checks and returns a comprehensive result
    with details about each check.

    Args:
        config: Configuration object with check settings.

    Returns:
        PostflightResult containing results of all checks and overall status.
    """
    checks: dict[str, CheckResult] = {}
    errors: list[str] = []

    # Run each postflight check
    run_check(
        "full_tests",
        lambda: run_full_tests(config),
        "Full test suite failed",
        checks,
        errors,
    )
    run_check(
        "full_lint",
        lambda: run_full_lint(config),
        "Full lint failed",
        checks,
        errors,
    )
    run_check(
        "push_to_origin",
        push_to_origin,
        "Push to origin failed",
        checks,
        errors,
    )

    # Determine overall result
    all_passed = all(check.passed for check in checks.values())

    # Create result
    result = PostflightResult(passed=all_passed, checks=checks, errors=errors)

    # Log results
    logger.info(
        "postflight_checks_completed",
        passed=all_passed,
        checks={name: check.passed for name, check in checks.items()},
        errors=errors if errors else None,
    )

    return result


@dataclass
class SessionResult:
    """Result of running a full session.

    Attributes:
        session_id: ID of the session that ran.
        status: Final status of the session ('completed', 'failed', 'halted').
        tasks_completed: Number of tasks successfully completed.
        tasks_failed: Number of tasks that failed.
        error: Error message if the session failed, None otherwise.
    """

    session_id: str
    status: SessionStatus
    tasks_completed: int
    tasks_failed: int
    error: str | None = None


ProgressCallback = Callable[[str, str | None], None]


class SessionOrchestrator:
    """Orchestrates the full session lifecycle.

    Manages the complete workflow: session creation, preflight checks,
    task execution in dependency order, postflight checks, and status tracking.
    """

    def __init__(
        self,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
        prompt_repo: "PromptRepository | None" = None,
        tracker: BeadsTracker | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize with dependencies.

        Args:
            config: Configuration object for checks and commands.
            session_repo: Repository for session persistence.
            task_repo: Repository for task execution persistence.
            prompt_repo: Repository for storing agent prompt/response data.
            tracker: Issue tracker for fetching tasks.
            progress_callback: Optional callback for progress reporting.
                              Called with (message, status) where status is
                              'pass', 'fail', 'skip', or None.
        """
        self.config = config
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.prompt_repo = prompt_repo
        self.tracker = tracker
        self.logger = logger  # Use module-level logger
        self.progress_callback = progress_callback

    def _report(self, message: str, status: str | None = None) -> None:
        """Report progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(message, status)

    def run(self, epic_id: str | None = None) -> SessionResult:
        """Execute a full session.

        Orchestrates the complete lifecycle: session creation, preflight checks,
        task execution, postflight checks, and status tracking.

        Args:
            epic_id: Optional epic ID to filter tasks.

        Returns:
            SessionResult with final status and statistics.
        """
        session = self._create_session(epic_id)
        try:
            preflight_result = self._run_preflight_phase(session)
            if not preflight_result.passed:
                return self._fail_session(session, preflight_result.errors, "Preflight")

            tasks_result = self._execute_tasks_phase(session, epic_id)
            if isinstance(tasks_result, SessionResult):
                return tasks_result
            tasks_completed, tasks_failed = tasks_result

            postflight_result = self._run_postflight_phase(session)
            if not postflight_result.passed:
                return self._fail_session(session, postflight_result.errors, "Postflight")

            return self._complete_session(session, tasks_completed, tasks_failed)
        except Exception as e:
            return self._handle_unexpected_error(session, e)

    def _create_session(self, epic_id: str | None) -> Session:
        """Create and initialize a new session.

        Args:
            epic_id: Optional epic ID to filter tasks.

        Returns:
            Newly created session record.
        """
        session_id = str(uuid.uuid4().hex)
        branch_name = self._get_current_branch()

        session = Session(
            id=session_id,
            branch_name=branch_name,
            status="running",
            started_at=datetime.now(),
            epic_id=epic_id,
        )
        self.session_repo.create(session)
        self.logger.info("session_created", session_id=session_id, branch=branch_name)
        return session

    def _run_preflight_phase(self, session: Session) -> PreflightResult:
        """Run preflight checks and record the passed timestamp.

        Args:
            session: Session to update with preflight results.

        Returns:
            PreflightResult with check details.
        """
        self._report("Running preflight checks...")
        preflight_result = self.run_preflight(self.config)

        # Report individual check results
        for name, check in preflight_result.checks.items():
            status = "pass" if check.passed else "fail"
            msg = f"{name}"
            if not check.passed and check.error:
                # Truncate long errors for display
                error_preview = check.error[:200] + "..." if len(check.error) > 200 else check.error
                msg = f"{name}: {error_preview}"
            self._report(msg, status)

        if preflight_result.passed:
            session.preflight_passed_at = datetime.now()
            self.session_repo.update(session)
            self.logger.info("preflight_passed", session_id=session.id)
            self._report("Preflight checks passed", "pass")
        else:
            self._report("Preflight checks failed", "fail")

        return preflight_result

    def _execute_tasks_phase(
        self, session: Session, epic_id: str | None
    ) -> tuple[int, int] | SessionResult:
        """Execute all tasks in the session.

        Args:
            session: Session record to update with progress.
            epic_id: Optional epic ID to filter tasks.

        Returns:
            Tuple of (tasks_completed, tasks_failed) if successful, or
            SessionResult with halted status if a task fails.
        """
        tasks = self.get_tasks(epic_id=epic_id)
        self.logger.info(
            "tasks_retrieved",
            session_id=session.id,
            task_count=len(tasks),
        )

        if tasks:
            self._report(f"Executing {len(tasks)} task(s)...")
        else:
            self._report("No tasks to execute", "skip")

        tasks_completed = 0
        tasks_failed = 0

        for task in tasks:
            try:
                self.execute_task(task, session.id)
                tasks_completed += 1
            except Exception as e:
                tasks_failed += 1
                error_msg = str(e)
                self.logger.error(
                    "task_execution_failed",
                    session_id=session.id,
                    task_id=task.id,
                    error=error_msg,
                )

                # HALT on task failure
                session.status = "halted"
                session.halt_reason = error_msg
                session.ended_at = datetime.now()
                self.session_repo.update(session)

                return SessionResult(
                    session_id=session.id,
                    status="halted",
                    tasks_completed=tasks_completed,
                    tasks_failed=tasks_failed,
                    error=f"Task {task.id} failed: {error_msg}",
                )

        return tasks_completed, tasks_failed

    def _run_postflight_phase(self, session: Session) -> PostflightResult:
        """Run postflight checks.

        Args:
            session: Session record (for context only).

        Returns:
            PostflightResult with check details.
        """
        self._report("Running postflight checks...")
        postflight_result = self.run_postflight(self.config)

        # Report individual check results
        for name, check in postflight_result.checks.items():
            status = "pass" if check.passed else "fail"
            msg = f"{name}"
            if not check.passed and check.error:
                # Truncate long errors for display
                error_preview = check.error[:200] + "..." if len(check.error) > 200 else check.error
                msg = f"{name}: {error_preview}"
            self._report(msg, status)

        if postflight_result.passed:
            self._report("Postflight checks passed", "pass")
        else:
            self._report("Postflight checks failed", "fail")

        return postflight_result

    def _complete_session(
        self, session: Session, tasks_completed: int, tasks_failed: int
    ) -> SessionResult:
        """Mark session as completed and return final result.

        Args:
            session: Session to complete.
            tasks_completed: Number of tasks completed successfully.
            tasks_failed: Number of tasks that failed.

        Returns:
            SessionResult with completed status.
        """
        session.status = "completed"
        session.ended_at = datetime.now()
        self.session_repo.update(session)
        self.logger.info(
            "session_completed",
            session_id=session.id,
            tasks_completed=tasks_completed,
        )

        return SessionResult(
            session_id=session.id,
            status="completed",
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            error=None,
        )

    def _fail_session(
        self,
        session: Session,
        errors: list[str],
        phase: str,
    ) -> SessionResult:
        """Handle session failure in a phase.

        Args:
            session: Session to fail.
            errors: List of error messages from the phase.
            phase: Name of the phase that failed (e.g., "Preflight").

        Returns:
            SessionResult with failed status.
        """
        self.logger.warning(
            f"{phase.lower()}_failed",
            session_id=session.id,
            errors=errors,
        )
        session.status = "failed"
        session.ended_at = datetime.now()
        self.session_repo.update(session)

        return SessionResult(
            session_id=session.id,
            status="failed",
            tasks_completed=0,
            tasks_failed=0,
            error=f"{phase} checks failed: {'; '.join(errors)}",
        )

    def _handle_unexpected_error(self, session: Session, error: Exception) -> SessionResult:
        """Handle unexpected errors during session execution.

        Args:
            session: Session to fail.
            error: Exception that occurred.

        Returns:
            SessionResult with failed status and error message.
        """
        self.logger.error(
            "session_error",
            session_id=session.id,
            error=str(error),
        )
        session.status = "failed"
        session.ended_at = datetime.now()
        self.session_repo.update(session)

        return SessionResult(
            session_id=session.id,
            status="failed",
            tasks_completed=0,
            tasks_failed=0,
            error=str(error),
        )

    def _get_current_branch(self) -> str:
        """Get the current git branch name.

        Returns:
            The current branch name, or 'unknown' if unable to determine.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            # Git command not found
            pass
        return "unknown"

    def run_preflight(self, config: Config) -> PreflightResult:
        """Run preflight checks.

        Args:
            config: Configuration object.

        Returns:
            PreflightResult with check details.
        """
        return run_preflight(config)

    def run_postflight(self, config: Config) -> PostflightResult:
        """Run postflight checks.

        Args:
            config: Configuration object.

        Returns:
            PostflightResult with check details.
        """
        return run_postflight(config)

    def get_tasks(self, epic_id: str | None = None) -> list[Task]:
        """Get tasks to execute.

        Fetches open tasks from the tracker. Only returns tasks that are
        ready to work on (no blocking dependencies).

        Args:
            epic_id: Optional epic ID to filter tasks.

        Returns:
            List of tasks to execute.
        """
        if self.tracker is None:
            return []

        # Get all open tasks, filtering by epic if specified
        tasks = self.tracker.list_tasks(status="open", epic_id=epic_id)

        # Filter to only non-epic tasks (we execute tasks, not epics)
        tasks = [t for t in tasks if t.task_type != "epic"]

        return tasks

    def execute_task(self, task: Task, session_id: str) -> None:
        """Execute a single task.

        Orchestrates the full task lifecycle through initialization, execution,
        and result handling.

        Args:
            task: Task to execute.
            session_id: ID of the current session.

        Raises:
            HaltError: If task execution fails or review halts execution.
        """
        self.logger.info(
            "task_execution_start",
            task_id=task.id,
            session_id=session_id,
        )

        task_exec = self._create_task_execution_record(task, session_id)

        try:
            executor = self._initialize_agents_and_executor()
            postflight_result = self._run_task_with_executor(executor, task)
            self._handle_postflight_result(task, task_exec, session_id, postflight_result)
            self.logger.info(
                "task_execution_complete",
                task_id=task.id,
                session_id=session_id,
                status="success",
            )
        except HaltError:
            raise
        except Exception as e:
            self._handle_task_execution_error(task, task_exec, session_id, e)

    def _create_task_execution_record(self, task: Any, session_id: str) -> TaskExecution:
        """Create a TaskExecution record for tracking.

        Args:
            task: Task to create record for.
            session_id: ID of the current session.

        Returns:
            Created TaskExecution record.
        """
        task_exec_id = str(uuid.uuid4().hex)
        task_exec = TaskExecution(
            id=task_exec_id,
            task_id=task.id,
            phase="preflight",
            status="running",
            started_at=datetime.now(),
            session_id=session_id,
        )
        self.task_repo.create(task_exec)
        return task_exec

    def _initialize_agents_and_executor(self) -> TaskExecutor:
        """Initialize agents, tracker, and executor for task execution.

        Returns:
            Configured TaskExecutor instance.

        Raises:
            ValueError: If prompt_repo is not configured.
        """
        if self.prompt_repo is None:
            raise ValueError("prompt_repo must be configured for task execution")

        from jiro.agents.base import AgentConfig

        # Create agent config for task execution
        agent_config = AgentConfig(
            model=self.config.models.execution,
            system_prompt="You are an expert software engineer executing tasks with TDD discipline.",
        )

        client = AgentClient(config=agent_config, repository=self.prompt_repo)
        planning_agent = PlanningAgent(client)
        review_agent = ReviewAgent(client, self.config)
        tracker = self.tracker or BeadsTracker(Path.cwd())

        return TaskExecutor(
            config=self.config,
            planning_agent=planning_agent,
            review_agent=review_agent,
            tracker=tracker,
        )

    def _run_task_with_executor(self, executor: TaskExecutor, task: Any) -> Any:
        """Execute task asynchronously using the executor.

        Args:
            executor: TaskExecutor instance.
            task: Task to execute.

        Returns:
            Postflight result from task execution.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(executor.execute_task(task))

    def _handle_postflight_result(
        self,
        task: Any,
        task_exec: TaskExecution,
        session_id: str,
        postflight_result: Any,
    ) -> None:
        """Process postflight result and validate task execution.

        Updates task execution record with results and raises HaltError if
        review or postflight checks failed.

        Args:
            task: Task that was executed.
            task_exec: TaskExecution record to update.
            session_id: ID of the current session.
            postflight_result: Result from task execution.

        Raises:
            HaltError: If review or postflight checks failed.
        """
        task_exec.phase = "postflight"

        # Determine overall status
        if (
            postflight_result.review_passed
            and postflight_result.tests_passed
            and postflight_result.lint_passed
        ):
            task_exec.status = "success"
        else:
            task_exec.status = "failed"
            error_parts = []
            if not postflight_result.review_passed:
                error_parts.append("Review failed")
            if not postflight_result.tests_passed:
                error_parts.append("Tests failed")
            if not postflight_result.lint_passed:
                error_parts.append("Lint failed")
            task_exec.halt_reason = "; ".join(error_parts)

        task_exec.ended_at = datetime.now()
        self.task_repo.update(task_exec)

        # Check for review failure
        if not postflight_result.review_passed:
            error_msg = f"Task {task.id} review failed: {postflight_result.error}"
            self.logger.error(
                "task_execution_review_failed",
                task_id=task.id,
                session_id=session_id,
                error=postflight_result.error,
            )
            raise HaltError(error_msg)

        # Check for postflight failure
        if task_exec.status == "failed":
            error_msg = f"Task {task.id} postflight checks failed: {task_exec.halt_reason}"
            self.logger.error(
                "task_execution_postflight_failed",
                task_id=task.id,
                session_id=session_id,
                reason=task_exec.halt_reason,
            )
            raise HaltError(error_msg)

    def _handle_task_execution_error(
        self,
        task: Any,
        task_exec: TaskExecution,
        session_id: str,
        error: Exception,
    ) -> None:
        """Handle errors during task execution.

        Updates task execution record with error information and logs the failure.

        Args:
            task: Task that failed.
            task_exec: TaskExecution record to update.
            session_id: ID of the current session.
            error: Exception that occurred.

        Raises:
            HaltError: Always raises HaltError wrapping the original error.
        """
        task_exec.phase = "executing"
        task_exec.status = "failed"
        task_exec.halt_reason = str(error)
        task_exec.ended_at = datetime.now()
        self.task_repo.update(task_exec)

        self.logger.error(
            "task_execution_failed",
            task_id=task.id,
            session_id=session_id,
            error=str(error),
        )
        raise HaltError(f"Task execution failed: {str(error)}") from error

    def halt(self, session: Session, halt_reason: str) -> None:
        """Halt the session and record the reason.

        Updates session status to 'halted' and records the halt reason.
        Also logs the halt with full context.

        Args:
            session: The session to halt.
            halt_reason: The reason the session is being halted.
        """
        session.status = "halted"
        session.halt_reason = halt_reason
        session.ended_at = datetime.now()
        self.session_repo.update(session)

        self.logger.error(
            "session_halted",
            session_id=session.id,
            halt_reason=halt_reason,
        )
