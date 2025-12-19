"""Tests for DreamSessionRepository."""

from datetime import datetime

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema
from jiro.db.models import DreamSession
from jiro.db.repository import DreamSessionRepository


@pytest.fixture
def db() -> Database:
    """Create an in-memory database with schema."""
    db = Database(":memory:")
    ensure_schema(db)
    return db


@pytest.fixture
def repository(db: Database) -> DreamSessionRepository:
    """Create a DreamSessionRepository with test database."""
    return DreamSessionRepository(db)


@pytest.fixture
def sample_session() -> DreamSession:
    """Create a sample DreamSession for testing."""
    now = datetime.now()
    return DreamSession(
        id="test-session-123",
        status="created",
        created_at=now,
        updated_at=now,
        conversation_json="[]",
        spec_json=None,
    )


class TestDreamSessionRepository:
    """Tests for DreamSessionRepository CRUD operations."""

    @pytest.mark.unit
    def test_create_session(
        self, repository: DreamSessionRepository, sample_session: DreamSession
    ) -> None:
        """Test creating a new dream session."""
        result = repository.create(sample_session)

        assert result.id == sample_session.id
        assert result.status == "created"

    @pytest.mark.unit
    def test_get_session_by_id(
        self, repository: DreamSessionRepository, sample_session: DreamSession
    ) -> None:
        """Test retrieving a session by ID."""
        repository.create(sample_session)

        result = repository.get(sample_session.id)

        assert result is not None
        assert result.id == sample_session.id
        assert result.status == "created"

    @pytest.mark.unit
    def test_get_nonexistent_session_returns_none(self, repository: DreamSessionRepository) -> None:
        """Test that getting a nonexistent session returns None."""
        result = repository.get("nonexistent-id")

        assert result is None

    @pytest.mark.unit
    def test_update_session(
        self, repository: DreamSessionRepository, sample_session: DreamSession
    ) -> None:
        """Test updating an existing session."""
        repository.create(sample_session)

        # Update the session
        sample_session.status = "interviewing"
        sample_session.conversation_json = '[{"role": "assistant", "content": "Hello!"}]'
        result = repository.update(sample_session)

        assert result.status == "interviewing"

        # Verify it persisted
        retrieved = repository.get(sample_session.id)
        assert retrieved is not None
        assert retrieved.status == "interviewing"
        assert "Hello!" in retrieved.conversation_json

    @pytest.mark.unit
    def test_delete_session(
        self, repository: DreamSessionRepository, sample_session: DreamSession
    ) -> None:
        """Test deleting a session."""
        repository.create(sample_session)

        repository.delete(sample_session.id)

        result = repository.get(sample_session.id)
        assert result is None

    @pytest.mark.unit
    def test_delete_nonexistent_session_no_error(self, repository: DreamSessionRepository) -> None:
        """Test that deleting a nonexistent session doesn't raise an error."""
        # Should not raise
        repository.delete("nonexistent-id")


