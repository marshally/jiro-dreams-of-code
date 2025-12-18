"""Tests for conflict resolution and error handling in parallel execution."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.parallel.conflict_resolver import (
    ConflictResolver,
    ConflictStrategy,
    RecoveryAction,
    ResolutionResult,
)


class TestConflictStrategy:
    """Tests for ConflictStrategy enum."""

    @pytest.mark.unit
    def test_conflict_strategy_abort(self) -> None:
        """Should have ABORT strategy."""
        assert ConflictStrategy.ABORT.value == "abort"

    @pytest.mark.unit
    def test_conflict_strategy_manual(self) -> None:
        """Should have MANUAL strategy."""
        assert ConflictStrategy.MANUAL.value == "manual"

    @pytest.mark.unit
    def test_conflict_strategy_auto_resolve(self) -> None:
        """Should have AUTO_RESOLVE strategy."""
        assert ConflictStrategy.AUTO_RESOLVE.value == "auto_resolve"


class TestRecoveryAction:
    """Tests for RecoveryAction enum."""

    @pytest.mark.unit
    def test_recovery_action_retry(self) -> None:
        """Should have RETRY action."""
        assert RecoveryAction.RETRY.value == "retry"

    @pytest.mark.unit
    def test_recovery_action_skip(self) -> None:
        """Should have SKIP action."""
        assert RecoveryAction.SKIP.value == "skip"

    @pytest.mark.unit
    def test_recovery_action_rollback(self) -> None:
        """Should have ROLLBACK action."""
        assert RecoveryAction.ROLLBACK.value == "rollback"

    @pytest.mark.unit
    def test_recovery_action_escalate(self) -> None:
        """Should have ESCALATE action."""
        assert RecoveryAction.ESCALATE.value == "escalate"


class TestResolutionResult:
    """Tests for ResolutionResult dataclass."""

    @pytest.mark.unit
    def test_resolution_result_successful(self) -> None:
        """Should create ResolutionResult with successful resolution."""
        result = ResolutionResult(
            success=True,
            strategy_used=ConflictStrategy.AUTO_RESOLVE,
            resolved_files=[Path("file1.py"), Path("file2.py")],
        )

        assert result.success is True
        assert result.strategy_used == ConflictStrategy.AUTO_RESOLVE
        assert len(result.resolved_files) == 2

    @pytest.mark.unit
    def test_resolution_result_failed(self) -> None:
        """Should create ResolutionResult with failed resolution."""
        result = ResolutionResult(
            success=False,
            strategy_used=ConflictStrategy.MANUAL,
            resolved_files=[],
        )

        assert result.success is False
        assert result.strategy_used == ConflictStrategy.MANUAL
        assert len(result.resolved_files) == 0

    @pytest.mark.unit
    def test_resolution_result_partial_resolution(self) -> None:
        """Should create ResolutionResult with partial file resolution."""
        result = ResolutionResult(
            success=False,
            strategy_used=ConflictStrategy.AUTO_RESOLVE,
            resolved_files=[Path("file1.py")],
        )

        assert result.success is False
        assert len(result.resolved_files) == 1


class TestConflictResolver:
    """Tests for ConflictResolver class."""

    @pytest.fixture
    def repo_path(self, tmp_path: Path) -> Path:
        """Provide a temporary repository path."""
        return tmp_path / "repo"

    @pytest.fixture
    def resolver(self, repo_path: Path) -> ConflictResolver:
        """Provide a ConflictResolver instance with default strategy."""
        return ConflictResolver(repo_path)

    @pytest.fixture
    def resolver_manual(self, repo_path: Path) -> ConflictResolver:
        """Provide a ConflictResolver instance with manual strategy."""
        return ConflictResolver(repo_path, strategy=ConflictStrategy.MANUAL)

    @pytest.mark.unit
    def test_resolver_initialization_default_strategy(self, repo_path: Path) -> None:
        """Should initialize ConflictResolver with default MANUAL strategy."""
        resolver = ConflictResolver(repo_path)

        assert resolver.repo_path == repo_path
        assert resolver.strategy == ConflictStrategy.MANUAL

    @pytest.mark.unit
    def test_resolver_initialization_custom_strategy(self, repo_path: Path) -> None:
        """Should initialize ConflictResolver with custom strategy."""
        resolver = ConflictResolver(repo_path, strategy=ConflictStrategy.AUTO_RESOLVE)

        assert resolver.repo_path == repo_path
        assert resolver.strategy == ConflictStrategy.AUTO_RESOLVE

    @pytest.mark.unit
    def test_resolver_initialization_abort_strategy(self, repo_path: Path) -> None:
        """Should initialize ConflictResolver with ABORT strategy."""
        resolver = ConflictResolver(repo_path, strategy=ConflictStrategy.ABORT)

        assert resolver.strategy == ConflictStrategy.ABORT

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_detect_conflicts_found(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should detect merge conflicts in worktree."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        # Mock git status output with conflict markers
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="UU file1.py\nAA file2.py\n",
            stderr="",
        )

        conflicts = resolver.detect_conflicts(worktree_path)

        assert len(conflicts) > 0

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_detect_conflicts_none_found(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should return empty list when no conflicts found."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        conflicts = resolver.detect_conflicts(worktree_path)

        assert conflicts == []

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_detect_conflicts_command_fails(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should handle git status command failure."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="fatal error")

        conflicts = resolver.detect_conflicts(worktree_path)

        assert conflicts == []

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_resolve_merge_conflict_abort_strategy(
        self, mock_run: MagicMock, repo_path: Path, tmp_path: Path
    ) -> None:
        """Should abort merge with ABORT strategy."""
        resolver = ConflictResolver(repo_path, strategy=ConflictStrategy.ABORT)
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        conflict_files = [Path("file1.py"), Path("file2.py")]

        # Mock merge abort command
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = resolver.resolve_merge_conflict(worktree_path, conflict_files)

        assert result.success is False
        assert result.strategy_used == ConflictStrategy.ABORT

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_resolve_merge_conflict_manual_strategy(
        self, mock_run: MagicMock, resolver_manual: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should indicate manual resolution needed with MANUAL strategy."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        conflict_files = [Path("file1.py")]

        result = resolver_manual.resolve_merge_conflict(worktree_path, conflict_files)

        assert result.success is False
        assert result.strategy_used == ConflictStrategy.MANUAL

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_resolve_merge_conflict_auto_resolve_strategy(
        self, mock_run: MagicMock, repo_path: Path, tmp_path: Path
    ) -> None:
        """Should attempt auto-resolution with AUTO_RESOLVE strategy."""
        resolver = ConflictResolver(repo_path, strategy=ConflictStrategy.AUTO_RESOLVE)
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        conflict_files = [Path("file1.py")]

        # Mock successful git add command
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = resolver.resolve_merge_conflict(worktree_path, conflict_files)

        assert result.strategy_used == ConflictStrategy.AUTO_RESOLVE

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_resolve_merge_conflict_empty_conflict_files(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should handle empty conflict files list."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        result = resolver.resolve_merge_conflict(worktree_path, [])

        assert result.success is False

    @pytest.mark.unit
    def test_handle_task_failure_no_retries_left(self, resolver: ConflictResolver) -> None:
        """Should escalate when no retries left."""
        error = RuntimeError("Task execution failed")

        action = resolver.handle_task_failure("task-1", error, retry_count=3)

        assert action == RecoveryAction.ESCALATE

    @pytest.mark.unit
    def test_handle_task_failure_transient_error(self, resolver: ConflictResolver) -> None:
        """Should retry on transient error with retries remaining."""
        error = TimeoutError("Connection timeout")

        action = resolver.handle_task_failure("task-1", error, retry_count=0)

        assert action == RecoveryAction.RETRY

    @pytest.mark.unit
    def test_handle_task_failure_permanent_error(self, resolver: ConflictResolver) -> None:
        """Should skip on permanent error."""
        error = ValueError("Invalid configuration")

        action = resolver.handle_task_failure("task-1", error, retry_count=0)

        assert action == RecoveryAction.SKIP

    @pytest.mark.unit
    def test_handle_task_failure_dependency_error(self, resolver: ConflictResolver) -> None:
        """Should rollback on dependency failure."""
        error = RuntimeError("Dependency task failed")

        action = resolver.handle_task_failure("task-2", error, retry_count=1)

        # Should be escalate because retry_count >= max_retries
        assert action in (RecoveryAction.ROLLBACK, RecoveryAction.ESCALATE)

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_abort_merge_success(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should abort merge and return True on success."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = resolver.abort_merge(worktree_path)

        assert result is True

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_abort_merge_failure(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should return False when abort merge fails."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="fatal error")

        result = resolver.abort_merge(worktree_path)

        assert result is False

    @patch("jiro.parallel.conflict_resolver.subprocess.run")
    def test_abort_merge_timeout(
        self, mock_run: MagicMock, resolver: ConflictResolver, tmp_path: Path
    ) -> None:
        """Should handle timeout during abort merge."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_run.side_effect = TimeoutError()

        result = resolver.abort_merge(worktree_path)

        assert result is False
