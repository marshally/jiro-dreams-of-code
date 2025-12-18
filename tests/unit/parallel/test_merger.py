"""Tests for worktree merge strategy and result aggregation."""

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.parallel.merger import (
    AggregatedResult,
    MergeResult,
    TaskResult,
    WorktreeMerger,
)


class TestMergeResult:
    """Tests for MergeResult dataclass."""

    @pytest.mark.unit
    def test_merge_result_creation_success(self) -> None:
        """Should create MergeResult with success flag and commit SHA."""
        result = MergeResult(
            success=True,
            commit_sha="abc123def456",
            error_message=None,
        )

        assert result.success is True
        assert result.commit_sha == "abc123def456"
        assert result.error_message is None

    @pytest.mark.unit
    def test_merge_result_creation_failure(self) -> None:
        """Should create MergeResult with failure and error message."""
        result = MergeResult(
            success=False,
            commit_sha=None,
            error_message="Merge conflict detected",
        )

        assert result.success is False
        assert result.commit_sha is None
        assert result.error_message == "Merge conflict detected"

    @pytest.mark.unit
    def test_merge_result_all_fields_optional_on_failure(self) -> None:
        """Should allow flexible field combinations on failure."""
        result = MergeResult(
            success=False,
            commit_sha=None,
            error_message="Failed to merge",
        )

        assert result.success is False
        assert result.error_message is not None


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    @pytest.mark.unit
    def test_task_result_creation(self) -> None:
        """Should create TaskResult with all required fields."""
        result = TaskResult(
            task_id="task-123",
            success=True,
            duration=timedelta(seconds=42.5),
            files_changed=5,
        )

        assert result.task_id == "task-123"
        assert result.success is True
        assert result.duration == timedelta(seconds=42.5)
        assert result.files_changed == 5

    @pytest.mark.unit
    def test_task_result_failure(self) -> None:
        """Should create TaskResult for failed tasks."""
        result = TaskResult(
            task_id="task-456",
            success=False,
            duration=timedelta(seconds=10.0),
            files_changed=0,
        )

        assert result.task_id == "task-456"
        assert result.success is False
        assert result.duration == timedelta(seconds=10.0)
        assert result.files_changed == 0

    @pytest.mark.unit
    def test_task_result_zero_files_changed(self) -> None:
        """Should allow zero files changed."""
        result = TaskResult(
            task_id="task-789",
            success=True,
            duration=timedelta(seconds=0),
            files_changed=0,
        )

        assert result.files_changed == 0


class TestAggregatedResult:
    """Tests for AggregatedResult dataclass."""

    @pytest.mark.unit
    def test_aggregated_result_creation(self) -> None:
        """Should create AggregatedResult with all task metrics."""
        result = AggregatedResult(
            total_tasks=10,
            successful=8,
            failed=2,
            total_duration=timedelta(seconds=500),
        )

        assert result.total_tasks == 10
        assert result.successful == 8
        assert result.failed == 2
        assert result.total_duration == timedelta(seconds=500)

    @pytest.mark.unit
    def test_aggregated_result_all_successful(self) -> None:
        """Should handle case where all tasks succeed."""
        result = AggregatedResult(
            total_tasks=5,
            successful=5,
            failed=0,
            total_duration=timedelta(seconds=100),
        )

        assert result.total_tasks == 5
        assert result.successful == 5
        assert result.failed == 0

    @pytest.mark.unit
    def test_aggregated_result_all_failed(self) -> None:
        """Should handle case where all tasks fail."""
        result = AggregatedResult(
            total_tasks=5,
            successful=0,
            failed=5,
            total_duration=timedelta(seconds=50),
        )

        assert result.total_tasks == 5
        assert result.successful == 0
        assert result.failed == 5

    @pytest.mark.unit
    def test_aggregated_result_empty(self) -> None:
        """Should handle zero tasks."""
        result = AggregatedResult(
            total_tasks=0,
            successful=0,
            failed=0,
            total_duration=timedelta(seconds=0),
        )

        assert result.total_tasks == 0
        assert result.successful == 0
        assert result.failed == 0


