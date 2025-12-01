"""Health checks for jiro installation and configuration."""

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from jiro.config.loader import load_config
from jiro.core.session import CheckResult


@dataclass
class DoctorResult:
    """Result of running all doctor checks.

    Attributes:
        passed: Whether all checks passed.
        checks: Dictionary mapping check names to CheckResult objects.
        errors: List of error messages from failed checks.
    """

    passed: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def check_python_version() -> CheckResult:
    """Check if Python version meets minimum requirements (3.10+).

    Returns:
        CheckResult indicating if Python version is >= 3.10.
    """
    try:
        version_info = sys.version_info
        passed = version_info.major > 3 or (version_info.major == 3 and version_info.minor >= 10)

        if passed:
            return CheckResult(
                name="python_version",
                passed=True,
            )
        else:
            return CheckResult(
                name="python_version",
                passed=False,
                error=f"Python {version_info.major}.{version_info.minor} detected, but 3.10+ required",
            )
    except Exception as e:
        return CheckResult(
            name="python_version",
            passed=False,
            error=f"Error checking Python version: {str(e)}",
        )


def check_claude_sdk() -> CheckResult:
    """Check if Anthropic Claude SDK is installed and importable.

    Returns:
        CheckResult indicating if anthropic SDK is available.
    """
    try:
        import anthropic  # noqa: F401

        return CheckResult(
            name="claude_sdk",
            passed=True,
        )
    except ImportError as e:
        return CheckResult(
            name="claude_sdk",
            passed=False,
            error=f"Anthropic SDK not installed: {str(e)}",
        )
    except Exception as e:
        return CheckResult(
            name="claude_sdk",
            passed=False,
            error=f"Error checking Anthropic SDK: {str(e)}",
        )


def check_api_key() -> CheckResult:
    """Check if ANTHROPIC_API_KEY environment variable is set.

    Returns:
        CheckResult indicating if API key is configured.
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

        if api_key:
            return CheckResult(
                name="api_key",
                passed=True,
            )
        else:
            return CheckResult(
                name="api_key",
                passed=False,
                error="ANTHROPIC_API_KEY environment variable not set",
            )
    except Exception as e:
        return CheckResult(
            name="api_key",
            passed=False,
            error=f"Error checking API key: {str(e)}",
        )


def check_git() -> CheckResult:
    """Check if git is installed and accessible.

    Returns:
        CheckResult indicating if git is available.
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return CheckResult(
                name="git",
                passed=True,
            )
        else:
            return CheckResult(
                name="git",
                passed=False,
                error="git command not found or not working",
            )
    except Exception as e:
        return CheckResult(
            name="git",
            passed=False,
            error=f"Error checking git: {str(e)}",
        )


def check_test_command(config) -> CheckResult:
    """Check if the configured test command works.

    Args:
        config: Configuration object with test command.

    Returns:
        CheckResult indicating if test command is functional.
    """
    try:
        test_command = config.commands.test
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        if result.returncode == 0:
            return CheckResult(
                name="test_command",
                passed=True,
            )
        else:
            return CheckResult(
                name="test_command",
                passed=False,
                error=f"Test command failed with exit code {result.returncode}",
            )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="test_command",
            passed=False,
            error="Test command timed out",
        )
    except Exception as e:
        return CheckResult(
            name="test_command",
            passed=False,
            error=f"Error running test command: {str(e)}",
        )


def check_lint_command(config) -> CheckResult:
    """Check if the configured lint command works.

    Args:
        config: Configuration object with lint command.

    Returns:
        CheckResult indicating if lint command is functional.
    """
    try:
        lint_command = config.commands.lint
        result = subprocess.run(
            lint_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        if result.returncode == 0:
            return CheckResult(
                name="lint_command",
                passed=True,
            )
        else:
            return CheckResult(
                name="lint_command",
                passed=False,
                error=f"Lint command failed with exit code {result.returncode}",
            )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="lint_command",
            passed=False,
            error="Lint command timed out",
        )
    except Exception as e:
        return CheckResult(
            name="lint_command",
            passed=False,
            error=f"Error running lint command: {str(e)}",
        )


