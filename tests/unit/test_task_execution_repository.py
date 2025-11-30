"""Tests for TaskExecutionRepository CRUD operations."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import Session, TaskExecution
from jiro.db.repository import SessionRepository, TaskExecutionRepository


@pytest.fixture
def db_with_schema(tmp_path: Path) -> Database:
    """Provide a database with schema initialized."""
    db = get_database(tmp_path / "test.db")
    ensure_schema(db)
    return db


@pytest.fixture
def session_repository(db_with_schema: Database) -> SessionRepository:
    """Provide a SessionRepository instance."""
    return SessionRepository(db_with_schema)


@pytest.fixture
def repository(db_with_schema: Database) -> TaskExecutionRepository:
    """Provide a TaskExecutionRepository instance."""
    return TaskExecutionRepository(db_with_schema)


def _create_test_session(session_repo: SessionRepository, session_id: str) -> Session:
    """Helper to create a test session."""
    session = Session(
        id=session_id,
        branch_name=f"branch-{session_id}",
        status="running",
        started_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    return session_repo.create(session)


@pytest.fixture
def sample_task_execution() -> TaskExecution:
    """Provide a sample TaskExecution instance."""
    return TaskExecution(
        id="exec-1",
        task_id="task-1",
        phase="executing",
        status="running",
        started_at=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestTaskExecutionRepositoryCreate:
    """Tests for create() method."""

    @pytest.mark.unit
    def test_create_execution_returns_execution(
        self,
        repository: TaskExecutionRepository,
        sample_task_execution: TaskExecution,
    ) -> None:
        """Should create and return a TaskExecution."""
        result = repository.create(sample_task_execution)
        assert result.id == sample_task_execution.id
        assert result.task_id == sample_task_execution.task_id
        assert result.phase == sample_task_execution.phase
        assert result.status == sample_task_execution.status

    @pytest.mark.unit
    def test_create_persists_to_database(
        self,
        repository: TaskExecutionRepository,
        sample_task_execution: TaskExecution,
        db_with_schema: Database,
    ) -> None:
        """Should persist the execution to the database."""
        repository.create(sample_task_execution)
        # Query directly from database
        rows = list(
            db_with_schema["task_executions"].rows_where("id = ?", [sample_task_execution.id])
        )
        assert len(rows) == 1
        assert rows[0]["id"] == sample_task_execution.id

    @pytest.mark.unit
    def test_create_with_optional_fields(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle optional fields like session_id and ended_at."""
        _create_test_session(session_repository, "session-1")
        execution = TaskExecution(
            id="exec-2",
            task_id="task-1",
            phase="postflight",
            status="success",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
            ended_at=datetime(2025, 1, 1, 13, 0, 0),
        )
        result = repository.create(execution)
        assert result.session_id == "session-1"
        assert result.ended_at == datetime(2025, 1, 1, 13, 0, 0)

    @pytest.mark.unit
    def test_create_with_halt_reason(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should handle halt_reason field."""
        execution = TaskExecution(
            id="exec-3",
            task_id="task-2",
            phase="executing",
            status="halted",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            halt_reason="Memory exceeded",
        )
        result = repository.create(execution)
        assert result.halt_reason == "Memory exceeded"

    @pytest.mark.unit
    def test_create_with_all_phases(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should correctly store all valid phases."""
        phases = ["preflight", "executing", "postflight"]
        for i, phase in enumerate(phases):
            execution = TaskExecution(
                id=f"exec-phase-{i}",
                task_id=f"task-{i}",
                phase=phase,  # type: ignore
                status="running",
                started_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            result = repository.create(execution)
            assert result.phase == phase


class TestTaskExecutionRepositoryGet:
    """Tests for get() method."""

    @pytest.mark.unit
    def test_get_existing_execution(
        self,
        repository: TaskExecutionRepository,
        sample_task_execution: TaskExecution,
    ) -> None:
        """Should retrieve an existing execution by id."""
        repository.create(sample_task_execution)
        result = repository.get(sample_task_execution.id)
        assert result is not None
        assert result.id == sample_task_execution.id
        assert result.task_id == sample_task_execution.task_id
        assert result.phase == sample_task_execution.phase
        assert result.status == sample_task_execution.status

    @pytest.mark.unit
    def test_get_nonexistent_execution_returns_none(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should return None for nonexistent execution."""
        result = repository.get("nonexistent-id")
        assert result is None

    @pytest.mark.unit
    def test_get_preserves_datetime_fields(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should correctly deserialize datetime fields."""
        execution = TaskExecution(
            id="exec-4",
            task_id="task-3",
            phase="postflight",
            status="success",
            started_at=datetime(2025, 1, 1, 12, 30, 45),
            ended_at=datetime(2025, 1, 1, 13, 45, 30),
        )
        repository.create(execution)
        result = repository.get(execution.id)
        assert result is not None
        assert result.started_at == datetime(2025, 1, 1, 12, 30, 45)
        assert result.ended_at == datetime(2025, 1, 1, 13, 45, 30)

    @pytest.mark.unit
    def test_get_with_all_fields(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should retrieve all fields correctly."""
        _create_test_session(session_repository, "sess-123")
        execution = TaskExecution(
            id="exec-5",
            task_id="task-456",
            phase="preflight",
            status="failed",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            session_id="sess-123",
            ended_at=datetime(2025, 1, 1, 10, 30, 0),
            halt_reason="Setup failed",
        )
        repository.create(execution)
        result = repository.get(execution.id)
        assert result is not None
        assert result.task_id == "task-456"
        assert result.phase == "preflight"
        assert result.status == "failed"
        assert result.session_id == "sess-123"
        assert result.started_at == datetime(2025, 1, 1, 10, 0, 0)
        assert result.ended_at == datetime(2025, 1, 1, 10, 30, 0)
        assert result.halt_reason == "Setup failed"


class TestTaskExecutionRepositoryGetBySession:
    """Tests for get_by_session() method."""

    @pytest.mark.unit
    def test_get_by_session_returns_matching_executions(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return only executions for the specified session."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        executions_data = [
            ("exec-1", "task-1", "session-1"),
            ("exec-2", "task-2", "session-1"),
            ("exec-3", "task-3", "session-2"),
            ("exec-4", "task-4", "session-1"),
        ]

        for eid, tid, sid in executions_data:
            execution = TaskExecution(
                id=eid,
                task_id=tid,
                phase="executing",
                status="running",
                started_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id=sid,
            )
            repository.create(execution)

        result = repository.get_by_session("session-1")
        assert len(result) == 3
        assert all(e.session_id == "session-1" for e in result)
        assert {e.id for e in result} == {"exec-1", "exec-2", "exec-4"}

    @pytest.mark.unit
    def test_get_by_session_empty_result(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return empty list when session has no executions."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        execution = TaskExecution(
            id="exec-1",
            task_id="task-1",
            phase="executing",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        repository.create(execution)

        result = repository.get_by_session("session-2")
        assert result == []

    @pytest.mark.unit
    def test_get_by_session_returns_list(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should always return a list."""
        result = repository.get_by_session("nonexistent")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_by_session_handles_none_session_id(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should not return executions with None session_id."""
        _create_test_session(session_repository, "session-1")

        exec1 = TaskExecution(
            id="exec-1",
            task_id="task-1",
            phase="preflight",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id=None,
        )
        exec2 = TaskExecution(
            id="exec-2",
            task_id="task-2",
            phase="executing",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        repository.create(exec1)
        repository.create(exec2)

        result = repository.get_by_session("session-1")
        assert len(result) == 1
        assert result[0].id == "exec-2"


class TestTaskExecutionRepositoryGetByTask:
    """Tests for get_by_task() method."""

    @pytest.mark.unit
    def test_get_by_task_returns_matching_executions(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should return only executions for the specified task."""
        executions_data = [
            ("exec-1", "task-1"),
            ("exec-2", "task-1"),
            ("exec-3", "task-2"),
            ("exec-4", "task-1"),
        ]

        for eid, tid in executions_data:
            execution = TaskExecution(
                id=eid,
                task_id=tid,
                phase="executing",
                status="running",
                started_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            repository.create(execution)

        result = repository.get_by_task("task-1")
        assert len(result) == 3
        assert all(e.task_id == "task-1" for e in result)
        assert {e.id for e in result} == {"exec-1", "exec-2", "exec-4"}

    @pytest.mark.unit
    def test_get_by_task_empty_result(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should return empty list when task has no executions."""
        execution = TaskExecution(
            id="exec-1",
            task_id="task-1",
            phase="executing",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(execution)

        result = repository.get_by_task("task-2")
        assert result == []

    @pytest.mark.unit
    def test_get_by_task_returns_list(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should always return a list."""
        result = repository.get_by_task("nonexistent")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_by_task_different_statuses(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should return all executions for task regardless of status."""
        statuses = ["running", "success", "failed"]
        for i, status in enumerate(statuses):
            execution = TaskExecution(
                id=f"exec-{i}",
                task_id="task-1",
                phase="executing",
                status=status,  # type: ignore
                started_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            repository.create(execution)

        result = repository.get_by_task("task-1")
        assert len(result) == 3
        assert {e.id for e in result} == {"exec-0", "exec-1", "exec-2"}


class TestTaskExecutionRepositoryUpdate:
    """Tests for update() method."""

    @pytest.mark.unit
    def test_update_execution_status(
        self,
        repository: TaskExecutionRepository,
        sample_task_execution: TaskExecution,
    ) -> None:
        """Should update an execution's status."""
        repository.create(sample_task_execution)
        # Modify and update
        sample_task_execution.status = "success"
        sample_task_execution.ended_at = datetime(2025, 1, 1, 14, 0, 0)
        result = repository.update(sample_task_execution)

        assert result.status == "success"
        assert result.ended_at == datetime(2025, 1, 1, 14, 0, 0)

    @pytest.mark.unit
    def test_update_persists_changes(
        self,
        repository: TaskExecutionRepository,
        sample_task_execution: TaskExecution,
        db_with_schema: Database,
    ) -> None:
        """Should persist changes to the database."""
        repository.create(sample_task_execution)
        sample_task_execution.status = "failed"
        sample_task_execution.halt_reason = "Task error"
        repository.update(sample_task_execution)

        # Query directly from database
        rows = list(
            db_with_schema["task_executions"].rows_where("id = ?", [sample_task_execution.id])
        )
        assert len(rows) == 1
        assert rows[0]["status"] == "failed"
        assert rows[0]["halt_reason"] == "Task error"

    @pytest.mark.unit
    def test_update_multiple_fields(
        self,
        repository: TaskExecutionRepository,
    ) -> None:
        """Should update multiple fields at once."""
        execution = TaskExecution(
            id="update-test",
            task_id="task-1",
            phase="preflight",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(execution)

        execution.phase = "executing"
        execution.status = "halted"
        execution.halt_reason = "User stopped"
        execution.ended_at = datetime(2025, 1, 1, 13, 0, 0)

        result = repository.update(execution)
        assert result.phase == "executing"
        assert result.status == "halted"
        assert result.halt_reason == "User stopped"
        assert result.ended_at == datetime(2025, 1, 1, 13, 0, 0)

    @pytest.mark.unit
    def test_update_clears_optional_fields(
        self,
        repository: TaskExecutionRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle clearing optional fields."""
        _create_test_session(session_repository, "session-1")

        execution = TaskExecution(
            id="update-clear",
            task_id="task-1",
            phase="executing",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
            halt_reason="Original reason",
        )
        repository.create(execution)

        execution.halt_reason = None
        result = repository.update(execution)
        assert result.halt_reason is None

        # Verify in database
        fetched = repository.get(execution.id)
        assert fetched is not None
        assert fetched.halt_reason is None
