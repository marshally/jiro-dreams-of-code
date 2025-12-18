"""Merge strategy for integrating completed worktree changes back to main.

This module provides functionality for merging worktree changes into target branches
and aggregating execution results across parallel tasks.
"""

import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path


@dataclass
class MergeResult:
    """Result of merging a worktree to a target branch.

    Attributes:
        success: Whether the merge completed successfully.
        commit_sha: SHA of the resulting commit if successful, None otherwise.
        error_message: Description of error if merge failed, None otherwise.
    """

    success: bool
    commit_sha: str | None
    error_message: str | None


@dataclass
class TaskResult:
    """Result of executing a single task.

    Attributes:
        task_id: Identifier for the task.
        success: Whether the task completed successfully.
        duration: Time taken to complete the task.
        files_changed: Number of files modified by the task.
    """

    task_id: str
    success: bool
    duration: timedelta
    files_changed: int


@dataclass
class AggregatedResult:
    """Aggregated results across multiple tasks.

    Attributes:
        total_tasks: Total number of tasks that were executed.
        successful: Number of tasks that completed successfully.
        failed: Number of tasks that failed.
        total_duration: Combined duration of all tasks.
    """

    total_tasks: int
    successful: int
    failed: int
    total_duration: timedelta


class WorktreeMerger:
    """Manages merging of completed worktrees and result aggregation.

    Provides high-level operations for merging worktree changes back to target
    branches and aggregating execution results across parallel tasks.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialize the WorktreeMerger.

        Args:
            repo_path: Path to the git repository root.
        """
        self.repo_path = Path(repo_path)

    def merge_worktree(self, worktree_path: Path, target_branch: str = "main") -> MergeResult:
        """Merge a worktree into the target branch.

        Safely integrates changes from a worktree into the specified target branch.
        Handles merge conflicts and returns appropriate status.

        Args:
            worktree_path: Path to the worktree to merge.
            target_branch: Name of the branch to merge into. Defaults to "main".

        Returns:
            MergeResult containing success status, commit SHA, and any error message.
        """
        try:
            # Get the branch name from the worktree
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if branch_result.returncode != 0:
                return MergeResult(
                    success=False,
                    commit_sha=None,
                    error_message=f"Failed to determine worktree branch: {branch_result.stderr}",
                )

            worktree_branch = branch_result.stdout.strip()

            # Perform the merge
            merge_result = subprocess.run(
                [
                    "git",
                    "merge",
                    worktree_branch,
                    "-m",
                    f"Merge {worktree_branch} into {target_branch}",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if merge_result.returncode != 0:
                return MergeResult(
                    success=False,
                    commit_sha=None,
                    error_message=f"Merge failed: {merge_result.stderr}",
                )

            # Get the commit SHA of the merge
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if commit_result.returncode != 0:
                return MergeResult(
                    success=False,
                    commit_sha=None,
                    error_message="Failed to get commit SHA after merge",
                )

            commit_sha = commit_result.stdout.strip()

            return MergeResult(
                success=True,
                commit_sha=commit_sha,
                error_message=None,
            )

        except subprocess.TimeoutExpired:
            return MergeResult(
                success=False,
                commit_sha=None,
                error_message="Merge operation timed out",
            )
        except Exception as e:
            return MergeResult(
                success=False,
                commit_sha=None,
                error_message=f"Unexpected error during merge: {str(e)}",
            )

    def aggregate_results(self, results: list[TaskResult]) -> AggregatedResult:
        """Aggregate execution results across multiple tasks.

        Combines individual task results into summary statistics across all tasks.

        Args:
            results: List of TaskResult objects to aggregate.

        Returns:
            AggregatedResult containing summary statistics.
        """
        total_tasks = len(results)
        successful = sum(1 for result in results if result.success)
        failed = sum(1 for result in results if not result.success)
        total_duration = sum((result.duration for result in results), timedelta(seconds=0))

        return AggregatedResult(
            total_tasks=total_tasks,
            successful=successful,
            failed=failed,
            total_duration=total_duration,
        )
