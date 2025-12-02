"""ReviewAgent for reviewing code changes via deterministic checks and LLM."""

import subprocess
from dataclasses import dataclass

import structlog

from jiro.agents.client import AgentClient
from jiro.config.schema import Config
from jiro.trackers.interface import Task

logger = structlog.get_logger()


@dataclass
class ReviewResult:
    """Result from reviewing code changes.

    Contains overall success status, halt flag, reason for decision,
    and detailed check results.
    """

    passed: bool
    halt: bool
    reason: str
    checks: dict


class ReviewAgent:
    """Agent that reviews code changes using deterministic checks and LLM.

    Takes a commit SHA and task, runs deterministic checks (tests, lint),
    then runs LLM review if deterministic checks pass. Returns HALT if
    any violation is found.
    """

    def __init__(self, client: AgentClient, config: Config) -> None:
        """Initialize ReviewAgent.

        Args:
            client: AgentClient instance for executing LLM review.
            config: Configuration for review behavior.

        Raises:
            TypeError: If client or config are None.
        """
        if client is None:
            raise TypeError("client cannot be None")
        if config is None:
            raise TypeError("config cannot be None")

        self.client = client
        self.config = config

    async def review(self, commit_sha: str, task: Task) -> ReviewResult:
        """Review code changes for a commit.

        Takes a commit SHA and task, runs deterministic checks first (tests, lint),
        then runs LLM review if deterministic checks pass.

        Args:
            commit_sha: The git commit SHA to review.
            task: The Task being worked on.

        Returns:
            A ReviewResult containing the review decision and details.
        """
        logger.info(
            "review_agent_review_start",
            commit_sha=commit_sha,
            task_id=task.id,
        )

        # Step 1: Run deterministic checks (tests, lint)
        checks_passed, check_results = self._run_deterministic_checks()

        # Step 2: If deterministic checks fail, HALT
        if not checks_passed:
            logger.warning(
                "review_agent_deterministic_check_failed",
                commit_sha=commit_sha,
                task_id=task.id,
                check_results=check_results,
            )
            return ReviewResult(
                passed=False,
                halt=True,
                reason="Deterministic checks failed",
                checks=check_results,
            )

        # Step 3: Run LLM review if deterministic checks pass
        logger.info(
            "review_agent_llm_review_start",
            commit_sha=commit_sha,
            task_id=task.id,
        )

        prompt = self._build_review_prompt(commit_sha, task)
        llm_result = await self.client.execute(prompt)

        # Step 4: Check LLM result
        if not llm_result.success:
            logger.error(
                "review_agent_llm_execution_failed",
                commit_sha=commit_sha,
                task_id=task.id,
                error=llm_result.error,
            )
            return ReviewResult(
                passed=False,
                halt=True,
                reason="LLM review execution failed",
                checks={**check_results, "llm": f"ERROR: {llm_result.error}"},
            )

        # Step 5: Parse LLM response for APPROVED/REJECTED
        is_approved = self._parse_llm_response(llm_result.output)

        if not is_approved:
            logger.warning(
                "review_agent_llm_rejected",
                commit_sha=commit_sha,
                task_id=task.id,
                feedback=llm_result.output,
            )
            return ReviewResult(
                passed=False,
                halt=True,
                reason="LLM review rejected changes",
                checks={**check_results, "llm": "REJECTED"},
            )

        # Step 6: All checks passed
        logger.info(
            "review_agent_review_approved",
            commit_sha=commit_sha,
            task_id=task.id,
        )

        return ReviewResult(
            passed=True,
            halt=False,
            reason="All checks passed",
            checks={**check_results, "llm": "APPROVED"},
        )

    def _run_deterministic_checks(self) -> tuple[bool, dict]:
        """Run deterministic checks (tests and linting).

        Returns:
            A tuple of (all_passed: bool, check_results: dict)
        """
        check_results = {}

        # Run tests
        tests_passed = self._run_tests()
        check_results["tests"] = "PASSED" if tests_passed else "FAILED"

        # Run linting
        lint_passed = self._run_lint()
        check_results["lint"] = "PASSED" if lint_passed else "FAILED"

        all_passed = tests_passed and lint_passed
        return all_passed, check_results

    def _run_tests(self) -> bool:
        """Run tests using configured test command.

        Returns:
            True if tests passed, False otherwise.
        """
        try:
            result = subprocess.run(
                self.config.commands.test,
                shell=True,
                capture_output=True,
                timeout=300,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("tests_timeout")
            return False
        except Exception as e:
            logger.error("tests_error", error=str(e))
            return False

    def _run_lint(self) -> bool:
        """Run linting checks using configured lint command.

        Returns:
            True if linting passed, False otherwise.
        """
        try:
            result = subprocess.run(
                self.config.commands.lint,
                shell=True,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("lint_timeout")
            return False
        except Exception as e:
            logger.error("lint_error", error=str(e))
            return False

    def _parse_llm_response(self, output: str) -> bool:
        """Parse LLM response to determine approval status.

        Args:
            output: The LLM response text.

        Returns:
            True if approved, False if rejected.
        """
        output_upper = output.upper()
        if "APPROVED" in output_upper:
            return True
        if "REJECTED" in output_upper:
            return False
        # Default to approval if no clear decision
        return "APPROVED" in output_upper

    def _build_review_prompt(self, commit_sha: str, task: Task) -> str:
        """Build a prompt for the LLM review.

        Args:
            commit_sha: The commit SHA being reviewed.
            task: The Task being worked on.

        Returns:
            A formatted prompt for the LLM reviewer.
        """
        prompt = f"""You are a code reviewer evaluating changes for semantic correctness and quality.

## Task Context
Task ID: {task.id}
Title: {task.title}
Type: {task.task_type}
Description: {task.description or 'No description'}

## Commit to Review
Commit SHA: {commit_sha}

## Your Review Task

Please review the code changes in this commit and determine if:
1. The changes align with the task requirements
2. The code follows best practices and conventions
3. Error handling is appropriate
4. The implementation is complete and correct

Respond with either:
- APPROVED: If the code is ready to merge
- REJECTED: With explanation of what needs to be fixed

Be concise and specific in your feedback."""

        return prompt