class TestDreamSessionRepositoryGetIncomplete:
    """Tests for get_incomplete method."""

    @pytest.mark.unit
    def test_get_incomplete_returns_interviewing_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete returns sessions with interviewing status."""
        now = datetime.now()
        session = DreamSession(
            id="interview-session",
            status="interviewing",
            created_at=now,
            updated_at=now,
        )
        repository.create(session)

        result = repository.get_incomplete()

        assert len(result) == 1
        assert result[0].id == "interview-session"

    @pytest.mark.unit
    def test_get_incomplete_returns_created_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete returns sessions with created status."""
        now = datetime.now()
        session = DreamSession(
            id="created-session",
            status="created",
            created_at=now,
            updated_at=now,
        )
        repository.create(session)

        result = repository.get_incomplete()

        assert len(result) == 1
        assert result[0].id == "created-session"

    @pytest.mark.unit
    def test_get_incomplete_returns_generating_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete returns sessions with generating status."""
        now = datetime.now()
        session = DreamSession(
            id="generating-session",
            status="generating",
            created_at=now,
            updated_at=now,
        )
        repository.create(session)

        result = repository.get_incomplete()

        assert len(result) == 1
        assert result[0].id == "generating-session"

    @pytest.mark.unit
    def test_get_incomplete_excludes_completed_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete excludes completed sessions."""
        now = datetime.now()
        completed = DreamSession(
            id="completed-session",
            status="completed",
            created_at=now,
            updated_at=now,
        )
        repository.create(completed)

        result = repository.get_incomplete()

        assert len(result) == 0

    @pytest.mark.unit
    def test_get_incomplete_excludes_abandoned_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete excludes abandoned sessions."""
        now = datetime.now()
        abandoned = DreamSession(
            id="abandoned-session",
            status="abandoned",
            created_at=now,
            updated_at=now,
        )
        repository.create(abandoned)

        result = repository.get_incomplete()

        assert len(result) == 0

    @pytest.mark.unit
    def test_get_incomplete_returns_empty_when_all_complete(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete returns empty list when all sessions are done."""
        now = datetime.now()
        repository.create(
            DreamSession(id="completed-1", status="completed", created_at=now, updated_at=now)
        )
        repository.create(
            DreamSession(id="abandoned-1", status="abandoned", created_at=now, updated_at=now)
        )

        result = repository.get_incomplete()

        assert len(result) == 0

    @pytest.mark.unit
    def test_get_incomplete_returns_multiple_sessions(
        self, repository: DreamSessionRepository
    ) -> None:
        """Test that get_incomplete returns all incomplete sessions."""
        now = datetime.now()
        repository.create(
            DreamSession(id="session-1", status="created", created_at=now, updated_at=now)
        )
        repository.create(
            DreamSession(id="session-2", status="interviewing", created_at=now, updated_at=now)
        )
        repository.create(
            DreamSession(id="session-3", status="completed", created_at=now, updated_at=now)
        )

        result = repository.get_incomplete()

        assert len(result) == 2
        ids = {s.id for s in result}
        assert "session-1" in ids
        assert "session-2" in ids
        assert "session-3" not in ids


class TestDreamSessionSerialization:
    """Tests for DreamSession serialization/deserialization."""

    @pytest.mark.unit
    def test_conversation_json_roundtrip(self, repository: DreamSessionRepository) -> None:
        """Test that conversation JSON is preserved through save/load cycle."""
        now = datetime.now()
        conversation = '[{"role": "assistant", "content": "What do you want to build?"}, {"role": "user", "content": "A todo app"}]'
        session = DreamSession(
            id="json-test",
            status="interviewing",
            created_at=now,
            updated_at=now,
            conversation_json=conversation,
        )
        repository.create(session)

        result = repository.get("json-test")

        assert result is not None
        assert result.conversation_json == conversation

    @pytest.mark.unit
    def test_spec_json_roundtrip(self, repository: DreamSessionRepository) -> None:
        """Test that spec JSON is preserved through save/load cycle."""
        now = datetime.now()
        spec = '{"title": "Todo App", "overview": "A simple todo application"}'
        session = DreamSession(
            id="spec-test",
            status="completed",
            created_at=now,
            updated_at=now,
            spec_json=spec,
        )
        repository.create(session)

        result = repository.get("spec-test")

        assert result is not None
        assert result.spec_json == spec

    @pytest.mark.unit
    def test_datetime_roundtrip(self, repository: DreamSessionRepository) -> None:
        """Test that datetimes are preserved through save/load cycle."""
        created = datetime(2024, 1, 15, 10, 30, 0)
        updated = datetime(2024, 1, 15, 11, 45, 0)
        session = DreamSession(
            id="datetime-test",
            status="created",
            created_at=created,
            updated_at=updated,
        )
        repository.create(session)

        result = repository.get("datetime-test")

        assert result is not None
        assert result.created_at == created
        assert result.updated_at == updated
