"""ReviewAgent for reviewing code changes via deterministic checks and LLM."""

import json
import re
import subprocess
from dataclasses import dataclass

import structlog

from jiro.agents.client import AgentClient
from jiro.assets.loader import load_template
from jiro.config.schema import Config
from jiro.core.review_tdd import TddReviewValidator
from jiro.steps.types import StepType
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

        # Step 1: Run deterministic checks (tests, lint, TDD phase validation)
        checks_passed, check_results = self._run_deterministic_checks(commit_sha)

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

    def _run_deterministic_checks(self, commit_sha: str = "") -> tuple[bool, dict]:
        """Run deterministic checks (tests and linting).

        Args:
            commit_sha: The commit SHA being reviewed (for TDD phase validation)

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

        # Run TDD phase validation if this is a TDD step
        if commit_sha:
            step_type = self._extract_step_type_from_commit(commit_sha)
            if step_type and step_type in (
                StepType.TDD_RED,
                StepType.TDD_GREEN,
                StepType.TDD_REFACTOR,
            ):
                tdd_valid, tdd_checks = TddReviewValidator.validate_tdd_phase(step_type, commit_sha)
                check_results.update(tdd_checks)
                tests_passed = tests_passed and tdd_valid

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

    def _get_commit_message(self, commit_sha: str) -> str:
        """Get the commit message for a commit SHA.

        Args:
            commit_sha: The commit SHA.

        Returns:
            The commit message, or empty string if unable to retrieve.
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B", commit_sha],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning("get_commit_message_failed", error=str(e))
        return ""

    def _get_commit_diff(self, commit_sha: str) -> str:
        """Get the unified diff for a commit.

        Args:
            commit_sha: The commit SHA.

        Returns:
            The unified diff, or empty string if unable to retrieve.
        """
        try:
            result = subprocess.run(
                ["git", "show", commit_sha],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning("get_commit_diff_failed", error=str(e))
        return ""

    def _parse_llm_response(self, output: str) -> bool:
        """Parse LLM response to determine approval status.

        Handles both JSON and legacy text-based responses.

        Args:
            output: The LLM response text.

        Returns:
            True if approved, False if rejected.
        """
        # Try to parse as JSON first (new format)
        json_match = re.search(r"\{.*?\}", output, re.DOTALL)
        if json_match:
            try:
                response_json = json.loads(json_match.group())
                if isinstance(response_json, dict):
                    passed = response_json.get("passed", False)
                    logger.info(
                        "llm_review_json_parsed",
                        passed=passed,
                        has_concerns=bool(response_json.get("concerns")),
                    )
                    return bool(passed)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback to text-based parsing (legacy format)
        output_upper = output.upper()
        if "APPROVED" in output_upper:
            return True
        if "REJECTED" in output_upper:
            return False
        # Default to False if no clear decision
        return False

    def _extract_step_type_from_commit(self, commit_sha: str) -> StepType | None:
        """Extract step type from commit message.

        Looks for emoji prefixes: 🔴 (red), 🟢 (green), ♻️ (refactor)

        Args:
            commit_sha: The commit SHA

        Returns:
            StepType if detected, None otherwise
        """
        message = self._get_commit_message(commit_sha)

        # Map emoji to step type
        emoji_map = {
            "🔴": StepType.TDD_RED,
            "🟢": StepType.TDD_GREEN,
            "♻️": StepType.TDD_REFACTOR,
        }

        for emoji, step_type in emoji_map.items():
            if message.startswith(emoji):
                return step_type

        return None

    def _get_commit_type_context(self, step_type: StepType | None) -> str:
        """Get LLM review context specific to commit type.

        Provides type-specific validation guidance to the LLM.

        Args:
            step_type: The detected step type (TDD phase or None)

        Returns:
            Context string with type-specific validation questions
        """
        if step_type == StepType.TDD_GREEN:
            return """## TDD Green Phase Validation

This is a TDD green phase commit. In addition to scope creep detection, validate:

1. **Code Minimalism**: Is the implementation minimal and focused on making tests pass?
   - No over-engineering or premature optimization
   - No additional features not required by the tests
   - Simple, direct solution to the test requirements

2. **No Unnecessary Complexity**: Does the code avoid unnecessary:
   - Generic abstractions when specific solutions work
   - Multiple implementations when one is sufficient
   - Edge case handling not covered by tests

If the code is over-engineered or includes unnecessary complexity, mark as failed."""

        elif step_type == StepType.TDD_REFACTOR:
            return """## TDD Refactor Phase Validation

This is a TDD refactor phase commit. In addition to scope creep detection, validate:

1. **Behavior Neutrality**: Are there ANY functional changes to the code logic?
   - The refactor should NOT change behavior
   - Only improve code structure, naming, or efficiency
   - All tests should pass with the same results

2. **No Hidden Functional Changes**: Look carefully for:
   - Subtle logic changes disguised as refactoring
   - Changed algorithm implementations
   - Modified return values or side effects
   - Conditional logic alterations

If there are any functional changes (behavior-altering modifications), mark as failed."""

        else:
            # Default context for non-TDD commits
            return ""

    def _build_review_prompt(self, commit_sha: str, task: Task) -> str:
        """Build a prompt for the LLM review.

        Args:
            commit_sha: The commit SHA being reviewed.
            task: The Task being worked on.

        Returns:
            A formatted prompt for the LLM reviewer.
        """
        # Load the base prompt template
        try:
            template = load_template("review_agent.md")
            base_prompt = template.render()
        except Exception:
            # Fallback if template loading fails
            base_prompt = "You are a code review agent. Review the changes below."

        # Get commit message and diff
        commit_message = self._get_commit_message(commit_sha)
        diff = self._get_commit_diff(commit_sha)

        # Extract commit type from commit message
        step_type = self._extract_step_type_from_commit(commit_sha)
        commit_type_context = self._get_commit_type_context(step_type)

        # Truncate diff if too large (LLM context limits)
        max_diff_lines = 500
        diff_lines = diff.split("\n")
        if len(diff_lines) > max_diff_lines:
            diff = "\n".join(diff_lines[:max_diff_lines])
            diff += f"\n\n... (diff truncated, {len(diff_lines) - max_diff_lines} lines omitted)"

        # Build full prompt
        prompt = f"""{base_prompt}

## Task Context
Task ID: {task.id}
Title: {task.title}
Type: {task.task_type}
Description: {task.description or "No description"}

## Commit to Review
SHA: {commit_sha}

### Commit Message
```
{commit_message}
```

### Diff
```diff
{diff}
```

{commit_type_context}

Please analyze these changes and respond with valid JSON following the output format specified above."""

        return prompt
