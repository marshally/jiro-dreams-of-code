"""Deterministic commit review checks.

These checks run before LLM review to catch obvious violations quickly.
"""

import re
import subprocess
from dataclasses import dataclass

# File extensions allowed for docs commits
DOCS_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}

# Valid commit prefixes
VALID_PREFIXES = {
    "📝",  # docs
    "🧪",  # TDD
    "♻️",  # refactor
    "🐛",  # bug fix
    "🔧",  # config
    "🧹",  # lint
    "⚡",  # performance
}


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    error: str | None = None


@dataclass
class ReviewResult:
    """Result of a single deterministic review check.

    Used for individual checks that run before LLM review.
    """

    passed: bool
    check_name: str
    message: str


def verify_commit_files(files: list[str], commit_type: str) -> ValidationResult:
    """Verify that commit files match the claimed commit type.

    Args:
        files: List of file paths modified in the commit.
        commit_type: The claimed commit type (docs, tdd_green, etc.).

    Returns:
        ValidationResult indicating if files match the type.
    """
    if commit_type == "docs":
        invalid_files = []
        for file_path in files:
            ext = _get_extension(file_path)
            if ext not in DOCS_EXTENSIONS:
                invalid_files.append(file_path)

        if invalid_files:
            return ValidationResult(
                is_valid=False,
                error=f"Docs commit contains non-documentation files: {', '.join(invalid_files)}",
            )

    # Other commit types allow any files for now
    return ValidationResult(is_valid=True)


def verify_commit_message(message: str) -> ValidationResult:
    """Verify that commit message follows conventions.

    Args:
        message: The commit message to validate.

    Returns:
        ValidationResult indicating if message is valid.
    """
    if not message or not message.strip():
        return ValidationResult(
            is_valid=False,
            error="Commit message cannot be empty",
        )

    # Check for emoji prefix
    has_valid_prefix = any(message.startswith(prefix) for prefix in VALID_PREFIXES)

    # Also allow conventional commit style (feat:, fix:, docs:, etc.)
    conventional_pattern = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?:"
    has_conventional = bool(re.match(conventional_pattern, message))

    if not has_valid_prefix and not has_conventional:
        return ValidationResult(
            is_valid=False,
            error="Commit message must start with a valid emoji prefix or conventional commit type",
        )

    return ValidationResult(is_valid=True)


def verify_task_reference(message: str, task_id: str) -> ValidationResult:
    """Verify that commit message references the correct task.

    Args:
        message: The commit message.
        task_id: The expected task ID.

    Returns:
        ValidationResult indicating if task reference is valid.
    """
    if task_id not in message:
        return ValidationResult(
            is_valid=False,
            error=f"Commit message does not reference task {task_id}",
        )

    return ValidationResult(is_valid=True)


def _get_extension(file_path: str) -> str:
    """Get file extension from path."""
    if "." not in file_path:
        return ""
    return "." + file_path.rsplit(".", 1)[-1].lower()


def verify_only_docs_files_changed(
    commit_sha: str, project_root: str | None = None
) -> ReviewResult:
    """Verify that commit only changes documentation files.

    For documentation commits, verify that only .md, .txt, .rst, .adoc files
    were changed, or that changes are in docstrings/comments only.

    Args:
        commit_sha: The git commit SHA to check.
        project_root: Optional project root directory for git commands.

    Returns:
        ReviewResult indicating if commit only changed docs files.
    """
    try:
        # Get list of files changed in the commit
        cmd = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha]
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return ReviewResult(
                passed=False,
                check_name="verify_only_docs_files_changed",
                message=f"Failed to get changed files for commit {commit_sha}",
            )

        changed_files = result.stdout.strip().split("\n")
        changed_files = [f for f in changed_files if f]  # Remove empty lines

        # Check if all changed files are documentation files
        non_docs_files = []
        for file_path in changed_files:
            ext = _get_extension(file_path)
            if ext not in DOCS_EXTENSIONS:
                non_docs_files.append(file_path)

        if non_docs_files:
            return ReviewResult(
                passed=False,
                check_name="verify_only_docs_files_changed",
                message=f"Commit contains non-documentation files: {', '.join(non_docs_files)}",
            )

        return ReviewResult(
            passed=True,
            check_name="verify_only_docs_files_changed",
            message="All changed files are documentation files",
        )

    except subprocess.TimeoutExpired:
        return ReviewResult(
            passed=False,
            check_name="verify_only_docs_files_changed",
            message="Git command timed out",
        )
    except Exception as e:
        return ReviewResult(
            passed=False,
            check_name="verify_only_docs_files_changed",
            message=f"Error checking changed files: {str(e)}",
        )


def verify_commit_message_format(message: str) -> ReviewResult:
    """Verify that commit message follows conventions and includes task reference.

    Checks for:
    1. Emoji prefix (📝) or conventional commit (docs:)
    2. Includes Task: reference
    3. Includes Type: documentation

    Args:
        message: The commit message to validate.

    Returns:
        ReviewResult indicating if message format is valid.
    """
    if not message or not message.strip():
        return ReviewResult(
            passed=False,
            check_name="verify_commit_message_format",
            message="Commit message cannot be empty",
        )

    # Check for emoji prefix or conventional commit
    has_valid_prefix = any(message.startswith(prefix) for prefix in VALID_PREFIXES)
    conventional_pattern = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?:"
    has_conventional = bool(re.match(conventional_pattern, message))

    if not has_valid_prefix and not has_conventional:
        return ReviewResult(
            passed=False,
            check_name="verify_commit_message_format",
            message="Commit message must start with emoji prefix or conventional commit type (e.g., docs:)",
        )

    # Check for Task: reference
    if "Task:" not in message and "task:" not in message.lower():
        return ReviewResult(
            passed=False,
            check_name="verify_commit_message_format",
            message="Commit message must include 'Task:' reference",
        )

    # Check for Type: documentation
    if "Type: documentation" not in message and "type: documentation" not in message.lower():
        return ReviewResult(
            passed=False,
            check_name="verify_commit_message_format",
            message="Commit message must include 'Type: documentation'",
        )

    return ReviewResult(
        passed=True,
        check_name="verify_commit_message_format",
        message="Commit message format is valid",
    )


def verify_task_reference_valid(task_id: str, tracker: object) -> ReviewResult:
    """Verify that task reference exists and is in_progress status.

    Args:
        task_id: The task ID to verify.
        tracker: The issue tracker instance (IssueTracker protocol).

    Returns:
        ReviewResult indicating if task reference is valid.
    """
    try:
        # Try to get the task from the tracker
        task = tracker.get_task(task_id)  # type: ignore

        # Check if task exists and is in_progress
        if not task:
            return ReviewResult(
                passed=False,
                check_name="verify_task_reference_valid",
                message=f"Task {task_id} not found",
            )

        # Check if task is in_progress
        if task.status != "in_progress":
            return ReviewResult(
                passed=False,
                check_name="verify_task_reference_valid",
                message=f"Task {task_id} is in '{task.status}' status, not 'in_progress'",
            )

        return ReviewResult(
            passed=True,
            check_name="verify_task_reference_valid",
            message=f"Task {task_id} is valid and in_progress",
        )

    except KeyError:
        return ReviewResult(
            passed=False,
            check_name="verify_task_reference_valid",
            message=f"Task {task_id} not found in tracker",
        )
    except Exception as e:
        return ReviewResult(
            passed=False,
            check_name="verify_task_reference_valid",
            message=f"Error validating task reference: {str(e)}",
        )