class TestWorktreeMerger:
    """Tests for WorktreeMerger class."""

    @pytest.fixture
    def repo_path(self, tmp_path: Path) -> Path:
        """Provide a temporary repository path."""
        return tmp_path / "repo"

    @pytest.fixture
    def merger(self, repo_path: Path) -> WorktreeMerger:
        """Provide a WorktreeMerger instance."""
        return WorktreeMerger(repo_path)

    @pytest.mark.unit
    def test_merger_initialization(self, repo_path: Path) -> None:
        """Should initialize WorktreeMerger with repo path."""
        merger = WorktreeMerger(repo_path)

        assert merger.repo_path == repo_path

    @patch("jiro.parallel.merger.subprocess.run")
    def test_merge_worktree_success(
        self, mock_run: MagicMock, merger: WorktreeMerger, tmp_path: Path
    ) -> None:
        """Should merge worktree and return success with commit SHA."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        # Mock successful git merge and log commands
        def run_side_effect(*args, **kwargs):
            if "merge" in args[0]:
                return MagicMock(returncode=0, stdout="", stderr="")
            elif "rev-parse" in args[0]:
                return MagicMock(returncode=0, stdout="abc123def456\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        result = merger.merge_worktree(worktree_path, target_branch="main")

        assert result.success is True
        assert result.commit_sha == "abc123def456"
        assert result.error_message is None

    @patch("jiro.parallel.merger.subprocess.run")
    def test_merge_worktree_with_default_branch(
        self, mock_run: MagicMock, merger: WorktreeMerger, tmp_path: Path
    ) -> None:
        """Should use main as default target branch."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n", stderr="")

        result = merger.merge_worktree(worktree_path)

        assert result.success is True

    @patch("jiro.parallel.merger.subprocess.run")
    def test_merge_worktree_conflict(
        self, mock_run: MagicMock, merger: WorktreeMerger, tmp_path: Path
    ) -> None:
        """Should handle merge conflicts gracefully."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        # Mock merge conflict
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Merge conflict in file.py"
        )

        result = merger.merge_worktree(worktree_path, target_branch="main")

        assert result.success is False
        assert result.commit_sha is None
        assert result.error_message is not None

    @patch("jiro.parallel.merger.subprocess.run")
    def test_merge_worktree_invalid_branch(
        self, mock_run: MagicMock, merger: WorktreeMerger, tmp_path: Path
    ) -> None:
        """Should handle invalid target branch."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        # Mock branch not found
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: reference not a tree"
        )

        result = merger.merge_worktree(worktree_path, target_branch="nonexistent")

        assert result.success is False
        assert result.error_message is not None

    @pytest.mark.unit
    def test_aggregate_results_single_task(self, merger: WorktreeMerger) -> None:
        """Should aggregate results from single task."""
        results = [
            TaskResult(
                task_id="task-1",
                success=True,
                duration=timedelta(seconds=30),
                files_changed=5,
            ),
        ]

        aggregated = merger.aggregate_results(results)

        assert aggregated.total_tasks == 1
        assert aggregated.successful == 1
        assert aggregated.failed == 0
        assert aggregated.total_duration == timedelta(seconds=30)

    @pytest.mark.unit
    def test_aggregate_results_multiple_tasks(self, merger: WorktreeMerger) -> None:
        """Should aggregate results from multiple tasks."""
        results = [
            TaskResult(
                task_id="task-1",
                success=True,
                duration=timedelta(seconds=30),
                files_changed=5,
            ),
            TaskResult(
                task_id="task-2",
                success=True,
                duration=timedelta(seconds=40),
                files_changed=3,
            ),
            TaskResult(
                task_id="task-3",
                success=False,
                duration=timedelta(seconds=10),
                files_changed=0,
            ),
        ]

        aggregated = merger.aggregate_results(results)

        assert aggregated.total_tasks == 3
        assert aggregated.successful == 2
        assert aggregated.failed == 1
        assert aggregated.total_duration == timedelta(seconds=80)

    @pytest.mark.unit
    def test_aggregate_results_all_failed(self, merger: WorktreeMerger) -> None:
        """Should aggregate when all tasks fail."""
        results = [
            TaskResult(
                task_id="task-1",
                success=False,
                duration=timedelta(seconds=5),
                files_changed=0,
            ),
            TaskResult(
                task_id="task-2",
                success=False,
                duration=timedelta(seconds=10),
                files_changed=0,
            ),
        ]

        aggregated = merger.aggregate_results(results)

        assert aggregated.total_tasks == 2
        assert aggregated.successful == 0
        assert aggregated.failed == 2

    @pytest.mark.unit
    def test_aggregate_results_empty_list(self, merger: WorktreeMerger) -> None:
        """Should handle aggregation of empty result list."""
        results = []

        aggregated = merger.aggregate_results(results)

        assert aggregated.total_tasks == 0
        assert aggregated.successful == 0
        assert aggregated.failed == 0
        assert aggregated.total_duration == timedelta(seconds=0)
