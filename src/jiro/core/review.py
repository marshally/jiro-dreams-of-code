"""Deterministic commit review checks.

These checks run before LLM review to catch obvious violations quickly.
"""

import re
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
