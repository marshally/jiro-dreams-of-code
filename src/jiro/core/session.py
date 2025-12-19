"""Session preflight checks for jiro workflow."""

import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from jiro.config.schema import Config
from jiro.db.models import Session, SessionStatus
from jiro.db.repository import SessionRepository, TaskExecutionRepository


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
    except Exception:
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
        target_branch = getattr(config.preflight, "target_branch", None)
        if target_branch is None:
            # No target branch specified, so always pass
            return True

        return bool(current_branch == target_branch)
    except Exception:
        return False


def check_up_to_date() -> bool:
    """Check if the local repository is up to date with origin.

    Performs git fetch and compares local HEAD with origin/HEAD.

    Returns:
        True if up to date with origin, False otherwise.
    """
    try:
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
    except Exception:
        return False


def check_tests_pass(config: Config) -> bool:
    """Check if all tests pass.

    Args:
        config: Configuration object containing test command.

    Returns:
        True if tests pass, False otherwise.
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
        return result.returncode == 0
    except Exception:
        return False


def check_lint_pass(config: Config) -> bool:
    """Check if linting passes.

    Args:
        config: Configuration object containing lint command.

    Returns:
        True if lint passes, False otherwise.
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
    except Exception:
        return False


def run_preflight(config: Config) -> PreflightResult:
    """Run all preflight checks.

    Orchestrates all preflight checks and returns a comprehensive result
    with details about each check.

    Args:
        config: Configuration object with check settings.

    Returns:
        PreflightResult containing results of all checks and overall status.
    """
    logger = structlog.get_logger()

    checks: dict[str, CheckResult] = {}
    errors: list[str] = []

    # Run check_git_clean
    try:
        git_clean = check_git_clean()
        checks["git_clean"] = CheckResult(
            name="git_clean",
            passed=git_clean,
            error=None if git_clean else "Uncommitted changes detected",
        )
        if not git_clean:
            errors.append("git_clean: Uncommitted changes detected")
    except Exception as e:
        checks["git_clean"] = CheckResult(
            name="git_clean",
            passed=False,
            error=str(e),
        )
        errors.append(f"git_clean: {str(e)}")

    # Run check_correct_branch
    try:
        correct_branch = check_correct_branch(config)
        checks["correct_branch"] = CheckResult(
            name="correct_branch",
            passed=correct_branch,
            error=None if correct_branch else "Not on correct branch",
        )
        if not correct_branch:
            errors.append("correct_branch: Not on correct branch")
    except Exception as e:
        checks["correct_branch"] = CheckResult(
            name="correct_branch",
            passed=False,
            error=str(e),
        )
        errors.append(f"correct_branch: {str(e)}")

    # Run check_up_to_date
    try:
        up_to_date = check_up_to_date()
        checks["up_to_date"] = CheckResult(
            name="up_to_date",
            passed=up_to_date,
            error=None if up_to_date else "Not up to date with origin",
        )
        if not up_to_date:
            errors.append("up_to_date: Not up to date with origin")
    except Exception as e:
        checks["up_to_date"] = CheckResult(
            name="up_to_date",
            passed=False,
            error=str(e),
        )
        errors.append(f"up_to_date: {str(e)}")

    # Run check_tests_pass
    try:
        tests_pass = check_tests_pass(config)
        checks["tests_pass"] = CheckResult(
            name="tests_pass",
            passed=tests_pass,
            error=None if tests_pass else "Tests failed",
        )
        if not tests_pass:
            errors.append("tests_pass: Tests failed")
    except Exception as e:
        checks["tests_pass"] = CheckResult(
            name="tests_pass",
            passed=False,
            error=str(e),
        )
        errors.append(f"tests_pass: {str(e)}")

    # Run check_lint_pass
    try:
        lint_pass = check_lint_pass(config)
        checks["lint_pass"] = CheckResult(
            name="lint_pass",
            passed=lint_pass,
            error=None if lint_pass else "Linting failed",
        )
        if not lint_pass:
            errors.append("lint_pass: Linting failed")
    except Exception as e:
        checks["lint_pass"] = CheckResult(
            name="lint_pass",
            passed=False,
            error=str(e),
        )
        errors.append(f"lint_pass: {str(e)}")

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
        True if tests pass, False otherwise.
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
        return result.returncode == 0
    except Exception:
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
    except Exception:
        return False


