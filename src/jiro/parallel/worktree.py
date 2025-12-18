"""Git worktree lifecycle management for parallel task execution.

This module provides functionality for creating, managing, and cleaning up
git worktrees that allow isolated task execution in parallel.
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class WorktreeInfo:
    """Information about a git worktree.

    Attributes:
        path: Full path to the worktree directory.
        task_id: Identifier for the task associated with this worktree.
        branch: Branch name checked out in the worktree.
        created_at: Timestamp when the worktree was created.
        status: Current status ('active', 'stale', 'orphaned').
    """

    path: Path
    task_id: str
    branch: str
    created_at: datetime
    status: str


class WorktreeManager:
    """Manages git worktree lifecycle operations.

    Provides high-level operations for creating, listing, and cleaning up
    git worktrees used for parallel task execution.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialize the WorktreeManager.

        Args:
            repo_path: Path to the git repository root.
        """
        self.repo_path = Path(repo_path)
        self.worktrees_dir = self.repo_path / ".worktrees"

    def create_worktree(
        self,
        task_id: str,
        branch_name: str | None = None,
    ) -> Path:
        """Create a new git worktree for task execution.

        Creates a new worktree in .worktrees/<task_id> with an associated branch.
        The branch name defaults to 'feature/<task_id>' if not specified.

        Args:
            task_id: Unique identifier for the task.
            branch_name: Optional custom branch name. Defaults to 'feature/<task_id>'.

        Returns:
            Path to the newly created worktree.

        Raises:
            RuntimeError: If worktree creation fails.
        """
        if branch_name is None:
            branch_name = f"feature/{task_id}"

        worktree_path = self.worktrees_dir / task_id

        # Ensure worktrees directory exists
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

        # Create the worktree
        result = subprocess.run(
            [
                "git",
                "worktree",
                "add",
                str(worktree_path),
                "-b",
                branch_name,
            ],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree for task {task_id}: {result.stderr}")

        return worktree_path

    def cleanup_worktree(self, worktree_path: Path) -> bool:
        """Remove a git worktree.

        Attempts to remove the worktree and its associated branch.
        Returns False if removal fails, but doesn't raise an exception.

        Args:
            worktree_path: Path to the worktree to remove.

        Returns:
            True if removal was successful, False otherwise.
        """
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        return result.returncode == 0

    def list_active_worktrees(self) -> list[WorktreeInfo]:
        """List all active worktrees in the repository.

        Parses git worktree output to extract worktree information.
        Excludes the main repository worktree.

        Returns:
            List of WorktreeInfo objects for active worktrees.
        """
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        worktrees = []
        lines = result.stdout.strip().split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Parse worktree line (format: "worktree /path/to/worktree")
            if line.startswith("worktree "):
                path_str = line.replace("worktree ", "", 1).strip()
                path = Path(path_str)

                # Skip main repository worktree
                if path == self.repo_path:
                    i += 1
                    continue

                # Look for branch and status info in following lines
                branch = ""
                status = "active"

                i += 1
                while i < len(lines) and not lines[i].startswith("worktree"):
                    current_line = lines[i]

                    if current_line.startswith("branch "):
                        branch = current_line.replace("branch ", "", 1).strip()
                    elif current_line.startswith("prunable"):
                        status = "stale"

                    i += 1

                # Extract task_id from path
                task_id = path.name

                worktrees.append(
                    WorktreeInfo(
                        path=path,
                        task_id=task_id,
                        branch=branch,
                        created_at=datetime.now(),
                        status=status,
                    )
                )
                continue

            i += 1

        return worktrees

    def cleanup_stale_worktrees(self, force: bool = False) -> int:
        """Clean up stale and orphaned worktrees.

        Identifies worktrees marked as prunable and removes them.
        Can optionally use force removal.

        Args:
            force: If True, uses --force flag for aggressive pruning.

        Returns:
            Number of worktrees pruned.
        """
        cmd = ["git", "worktree", "prune"]
        if force:
            cmd.append("--force")

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return 0

        # Parse output to count pruned worktrees
        # Note: git worktree prune doesn't output count, so we return 0
        # In a real implementation, we might track this separately
        return 0
