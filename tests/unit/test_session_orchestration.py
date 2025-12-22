"""Tests for SessionOrchestrator - session lifecycle management."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlite_utils import Database

from jiro.config.schema import Config
from jiro.core.session import PostflightResult, PreflightResult
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import SessionRepository, TaskExecutionRepository


@pytest.fixture
def db_with_schema(tmp_path: Path) -> Database:
    """Provide a database with schema initialized."""
    db = get_database(tmp_path / "test.db")
    ensure_schema(db)
    return db


@pytest.fixture
def session_repo(db_with_schema: Database) -> SessionRepository:
    """Provide a SessionRepository instance."""
    return SessionRepository(db_with_schema)


@pytest.fixture
def task_repo(db_with_schema: Database) -> TaskExecutionRepository:
    """Provide a TaskExecutionRepository instance."""
    return TaskExecutionRepository(db_with_schema)


@pytest.fixture
def config() -> Config:
    """Provide a Config instance."""
    return Config()


class TestSessionOrchestratorInit:
    """Tests for SessionOrchestrator initialization."""

    @pytest.mark.unit
    def test_orchestrator_initializes_with_dependencies(
        self,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should initialize with config and repositories."""
        from jiro.core.session import SessionOrchestrator

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )
        assert orchestrator.config == config
        assert orchestrator.session_repo == session_repo
        assert orchestrator.task_repo == task_repo


class TestSessionOrchestratorCreateSession:
    """Tests for session creation."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_creates_session_record(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should create a session record in the database."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)
                    orchestrator.run()

        # Session should be created
        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.branch_name == "test-branch"
        # Session starts as running and transitions to completed after successful run
        assert session.status == "completed"

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_creates_session_with_epic_id(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should create session with epic_id when provided."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=False)
            orchestrator.run(epic_id="epic-123")

        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.epic_id == "epic-123"


class TestSessionOrchestratorPreflight:
    """Tests for preflight execution."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_runs_preflight_on_start(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should run preflight checks after creating session."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=False)
            orchestrator.run()

        mock_preflight.assert_called_once_with(config)

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_halts_on_preflight_failure(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should halt session if preflight checks fail."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(
                passed=False,
                errors=["git_clean: Uncommitted changes detected"],
            )
            result = orchestrator.run()

        # Session should be marked as failed
        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.status == "failed"

        # Result should indicate failure
        assert result.status == "failed"
        assert "preflight" in result.error.lower()


