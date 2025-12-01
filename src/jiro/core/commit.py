"""Git commit creation and management."""

import subprocess
import uuid
from datetime import datetime

from jiro.assets.loader import load_template
from jiro.db.models import Commit
from jiro.db.repository import CommitRepository


class ValidationError(Exception):
    """Raised when commit validation fails."""

    pass


# File extensions allowed for docs commits
DOCS_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}


def _get_staged_files() -> list[str]:
    """Get list of staged files from git.

    Returns:
        List of file paths that are staged for commit.

    Raises:
        RuntimeError: If git command fails.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get staged files: {result.stderr}")
    return [f for f in result.stdout.strip().split("\n") if f]


def _validate_docs_files(files: list[str]) -> None:
    """Validate that all files are documentation files.

    Args:
        files: List of file paths to validate.

    Raises:
        ValidationError: If any non-documentation files are found.
    """
    invalid_files = []
    for file_path in files:
        ext = _get_extension(file_path)
        if ext not in DOCS_EXTENSIONS:
            invalid_files.append(file_path)

    if invalid_files:
        raise ValidationError(
            f"Docs commit contains non-documentation files: {', '.join(invalid_files)}"
        )


def _get_extension(file_path: str) -> str:
    """Get file extension from path.

    Args:
        file_path: Path to the file.

    Returns:
        File extension including the dot (e.g., ".md").
    """
    if "." not in file_path:
        return ""
    return "." + file_path.rsplit(".", 1)[-1].lower()


def _get_current_commit_sha() -> str:
    """Get the current HEAD commit SHA.

    Returns:
        The SHA of the current commit (after git commit).

    Raises:
        RuntimeError: If git command fails.
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get commit SHA: {result.stderr}")
    return result.stdout.strip()


def create_docs_commit(
    task_id: str,
    task_type: str,
    reason: str,
    verification_command: str,
    verification_results: str,
    time_taken_seconds: int,
    context_tokens_before: int,
    context_tokens_after: int,
    repository: CommitRepository,
    session_id: str | None = None,
) -> Commit:
    """Create a documentation commit.

    Validates that only documentation files are staged, renders the commit
    message from a template, creates the git commit, and records it in the
    database.

    Args:
        task_id: ID of the task this commit is for.
        task_type: Type of task (e.g., "docs", "feature").
        reason: Human-readable reason for the documentation changes.
        verification_command: Command used to verify the documentation.
        verification_results: Results of the verification command.
        time_taken_seconds: Time taken to complete the task.
        context_tokens_before: Context tokens before the task.
        context_tokens_after: Context tokens after the task.
        repository: CommitRepository instance for recording the commit.
        session_id: Optional session ID to associate with this commit.

    Returns:
        The recorded Commit object.

    Raises:
        ValidationError: If staged files include non-documentation files.
        RuntimeError: If git operations fail.
    """
    # Get staged files
    staged_files = _get_staged_files()

    # Validate files are docs-only
    _validate_docs_files(staged_files)

    # Load and render template
    template = load_template("commit/docs.txt.j2")
    commit_message = template.render(
        task_id=task_id,
        task_type=task_type,
        reason=reason,
        verification_command=verification_command,
        verification_results=verification_results,
        time_taken_seconds=time_taken_seconds,
        context_tokens_before=context_tokens_before,
        context_tokens_after=context_tokens_after,
    )

    # Create git commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create git commit: {result.stderr}")

    # Get the commit SHA
    sha = _get_current_commit_sha()

    # Create Commit object
    commit = Commit(
        id=str(uuid.uuid4()),
        task_id=task_id,
        sha=sha,
        commit_type="docs",
        message=commit_message,
        created_at=datetime.now(),
        session_id=session_id,
        verification_command=verification_command,
        verification_results=verification_results,
        time_taken_seconds=time_taken_seconds,
        context_tokens_before=context_tokens_before,
        context_tokens_after=context_tokens_after,
    )

    # Record in database
    repository.create(commit)

    return commit
