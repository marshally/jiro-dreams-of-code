"""Tests for git worktree lifecycle management."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.parallel.worktree import WorktreeInfo, WorktreeManager


class TestWorktreeInfo:
    """Tests for WorktreeInfo dataclass."""

    @pytest.mark.unit
    def test_worktree_info_creation(self, tmp_path: Path) -> None:
        """Should create WorktreeInfo with all fields."""
        created_at = datetime(2025, 1, 1, 12, 0, 0)
        info = WorktreeInfo(
            path=tmp_path / "worktree",
            task_id="task-123",
            branch="feature/task-123",
            created_at=created_at,
            status="active",
        )

        assert info.path == tmp_path / "worktree"
        assert info.task_id == "task-123"
        assert info.branch == "feature/task-123"
        assert info.created_at == created_at
        assert info.status == "active"

    @pytest.mark.unit
    def test_worktree_info_status_values(self, tmp_path: Path) -> None:
        """Should support different status values."""
        for status in ["active", "stale", "orphaned"]:
            info = WorktreeInfo(
                path=tmp_path / "worktree",
                task_id="task-123",
                branch="feature/task-123",
                created_at=datetime.now(),
                status=status,
            )
            assert info.status == status


class TestWorktreeManager:
    """Tests for WorktreeManager class."""

    @pytest.fixture
    def repo_path(self, tmp_path: Path) -> Path:
        """Provide a temporary repository path."""
        return tmp_path / "repo"

    @pytest.fixture
    def manager(self, repo_path: Path) -> WorktreeManager:
        """Provide a WorktreeManager instance."""
        return WorktreeManager(repo_path)

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_create_worktree_success(self, mock_run: MagicMock, manager: WorktreeManager) -> None:
        """Should create worktree and return path."""
        task_id = "task-123"
        expected_path = manager.worktrees_dir / task_id

        # Mock successful git worktree add and git branch
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = manager.create_worktree(task_id)

        assert result == expected_path
        # Verify git worktree add was called
        assert mock_run.call_count >= 1
        first_call = mock_run.call_args_list[0]
        assert "git" in first_call[0][0]
        assert "worktree" in first_call[0][0]
        assert "add" in first_call[0][0]

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_create_worktree_failure(self, mock_run: MagicMock, manager: WorktreeManager) -> None:
        """Should raise exception on git worktree add failure."""
        task_id = "task-123"
        mock_run.return_value = MagicMock(returncode=1, stderr="Failed to create worktree")

        with pytest.raises(RuntimeError, match="Failed to create worktree"):
            manager.create_worktree(task_id)

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_cleanup_worktree_success(
        self, mock_run: MagicMock, manager: WorktreeManager, tmp_path: Path
    ) -> None:
        """Should remove worktree successfully."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = manager.cleanup_worktree(worktree_path)

        assert result is True
        # Verify git worktree remove was called
        assert mock_run.call_count >= 1
        calls = mock_run.call_args_list
        assert any("remove" in str(c) for c in calls)

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_cleanup_worktree_failure(
        self, mock_run: MagicMock, manager: WorktreeManager, tmp_path: Path
    ) -> None:
        """Should return False on cleanup failure."""
        worktree_path = tmp_path / "worktree"
        mock_run.return_value = MagicMock(returncode=1, stderr="Failed to remove worktree")

        result = manager.cleanup_worktree(worktree_path)

        assert result is False

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_list_active_worktrees_empty(
        self, mock_run: MagicMock, manager: WorktreeManager
    ) -> None:
        """Should return empty list when no worktrees exist."""
        # Mock git worktree list output
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = manager.list_active_worktrees()

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_list_active_worktrees_with_entries(
        self, mock_run: MagicMock, manager: WorktreeManager, tmp_path: Path
    ) -> None:
        """Should parse and return active worktrees."""
        worktree_path1 = manager.worktrees_dir / "task-1"
        worktree_path2 = manager.worktrees_dir / "task-2"

        # Mock git worktree list output (porcelain format)
        list_output = f"""worktree {worktree_path1}
branch refs/heads/feature/task-1
detach

worktree {worktree_path2}
branch refs/heads/feature/task-2
detach
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=list_output, stderr="")

        result = manager.list_active_worktrees()

        assert len(result) >= 2
        # Check that WorktreeInfo objects have expected structure
        for info in result:
            assert isinstance(info, WorktreeInfo)
            assert info.path is not None
            assert info.task_id is not None
            assert info.branch is not None

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_list_active_worktrees_filters_main_branch(
        self, mock_run: MagicMock, manager: WorktreeManager
    ) -> None:
        """Should filter out main worktree from results."""
        # Mock git worktree list with main branch included
        repo_path = manager.repo_path
        list_output = f"""worktree {repo_path}
branch refs/heads/main
detach

worktree {manager.worktrees_dir}/task-1
branch refs/heads/feature/task-1
detach
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=list_output, stderr="")

        result = manager.list_active_worktrees()

        # Should only include task-1, not main
        assert all(str(info.path) != str(repo_path) for info in result)

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_cleanup_stale_worktrees(self, mock_run: MagicMock, manager: WorktreeManager) -> None:
        """Should identify and remove stale worktrees."""
        # Mock git worktree list with stale entry
        list_output = """worktree /tmp/repo/worktrees/task-1
branch refs/heads/feature/task-1
prunable

worktree /tmp/repo/worktrees/task-2
branch refs/heads/feature/task-2
detach
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=list_output, stderr="")

        result = manager.cleanup_stale_worktrees()

        # Should find at least 1 stale worktree
        assert result >= 0
        # Verify git worktree prune was called
        assert mock_run.call_count >= 1

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_cleanup_stale_worktrees_with_force(
        self, mock_run: MagicMock, manager: WorktreeManager
    ) -> None:
        """Should use --force flag when removing stale worktrees."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        manager.cleanup_stale_worktrees(force=True)

        # Verify prune was called with --force
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("force" in c.lower() for c in calls)

    @pytest.mark.unit
    def test_manager_initialization(self, repo_path: Path) -> None:
        """Should initialize with repo path."""
        manager = WorktreeManager(repo_path)

        assert manager.repo_path == repo_path
        assert manager.worktrees_dir == repo_path / ".worktrees"

    @patch("jiro.parallel.worktree.subprocess.run")
    def test_create_worktree_with_custom_branch(
        self, mock_run: MagicMock, manager: WorktreeManager
    ) -> None:
        """Should create worktree with custom branch name."""
        task_id = "task-456"
        branch_name = "custom/branch-456"

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = manager.create_worktree(task_id, branch_name=branch_name)

        assert result == manager.worktrees_dir / task_id
        # Verify branch name was used
        calls = [str(c) for c in mock_run.call_args_list]
        assert any(branch_name in c for c in calls)
