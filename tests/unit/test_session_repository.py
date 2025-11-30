"""Tests for SessionRepository CRUD operations."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import Session
from jiro.db.repository import SessionRepository


@pytest.fixture
def db_with_schema(tmp_path: Path) -> Database:
    """Provide a database with schema initialized."""
    db = get_database(tmp_path / "test.db")
    ensure_schema(db)
    return db


@pytest.fixture
def repository(db_with_schema: Database) -> SessionRepository:
    """Provide a SessionRepository instance."""
    return SessionRepository(db_with_schema)


@pytest.fixture
def sample_session() -> Session:
    """Provide a sample Session instance."""
    return Session(
        id="test-session-1",
        branch_name="test-branch",
        status="running",
        started_at=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestSessionRepositoryCreate:
    """Tests for create() method."""

    @pytest.mark.unit
    def test_create_session_returns_session(
        self,
        repository: SessionRepository,
        sample_session: Session,
    ) -> None:
        """Should create and return a Session."""
        result = repository.create(sample_session)
        assert result.id == sample_session.id
        assert result.branch_name == sample_session.branch_name
        assert result.status == sample_session.status

    @pytest.mark.unit
    def test_create_persists_to_database(
        self,
        repository: SessionRepository,
        sample_session: Session,
        db_with_schema: Database,
    ) -> None:
        """Should persist the session to the database."""
        repository.create(sample_session)
        # Query directly from database
        rows = list(db_with_schema["sessions"].rows_where("id = ?", [sample_session.id]))
        assert len(rows) == 1
        assert rows[0]["id"] == sample_session.id

    @pytest.mark.unit
    def test_create_with_optional_fields(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should handle optional fields like epic_id and halt_reason."""
        session = Session(
            id="test-session-2",
            branch_name="test-branch",
            status="failed",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            epic_id="epic-1",
            halt_reason="Memory exceeded",
        )
        result = repository.create(session)
        assert result.epic_id == "epic-1"
        assert result.halt_reason == "Memory exceeded"

    @pytest.mark.unit
    def test_create_with_ended_at(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should handle ended_at timestamp."""
        session = Session(
            id="test-session-3",
            branch_name="test-branch",
            status="completed",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            ended_at=datetime(2025, 1, 1, 13, 0, 0),
        )
        result = repository.create(session)
        assert result.ended_at == datetime(2025, 1, 1, 13, 0, 0)


class TestSessionRepositoryGet:
    """Tests for get() method."""

    @pytest.mark.unit
    def test_get_existing_session(
        self,
        repository: SessionRepository,
        sample_session: Session,
    ) -> None:
        """Should retrieve an existing session by id."""
        repository.create(sample_session)
        result = repository.get(sample_session.id)
        assert result is not None
        assert result.id == sample_session.id
        assert result.branch_name == sample_session.branch_name
        assert result.status == sample_session.status

    @pytest.mark.unit
    def test_get_nonexistent_session_returns_none(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should return None for nonexistent session."""
        result = repository.get("nonexistent-id")
        assert result is None

    @pytest.mark.unit
    def test_get_preserves_datetime_fields(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should correctly deserialize datetime fields."""
        session = Session(
            id="test-session-4",
            branch_name="test-branch",
            status="completed",
            started_at=datetime(2025, 1, 1, 12, 30, 45),
            ended_at=datetime(2025, 1, 1, 13, 45, 30),
            preflight_passed_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(session)
        result = repository.get(session.id)
        assert result is not None
        assert result.started_at == datetime(2025, 1, 1, 12, 30, 45)
        assert result.ended_at == datetime(2025, 1, 1, 13, 45, 30)
        assert result.preflight_passed_at == datetime(2025, 1, 1, 12, 0, 0)


class TestSessionRepositoryGetActive:
    """Tests for get_active() method."""

    @pytest.mark.unit
    def test_get_active_returns_running_sessions(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should return only running sessions."""
        # Create multiple sessions with different statuses
        session1 = Session(
            id="active-1",
            branch_name="branch1",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        session2 = Session(
            id="active-2",
            branch_name="branch2",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 30, 0),
        )
        completed = Session(
            id="completed-1",
            branch_name="branch3",
            status="completed",
            started_at=datetime(2025, 1, 1, 13, 0, 0),
        )

        repository.create(session1)
        repository.create(session2)
        repository.create(completed)

        result = repository.get_active()
        assert len(result) == 2
        assert all(s.status == "running" for s in result)
        assert {s.id for s in result} == {"active-1", "active-2"}

    @pytest.mark.unit
    def test_get_active_empty_list_when_no_running(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should return empty list when no running sessions."""
        session = Session(
            id="completed-2",
            branch_name="branch",
            status="completed",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(session)
        result = repository.get_active()
        assert result == []

    @pytest.mark.unit
    def test_get_active_returns_list(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should always return a list (possibly empty)."""
        result = repository.get_active()
        assert isinstance(result, list)


class TestSessionRepositoryUpdate:
    """Tests for update() method."""

    @pytest.mark.unit
    def test_update_session_status(
        self,
        repository: SessionRepository,
        sample_session: Session,
    ) -> None:
        """Should update a session's status."""
        repository.create(sample_session)
        # Modify and update
        sample_session.status = "completed"
        sample_session.ended_at = datetime(2025, 1, 1, 14, 0, 0)
        result = repository.update(sample_session)

        assert result.status == "completed"
        assert result.ended_at == datetime(2025, 1, 1, 14, 0, 0)

    @pytest.mark.unit
    def test_update_persists_changes(
        self,
        repository: SessionRepository,
        sample_session: Session,
        db_with_schema: Database,
    ) -> None:
        """Should persist changes to the database."""
        repository.create(sample_session)
        sample_session.status = "failed"
        sample_session.halt_reason = "Test failure"
        repository.update(sample_session)

        # Query directly from database
        rows = list(db_with_schema["sessions"].rows_where("id = ?", [sample_session.id]))
        assert len(rows) == 1
        assert rows[0]["status"] == "failed"
        assert rows[0]["halt_reason"] == "Test failure"

    @pytest.mark.unit
    def test_update_multiple_fields(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should update multiple fields at once."""
        session = Session(
            id="update-test",
            branch_name="old-branch",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(session)

        session.branch_name = "new-branch"
        session.status = "halted"
        session.halt_reason = "User stopped"
        session.preflight_passed_at = datetime(2025, 1, 1, 11, 0, 0)

        result = repository.update(session)
        assert result.branch_name == "new-branch"
        assert result.status == "halted"
        assert result.halt_reason == "User stopped"
        assert result.preflight_passed_at == datetime(2025, 1, 1, 11, 0, 0)


class TestSessionRepositoryGetByStatus:
    """Tests for get_by_status() method."""

    @pytest.mark.unit
    def test_get_by_status_filters_correctly(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should return only sessions with the specified status."""
        sessions_data = [
            ("session-1", "running"),
            ("session-2", "completed"),
            ("session-3", "running"),
            ("session-4", "failed"),
        ]

        for sid, status in sessions_data:
            session = Session(
                id=sid,
                branch_name=f"branch-{sid}",
                status=status,  # type: ignore
                started_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            repository.create(session)

        result = repository.get_by_status("running")
        assert len(result) == 2
        assert all(s.status == "running" for s in result)
        assert {s.id for s in result} == {"session-1", "session-3"}

    @pytest.mark.unit
    def test_get_by_status_completed(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should work with 'completed' status."""
        session1 = Session(
            id="s1",
            branch_name="b1",
            status="completed",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        session2 = Session(
            id="s2",
            branch_name="b2",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(session1)
        repository.create(session2)

        result = repository.get_by_status("completed")
        assert len(result) == 1
        assert result[0].id == "s1"

    @pytest.mark.unit
    def test_get_by_status_empty_result(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should return empty list for status with no sessions."""
        session = Session(
            id="s",
            branch_name="b",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(session)

        result = repository.get_by_status("failed")
        assert result == []

    @pytest.mark.unit
    def test_get_by_status_all_statuses(
        self,
        repository: SessionRepository,
    ) -> None:
        """Should work with all valid statuses."""
        statuses = ["running", "completed", "failed", "halted"]
        for i, status in enumerate(statuses):
            session = Session(
                id=f"s{i}",
                branch_name=f"b{i}",
                status=status,  # type: ignore
                started_at=datetime(2025, 1, 1, 12, 0, 0),
            )
            repository.create(session)

        for status in statuses:
            result = repository.get_by_status(status)
            assert len(result) == 1
            assert result[0].status == status