def push_to_origin() -> bool:
    """Push the current branch to origin.

    Returns:
        True if push succeeds, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "push", "origin", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
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
    logger = structlog.get_logger()

    checks: dict[str, CheckResult] = {}
    errors: list[str] = []

    # Run run_full_tests
    try:
        full_tests = run_full_tests(config)
        checks["full_tests"] = CheckResult(
            name="full_tests",
            passed=full_tests,
            error=None if full_tests else "Full test suite failed",
        )
        if not full_tests:
            errors.append("full_tests: Full test suite failed")
    except Exception as e:
        checks["full_tests"] = CheckResult(
            name="full_tests",
            passed=False,
            error=str(e),
        )
        errors.append(f"full_tests: {str(e)}")

    # Run run_full_lint
    try:
        full_lint = run_full_lint(config)
        checks["full_lint"] = CheckResult(
            name="full_lint",
            passed=full_lint,
            error=None if full_lint else "Full lint failed",
        )
        if not full_lint:
            errors.append("full_lint: Full lint failed")
    except Exception as e:
        checks["full_lint"] = CheckResult(
            name="full_lint",
            passed=False,
            error=str(e),
        )
        errors.append(f"full_lint: {str(e)}")

    # Run push_to_origin
    try:
        push_success = push_to_origin()
        checks["push_to_origin"] = CheckResult(
            name="push_to_origin",
            passed=push_success,
            error=None if push_success else "Push to origin failed",
        )
        if not push_success:
            errors.append("push_to_origin: Push to origin failed")
    except Exception as e:
        checks["push_to_origin"] = CheckResult(
            name="push_to_origin",
            passed=False,
            error=str(e),
        )
        errors.append(f"push_to_origin: {str(e)}")

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
    ) -> None:
        """Initialize with dependencies.

        Args:
            config: Configuration object for checks and commands.
            session_repo: Repository for session persistence.
            task_repo: Repository for task execution persistence.
        """
        self.config = config
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.logger = structlog.get_logger()

    def run(self, epic_id: str | None = None) -> SessionResult:
        """Execute a full session.

        Orchestrates the complete lifecycle:
        1. Create session record (status='running')
        2. Run preflight checks
           - If fails: update session status='failed', return
        3. Get tasks (filtered by epic_id if provided)
        4. Execute tasks in dependency order
           - For each task: create TaskExecution, run task, update status
           - On task failure: HALT, update session status='halted'
        5. Run postflight checks
           - If fails: update session status='failed'
        6. Update session status='completed'
        7. Return SessionResult

        Args:
            epic_id: Optional epic ID to filter tasks.

        Returns:
            SessionResult with final status and statistics.
        """
        # Step 1: Create session record
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

        try:
            # Step 2: Run preflight checks
            preflight_result = self.run_preflight(self.config)
            if not preflight_result.passed:
                self.logger.warning(
                    "preflight_failed",
                    session_id=session_id,
                    errors=preflight_result.errors,
                )
                session.status = "failed"
                session.ended_at = datetime.now()
                self.session_repo.update(session)

                return SessionResult(
                    session_id=session_id,
                    status="failed",
                    tasks_completed=0,
                    tasks_failed=0,
                    error=f"Preflight checks failed: {'; '.join(preflight_result.errors)}",
                )

            # Record preflight passed timestamp
            session.preflight_passed_at = datetime.now()
            self.session_repo.update(session)
            self.logger.info("preflight_passed", session_id=session_id)

            # Step 3: Get tasks
            tasks = self.get_tasks(epic_id=epic_id)
            self.logger.info(
                "tasks_retrieved",
                session_id=session_id,
                task_count=len(tasks),
            )

            # Step 4: Execute tasks
            tasks_completed = 0
            tasks_failed = 0

            for task in tasks:
                try:
                    self.execute_task(task, session_id)
                    tasks_completed += 1
                except Exception as e:
                    tasks_failed += 1
                    error_msg = str(e)
                    self.logger.error(
                        "task_execution_failed",
                        session_id=session_id,
                        task_id=task.id,
                        error=error_msg,
                    )

                    # HALT on task failure
                    session.status = "halted"
                    session.halt_reason = error_msg
                    session.ended_at = datetime.now()
                    self.session_repo.update(session)

                    return SessionResult(
                        session_id=session_id,
                        status="halted",
                        tasks_completed=tasks_completed,
                        tasks_failed=tasks_failed,
                        error=f"Task {task.id} failed: {error_msg}",
                    )

            # Step 5: Run postflight checks
            postflight_result = self.run_postflight(self.config)
            if not postflight_result.passed:
                self.logger.warning(
                    "postflight_failed",
                    session_id=session_id,
                    errors=postflight_result.errors,
                )
                session.status = "failed"
                session.ended_at = datetime.now()
                self.session_repo.update(session)

                return SessionResult(
                    session_id=session_id,
                    status="failed",
                    tasks_completed=tasks_completed,
                    tasks_failed=tasks_failed,
                    error=f"Postflight checks failed: {'; '.join(postflight_result.errors)}",
                )

            # Step 6: Update session to completed
            session.status = "completed"
            session.ended_at = datetime.now()
            self.session_repo.update(session)
            self.logger.info(
                "session_completed",
                session_id=session_id,
                tasks_completed=tasks_completed,
            )

            # Step 7: Return result
            return SessionResult(
                session_id=session_id,
                status="completed",
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                error=None,
            )

        except Exception as e:
            # Catch unexpected errors
            self.logger.error(
                "session_error",
                session_id=session_id,
                error=str(e),
            )
            session.status = "failed"
            session.ended_at = datetime.now()
            self.session_repo.update(session)

            return SessionResult(
                session_id=session_id,
                status="failed",
                tasks_completed=0,
                tasks_failed=0,
                error=str(e),
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
        except Exception:
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

    def get_tasks(self, epic_id: str | None = None) -> list[Any]:
        """Get tasks to execute.

        Args:
            epic_id: Optional epic ID to filter tasks.

        Returns:
            List of tasks to execute.
        """
        # This will be implemented to fetch from issue tracker
        # For now, return empty list for basic tests
        return []

    def execute_task(self, task: Any, session_id: str) -> None:
        """Execute a single task.

        Creates a TaskExecution record and orchestrates the full task lifecycle
        through preflight, execution, and postflight phases.

        Args:
            task: Task to execute.
            session_id: ID of the current session.

        Raises:
            HaltError: If task execution fails or review halts execution.
            Exception: If task execution fails.
        """
        import asyncio
        import uuid
        from datetime import datetime

        from jiro.agents.client import AgentClient
        from jiro.agents.planning import PlanningAgent
        from jiro.agents.review import ReviewAgent
        from jiro.core.executor import TaskExecutor
        from jiro.db.models import TaskExecution

        self.logger.info(
            "task_execution_start",
            task_id=task.id,
            session_id=session_id,
        )

        # Create a TaskExecution record
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

        try:
            # Initialize agents for this task execution
            client = AgentClient(config=self.config, repository=None)  # type: ignore[arg-type]
            planning_agent = PlanningAgent(client)
            review_agent = ReviewAgent(client, self.config)

            # Create executor
            executor = TaskExecutor(
                config=self.config,
                planning_agent=planning_agent,
                review_agent=review_agent,
            )

            # Execute the task (this is async, so we need to run it)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            postflight_result = loop.run_until_complete(executor.execute_task(task))

            # Update task execution with results
            task_exec.phase = "postflight"
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

            # If postflight failed, halt
            if not postflight_result.review_passed:
                error_msg = f"Task {task.id} review failed: {postflight_result.error}"
                self.logger.error(
                    "task_execution_review_failed",
                    task_id=task.id,
                    session_id=session_id,
                    error=postflight_result.error,
                )
                raise HaltError(error_msg)

            if task_exec.status == "failed":
                error_msg = f"Task {task.id} postflight checks failed: {task_exec.halt_reason}"
                self.logger.error(
                    "task_execution_postflight_failed",
                    task_id=task.id,
                    session_id=session_id,
                    reason=task_exec.halt_reason,
                )
                raise HaltError(error_msg)

            self.logger.info(
                "task_execution_complete",
                task_id=task.id,
                session_id=session_id,
                status="success",
            )

        except HaltError:
            # Re-raise halt errors
            raise
        except Exception as e:
            # Update task execution with error
            task_exec.phase = "executing"
            task_exec.status = "failed"
            task_exec.halt_reason = str(e)
            task_exec.ended_at = datetime.now()
            self.task_repo.update(task_exec)

            self.logger.error(
                "task_execution_failed",
                task_id=task.id,
                session_id=session_id,
                error=str(e),
            )
            raise HaltError(f"Task execution failed: {str(e)}") from e

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