class TestSessionOrchestratorTaskExecution:
    """Tests for task execution logic."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_executes_tasks_in_dependency_order(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should execute tasks in the correct dependency order."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return dummy tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run()

        # Should have called get_tasks to retrieve tasks
        mock_get_tasks.assert_called_once()

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_halts_on_task_failure(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should halt session if a task fails."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock execute_task to raise an exception
            with patch.object(orchestrator, "execute_task") as mock_execute:
                mock_execute.side_effect = Exception("Task execution failed")

                # Mock get_tasks to return a task
                with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                    mock_get_tasks.return_value = [
                        MagicMock(id="task-1", dependencies=[]),
                    ]

                    result = orchestrator.run()

                    # Session should be marked as halted
                    session = session_repo.get("test-session-id")
                    assert session is not None
                    assert session.status == "halted"
                    assert session.halt_reason is not None

                    # Result should indicate halt
                    assert result.status == "halted"


class TestSessionOrchestratorPostflight:
    """Tests for postflight execution."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_runs_postflight_after_tasks(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should run postflight checks after task execution."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run()

        # Should have called run_postflight
        mock_postflight.assert_called_once_with(config)

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_marks_failed_on_postflight_failure(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should mark session as failed if postflight fails."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to fail
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(
                        passed=False,
                        errors=["full_tests: Full test suite failed"],
                    )

                    orchestrator.run()

        # Session should be marked as failed
        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.status == "failed"


class TestSessionOrchestratorSessionStatus:
    """Tests for session status updates."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_updates_session_status_to_completed(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should update session status to 'completed' on success."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run()

        # Session should be marked as completed
        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.status == "completed"

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_sets_ended_at_timestamp(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should set ended_at timestamp when session finishes."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run()

        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.ended_at is not None

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_sets_preflight_passed_at(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should set preflight_passed_at timestamp when preflight passes."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run()

        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.preflight_passed_at is not None


class TestSessionOrchestratorResult:
    """Tests for SessionResult."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_returns_session_result(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should return a SessionResult object."""
        from jiro.core.session import SessionOrchestrator, SessionResult

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    result = orchestrator.run()

        assert isinstance(result, SessionResult)
        assert result.session_id == "test-session-id"
        assert result.status == "completed"
        assert result.error is None

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_result_contains_task_counts(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should include task completion counts in result."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    result = orchestrator.run()

        assert result.tasks_completed == 0
        assert result.tasks_failed == 0


class TestSessionOrchestratorEpicFiltering:
    """Tests for epic ID filtering."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_filters_tasks_by_epic_id(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should filter tasks by epic_id when provided."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to verify epic_id is passed
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    orchestrator.run(epic_id="epic-456")

        # Should have called get_tasks with epic_id
        mock_get_tasks.assert_called_once_with(epic_id="epic-456")


class TestSessionOrchestratorHalt:
    """Tests for session halt mechanism."""

    @pytest.mark.unit
    def test_halt_updates_session_status(
        self,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should update session status to 'halted' when halt is called."""
        from datetime import datetime

        from jiro.core.session import SessionOrchestrator
        from jiro.db.models import Session

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        session = Session(
            id="test-session",
            branch_name="test-branch",
            status="running",
            started_at=datetime.now(),
        )
        session_repo.create(session)

        orchestrator.halt(session, "Test halt reason")

        updated_session = session_repo.get("test-session")
        assert updated_session is not None
        assert updated_session.status == "halted"

    @pytest.mark.unit
    def test_halt_records_halt_reason(
        self,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should record halt reason in session."""
        from datetime import datetime

        from jiro.core.session import SessionOrchestrator
        from jiro.db.models import Session

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        session = Session(
            id="test-session",
            branch_name="test-branch",
            status="running",
            started_at=datetime.now(),
        )
        session_repo.create(session)

        halt_reason = "Review failed: code quality issues"
        orchestrator.halt(session, halt_reason)

        updated_session = session_repo.get("test-session")
        assert updated_session is not None
        assert updated_session.halt_reason == halt_reason

    @pytest.mark.unit
    def test_halt_sets_ended_at_timestamp(
        self,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should set ended_at timestamp when halt is called."""
        from datetime import datetime

        from jiro.core.session import SessionOrchestrator
        from jiro.db.models import Session

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        session = Session(
            id="test-session",
            branch_name="test-branch",
            status="running",
            started_at=datetime.now(),
        )
        session_repo.create(session)

        orchestrator.halt(session, "Test halt")

        updated_session = session_repo.get("test-session")
        assert updated_session is not None
        assert updated_session.ended_at is not None


class TestSessionOrchestratorParallelExecution:
    """Tests for parallel task execution."""

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_routes_to_sequential_when_parallel_disabled(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should execute sequentially when parallel mode is disabled."""
        from jiro.core.session import SessionOrchestrator

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        # Ensure parallel is disabled (default)
        assert config.parallel.enabled is False

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with (
            patch.object(orchestrator, "run_preflight") as mock_preflight,
            patch.object(orchestrator, "get_tasks") as mock_get_tasks,
            patch.object(orchestrator, "execute_task") as mock_execute,
            patch.object(orchestrator, "run_postflight") as mock_postflight,
        ):
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return a task
            mock_task = MagicMock(id="task-1")
            mock_get_tasks.return_value = [mock_task]

            # Mock postflight to pass
            mock_postflight.return_value = PostflightResult(passed=True)

            result = orchestrator.run()

            # Task should have been executed
            mock_execute.assert_called_once_with(mock_task, "test-session-id")

        # Result should be successful
        assert result.status == "completed"
        assert result.tasks_completed == 1

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    @patch("jiro.core.session.WorktreeMerger")
    @patch("jiro.core.session.TaskScheduler")
    @patch("jiro.core.session.WorktreeManager")
    def test_orchestrator_routes_to_parallel_when_enabled(
        self,
        mock_worktree_class,
        mock_scheduler_class,
        mock_merger_class,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should execute in parallel when parallel mode is enabled."""
        from jiro.core.session import SessionOrchestrator

        # Enable parallel execution
        config.parallel.enabled = True
        config.parallel.max_parallel_tasks = 4

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        # Mock parallel components
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_scheduler.pending_queue = []
        mock_scheduler.executing_tasks = {}
        mock_scheduler.queue_task.return_value = MagicMock()
        mock_scheduler.dispatch_next.return_value = None

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    result = orchestrator.run()

        # Parallel components should be initialized
        mock_worktree_class.assert_called_once()
        mock_scheduler_class.assert_called_once()

        # Result should be successful
        assert result.status == "completed"

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_respects_max_parallel_tasks_config(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should pass max_parallel_tasks to scheduler."""
        from jiro.core.session import SessionOrchestrator

        # Configure parallel execution with custom max
        config.parallel.enabled = True
        config.parallel.max_parallel_tasks = 8

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    with patch("jiro.core.session.TaskScheduler") as mock_scheduler_class:
                        mock_scheduler = MagicMock()
                        mock_scheduler_class.return_value = mock_scheduler
                        mock_scheduler.pending_queue = []
                        mock_scheduler.executing_tasks = {}

                        orchestrator.run()

                        # TaskScheduler should be initialized with max_parallel_tasks=8
                        call_args = mock_scheduler_class.call_args
                        assert call_args is not None
                        assert call_args[1]["max_parallel"] == 8

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_uses_merge_target_branch(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should use configured merge target branch."""
        from jiro.core.session import SessionOrchestrator

        # Configure parallel execution with custom merge target
        config.parallel.enabled = True
        config.parallel.merge_target_branch = "develop"

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock get_tasks to return no tasks
            with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                mock_get_tasks.return_value = []

                # Mock postflight to pass
                with patch.object(orchestrator, "run_postflight") as mock_postflight:
                    mock_postflight.return_value = PostflightResult(passed=True)

                    with patch("jiro.core.session.TaskScheduler") as mock_scheduler_class:
                        mock_scheduler = MagicMock()
                        mock_scheduler_class.return_value = mock_scheduler
                        mock_scheduler.pending_queue = []
                        mock_scheduler.executing_tasks = {}

                        orchestrator.run()

                        # Merge target should be stored in config
                        assert config.parallel.merge_target_branch == "develop"

    @pytest.mark.unit
    @patch("jiro.core.session.subprocess.run")
    @patch("jiro.core.session.uuid.uuid4")
    def test_orchestrator_halts_on_parallel_task_failure(
        self,
        mock_uuid,
        mock_subprocess,
        config: Config,
        session_repo: SessionRepository,
        task_repo: TaskExecutionRepository,
    ) -> None:
        """Should halt session if a task fails in parallel mode."""
        from jiro.core.session import SessionOrchestrator

        config.parallel.enabled = True

        mock_uuid.return_value.hex = "test-session-id"
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test-branch\n"

        orchestrator = SessionOrchestrator(
            config=config,
            session_repo=session_repo,
            task_repo=task_repo,
        )

        # Mock preflight to pass
        with patch.object(orchestrator, "run_preflight") as mock_preflight:
            mock_preflight.return_value = PreflightResult(passed=True)

            # Mock execute_task to raise an exception
            with patch.object(orchestrator, "execute_task") as mock_execute:
                mock_execute.side_effect = Exception("Task execution failed")

                # Mock get_tasks to return a task
                with patch.object(orchestrator, "get_tasks") as mock_get_tasks:
                    mock_task = MagicMock(id="task-1")
                    mock_get_tasks.return_value = [mock_task]

                    with patch("jiro.core.session.TaskScheduler") as mock_scheduler_class:
                        mock_scheduler = MagicMock()
                        mock_scheduler_class.return_value = mock_scheduler

                        # Simulate task queuing and dispatching
                        mock_scheduler.pending_queue = []
                        mock_scheduler.executing_tasks = {"task-1": MagicMock(task_id="task-1")}
                        mock_scheduler.queue_task.return_value = MagicMock()
                        mock_scheduler.dispatch_next.side_effect = [
                            MagicMock(task_id="task-1", worktree_path="/tmp/wt"),
                            None,
                        ]

                        result = orchestrator.run()

        # Session should be marked as halted
        session = session_repo.get("test-session-id")
        assert session is not None
        assert session.status == "halted"

        # Result should indicate halt
        assert result.status == "halted"
        assert result.error is not None
