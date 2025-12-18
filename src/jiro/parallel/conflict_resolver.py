"""Conflict resolution and error handling for parallel task execution.

This module provides functionality for detecting and resolving merge conflicts,
handling task failures, and implementing recovery strategies during parallel
execution using git worktrees.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ConflictStrategy(Enum):
    """Strategy for handling merge conflicts.

    Attributes:
        ABORT: Stop execution and abort the merge.
        MANUAL: Mark conflict for manual resolution by user.
        AUTO_RESOLVE: Attempt automatic resolution of conflicts.
    """

    ABORT = "abort"
    MANUAL = "manual"
    AUTO_RESOLVE = "auto_resolve"


class RecoveryAction(Enum):
    """Action to take when a task fails.

    Attributes:
        RETRY: Retry the failed task.
        SKIP: Skip the task and continue.
        ROLLBACK: Rollback changes made by the task.
        ESCALATE: Escalate failure to user/supervisor.
    """

    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"


@dataclass
class ResolutionResult:
    """Result of attempting to resolve merge conflicts.

    Attributes:
        success: Whether the resolution was successful.
        strategy_used: The conflict strategy that was used.
        resolved_files: List of files that were resolved.
    """

    success: bool
    strategy_used: ConflictStrategy
    resolved_files: list[Path]


class ConflictResolver:
    """Manages conflict detection and resolution during parallel task execution.

    Provides functionality for detecting merge conflicts in worktrees,
    applying resolution strategies, and handling task failures with
    appropriate recovery actions.
    """

    def __init__(
        self, repo_path: Path, strategy: ConflictStrategy = ConflictStrategy.MANUAL
    ) -> None:
        """Initialize the ConflictResolver.

        Args:
            repo_path: Path to the git repository root.
            strategy: Conflict resolution strategy to use. Defaults to MANUAL.
        """
        self.repo_path = Path(repo_path)
        self.strategy = strategy

    def detect_conflicts(self, worktree_path: Path) -> list[Path]:
        """Detect merge conflicts in a worktree.

        Checks for conflicted files marked by git (UU, AA, DD, etc. status codes).

        Args:
            worktree_path: Path to the worktree to check for conflicts.

        Returns:
            List of paths to files with conflicts. Empty list if no conflicts found.
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return []

            conflicts = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                # Check for conflict markers (UU, AA, DD, AU, UD, etc.)
                status = line[:2]
                if status[0] in ("U", "D", "A") and status[1] in ("U", "D", "A"):
                    filepath = line[3:].strip()
                    conflicts.append(Path(filepath))

            return conflicts

        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []

    def resolve_merge_conflict(
        self, worktree_path: Path, conflict_files: list[Path]
    ) -> ResolutionResult:
        """Attempt to resolve merge conflicts using configured strategy.

        Args:
            worktree_path: Path to the worktree with conflicts.
            conflict_files: List of files with conflicts.

        Returns:
            ResolutionResult with success status and files resolved.
        """
        if not conflict_files:
            return ResolutionResult(
                success=False,
                strategy_used=self.strategy,
                resolved_files=[],
            )

        if self.strategy == ConflictStrategy.ABORT:
            self.abort_merge(worktree_path)
            return ResolutionResult(
                success=False,
                strategy_used=ConflictStrategy.ABORT,
                resolved_files=[],
            )

        if self.strategy == ConflictStrategy.MANUAL:
            return ResolutionResult(
                success=False,
                strategy_used=ConflictStrategy.MANUAL,
                resolved_files=[],
            )

        if self.strategy == ConflictStrategy.AUTO_RESOLVE:
            resolved = []
            for filepath in conflict_files:
                try:
                    result = subprocess.run(
                        ["git", "add", str(filepath)],
                        cwd=worktree_path,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        resolved.append(filepath)
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass

            success = len(resolved) == len(conflict_files)
            return ResolutionResult(
                success=success,
                strategy_used=ConflictStrategy.AUTO_RESOLVE,
                resolved_files=resolved,
            )

        return ResolutionResult(
            success=False,
            strategy_used=self.strategy,
            resolved_files=[],
        )

    def handle_task_failure(
        self, task_id: str, error: Exception, retry_count: int = 0
    ) -> RecoveryAction:
        """Determine recovery action for a failed task.

        Analyzes the error type and retry count to determine the appropriate
        recovery action.

        Args:
            task_id: Identifier for the failed task.
            error: The exception that caused the failure.
            retry_count: Number of retries already attempted.

        Returns:
            RecoveryAction indicating what action to take.
        """
        max_retries = 3

        # Check if we've exhausted retries
        if retry_count >= max_retries:
            return RecoveryAction.ESCALATE

        # Transient errors should be retried
        if isinstance(error, TimeoutError | ConnectionError):
            return RecoveryAction.RETRY

        # Permanent errors should be skipped
        if isinstance(error, ValueError | TypeError | KeyError):
            return RecoveryAction.SKIP

        # Runtime errors depend on context
        if isinstance(error, RuntimeError):
            if "Dependency" in str(error) or "dependency" in str(error).lower():
                return RecoveryAction.ROLLBACK
            return RecoveryAction.ESCALATE

        # Default to escalation for unknown errors
        return RecoveryAction.ESCALATE

    def abort_merge(self, worktree_path: Path) -> bool:
        """Abort a merge in progress in the worktree.

        Args:
            worktree_path: Path to the worktree with in-progress merge.

        Returns:
            True if merge was aborted successfully, False otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "merge", "--abort"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
