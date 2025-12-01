"""Session preflight checks for jiro workflow."""

import subprocess
from dataclasses import dataclass, field

import structlog

from jiro.config.schema import Config


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
class PreflightResult:
    """Result of running all preflight checks.

    Attributes:
        passed: Whether all checks passed.
        checks: Dictionary mapping check names to CheckResult objects.
        errors: List of error messages from failed checks.
    """

    passed: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


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

        return current_branch == target_branch
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