def check_beads() -> CheckResult:
    """Check if bd (beads) CLI tool is installed and accessible.

    Returns:
        CheckResult indicating if beads is available.
    """
    try:
        result = subprocess.run(
            ["bd", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return CheckResult(
                name="beads",
                passed=True,
            )
        else:
            return CheckResult(
                name="beads",
                passed=False,
                error="bd (beads) command not found or not working",
            )
    except Exception as e:
        return CheckResult(
            name="beads",
            passed=False,
            error=f"Error checking beads: {str(e)}",
        )


def check_config(project_root: Path | None = None) -> CheckResult:
    """Check if project configuration can be loaded.

    Args:
        project_root: Optional project root path. Defaults to current directory.

    Returns:
        CheckResult indicating if config loads successfully.
    """
    try:
        if project_root is None:
            project_root = Path.cwd()
        project_name = project_root.name
        _ = load_config(project_root, project_name)

        return CheckResult(
            name="config",
            passed=True,
        )
    except FileNotFoundError as e:
        return CheckResult(
            name="config",
            passed=False,
            error=f"Config file not found: {str(e)}",
        )
    except Exception as e:
        return CheckResult(
            name="config",
            passed=False,
            error=f"Error loading config: {str(e)}",
        )


def check_directories(project_root: Path | None = None) -> CheckResult:
    """Check if required project directories exist.

    Args:
        project_root: Optional project root path. Defaults to current directory.

    Returns:
        CheckResult indicating if directories are present.
    """
    try:
        if project_root is None:
            project_root = Path.cwd()

        required_dirs = [
            project_root / "src",
            project_root / "tests",
        ]

        missing = [d for d in required_dirs if not d.exists()]

        if not missing:
            return CheckResult(
                name="directories",
                passed=True,
            )
        else:
            missing_paths = ", ".join(str(d) for d in missing)
            return CheckResult(
                name="directories",
                passed=False,
                error=f"Required directories missing: {missing_paths}",
            )
    except Exception as e:
        return CheckResult(
            name="directories",
            passed=False,
            error=f"Error checking directories: {str(e)}",
        )


def run_doctor(project_root: Path | None = None) -> DoctorResult:
    """Run all doctor health checks.

    Orchestrates all doctor checks and returns a comprehensive result
    with details about each check.

    Args:
        project_root: Optional project root path. Defaults to current directory.

    Returns:
        DoctorResult containing results of all checks and overall status.
    """
    logger = structlog.get_logger()

    if project_root is None:
        project_root = Path.cwd()

    checks: dict[str, CheckResult] = {}
    errors: list[str] = []

    # Load config once for commands checks
    try:
        project_name = project_root.name
        config = load_config(project_root, project_name)
    except Exception:
        # Config loading error will be caught by check_config
        config = None

    # Run check_python_version
    try:
        result = check_python_version()
        checks["python_version"] = result
        if not result.passed:
            errors.append(f"python_version: {result.error}")
    except Exception as e:
        checks["python_version"] = CheckResult(
            name="python_version",
            passed=False,
            error=str(e),
        )
        errors.append(f"python_version: {str(e)}")

    # Run check_claude_sdk
    try:
        result = check_claude_sdk()
        checks["claude_sdk"] = result
        if not result.passed:
            errors.append(f"claude_sdk: {result.error}")
    except Exception as e:
        checks["claude_sdk"] = CheckResult(
            name="claude_sdk",
            passed=False,
            error=str(e),
        )
        errors.append(f"claude_sdk: {str(e)}")

    # Run check_api_key
    try:
        result = check_api_key()
        checks["api_key"] = result
        if not result.passed:
            errors.append(f"api_key: {result.error}")
    except Exception as e:
        checks["api_key"] = CheckResult(
            name="api_key",
            passed=False,
            error=str(e),
        )
        errors.append(f"api_key: {str(e)}")

    # Run check_git
    try:
        result = check_git()
        checks["git"] = result
        if not result.passed:
            errors.append(f"git: {result.error}")
    except Exception as e:
        checks["git"] = CheckResult(
            name="git",
            passed=False,
            error=str(e),
        )
        errors.append(f"git: {str(e)}")

    # Run check_test_command
    try:
        if config:
            result = check_test_command(config)
        else:
            result = CheckResult(
                name="test_command",
                passed=False,
                error="Config not available",
            )
        checks["test_command"] = result
        if not result.passed:
            errors.append(f"test_command: {result.error}")
    except Exception as e:
        checks["test_command"] = CheckResult(
            name="test_command",
            passed=False,
            error=str(e),
        )
        errors.append(f"test_command: {str(e)}")

    # Run check_lint_command
    try:
        if config:
            result = check_lint_command(config)
        else:
            result = CheckResult(
                name="lint_command",
                passed=False,
                error="Config not available",
            )
        checks["lint_command"] = result
        if not result.passed:
            errors.append(f"lint_command: {result.error}")
    except Exception as e:
        checks["lint_command"] = CheckResult(
            name="lint_command",
            passed=False,
            error=str(e),
        )
        errors.append(f"lint_command: {str(e)}")

    # Run check_beads
    try:
        result = check_beads()
        checks["beads"] = result
        if not result.passed:
            errors.append(f"beads: {result.error}")
    except Exception as e:
        checks["beads"] = CheckResult(
            name="beads",
            passed=False,
            error=str(e),
        )
        errors.append(f"beads: {str(e)}")

    # Run check_config
    try:
        result = check_config(project_root)
        checks["config"] = result
        if not result.passed:
            errors.append(f"config: {result.error}")
    except Exception as e:
        checks["config"] = CheckResult(
            name="config",
            passed=False,
            error=str(e),
        )
        errors.append(f"config: {str(e)}")

    # Run check_directories
    try:
        result = check_directories(project_root)
        checks["directories"] = result
        if not result.passed:
            errors.append(f"directories: {result.error}")
    except Exception as e:
        checks["directories"] = CheckResult(
            name="directories",
            passed=False,
            error=str(e),
        )
        errors.append(f"directories: {str(e)}")

    # Determine overall result
    all_passed = all(check.passed for check in checks.values())

    # Create result
    result = DoctorResult(passed=all_passed, checks=checks, errors=errors)

    # Log results
    logger.info(
        "doctor_checks_completed",
        passed=all_passed,
        checks={name: check.passed for name, check in checks.items()},
        errors=errors if errors else None,
    )

    return result
