"""Tests for database models."""

from datetime import datetime

import pytest

from jiro.db.models import AgentType, Prompt, Session, SessionStatus


class TestSession:
    """Tests for Session dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """Session should require id, branch_name, status, started_at."""
        session = Session(
            id="sess-123",
            branch_name="feature/test",
            status="running",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert session.id == "sess-123"
        assert session.branch_name == "feature/test"
        assert session.status == "running"
        assert session.started_at == datetime(2024, 1, 15, 10, 30, 0)

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        session = Session(
            id="sess-123",
            branch_name="main",
            status="running",
            started_at=datetime.now(),
        )
        assert session.epic_id is None
        assert session.ended_at is None
        assert session.preflight_passed_at is None
        assert session.halt_reason is None

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """Session should accept all fields."""
        session = Session(
            id="sess-123",
            branch_name="feature/test",
            status="completed",
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            epic_id="epic-456",
            ended_at=datetime(2024, 1, 15, 12, 0, 0),
            preflight_passed_at=datetime(2024, 1, 15, 10, 5, 0),
            halt_reason=None,
        )
        assert session.epic_id == "epic-456"
        assert session.ended_at == datetime(2024, 1, 15, 12, 0, 0)
        assert session.preflight_passed_at == datetime(2024, 1, 15, 10, 5, 0)

    @pytest.mark.unit
    def test_from_row(self) -> None:
        """from_row should deserialize from database row."""
        row = {
            "id": "sess-123",
            "branch_name": "feature/test",
            "status": "running",
            "started_at": "2024-01-15T10:30:00",
            "epic_id": "epic-456",
            "ended_at": None,
            "preflight_passed_at": "2024-01-15T10:35:00",
            "halt_reason": None,
        }
        session = Session.from_row(row)
        assert session.id == "sess-123"
        assert session.branch_name == "feature/test"
        assert session.status == "running"
        assert session.started_at == datetime(2024, 1, 15, 10, 30, 0)
        assert session.epic_id == "epic-456"
        assert session.ended_at is None
        assert session.preflight_passed_at == datetime(2024, 1, 15, 10, 35, 0)

    @pytest.mark.unit
    def test_from_row_with_all_datetimes(self) -> None:
        """from_row should handle all datetime fields."""
        row = {
            "id": "sess-123",
            "branch_name": "main",
            "status": "completed",
            "started_at": "2024-01-15T10:00:00",
            "epic_id": None,
            "ended_at": "2024-01-15T12:00:00",
            "preflight_passed_at": "2024-01-15T10:05:00",
            "halt_reason": None,
        }
        session = Session.from_row(row)
        assert session.ended_at == datetime(2024, 1, 15, 12, 0, 0)

    @pytest.mark.unit
    def test_to_row(self) -> None:
        """to_row should serialize to database row."""
        session = Session(
            id="sess-123",
            branch_name="feature/test",
            status="running",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
            epic_id="epic-456",
            ended_at=None,
            preflight_passed_at=datetime(2024, 1, 15, 10, 35, 0),
            halt_reason=None,
        )
        row = session.to_row()
        assert row["id"] == "sess-123"
        assert row["branch_name"] == "feature/test"
        assert row["status"] == "running"
        assert row["started_at"] == "2024-01-15T10:30:00"
        assert row["epic_id"] == "epic-456"
        assert row["ended_at"] is None
        assert row["preflight_passed_at"] == "2024-01-15T10:35:00"
        assert row["halt_reason"] is None

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_row then from_row should produce equivalent object."""
        original = Session(
            id="sess-123",
            branch_name="feature/test",
            status="halted",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
            epic_id="epic-456",
            ended_at=datetime(2024, 1, 15, 11, 0, 0),
            preflight_passed_at=datetime(2024, 1, 15, 10, 35, 0),
            halt_reason="Test failed",
        )
        row = original.to_row()
        restored = Session.from_row(row)
        assert restored.id == original.id
        assert restored.branch_name == original.branch_name
        assert restored.status == original.status
        assert restored.started_at == original.started_at
        assert restored.epic_id == original.epic_id
        assert restored.ended_at == original.ended_at
        assert restored.preflight_passed_at == original.preflight_passed_at
        assert restored.halt_reason == original.halt_reason


class TestSessionStatus:
    """Tests for SessionStatus type alias."""

    @pytest.mark.unit
    def test_valid_statuses(self) -> None:
        """SessionStatus should allow valid values."""
        valid: list[SessionStatus] = ["running", "completed", "failed", "halted"]
        for status in valid:
            session = Session(
                id="test",
                branch_name="main",
                status=status,
                started_at=datetime.now(),
            )
            assert session.status == status


class TestPrompt:
    """Tests for Prompt dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """Prompt should require core fields."""
        prompt = Prompt(
            id="prompt-123",
            agent_type="planning",
            prompt_text="Analyze this code...",
            model="claude-opus-4-5-20250514",
            tokens_before=1000,
            tokens_after=1500,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert prompt.id == "prompt-123"
        assert prompt.agent_type == "planning"
        assert prompt.prompt_text == "Analyze this code..."
        assert prompt.model == "claude-opus-4-5-20250514"
        assert prompt.tokens_before == 1000
        assert prompt.tokens_after == 1500

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        prompt = Prompt(
            id="prompt-123",
            agent_type="execution",
            prompt_text="Execute step 1...",
            model="claude-haiku-4-5-20250514",
            tokens_before=500,
            tokens_after=800,
            created_at=datetime.now(),
        )
        assert prompt.session_id is None
        assert prompt.task_id is None

    @pytest.mark.unit
    def test_from_row(self) -> None:
        """from_row should deserialize from database row."""
        row = {
            "id": "prompt-123",
            "agent_type": "review",
            "prompt_text": "Review these commits...",
            "model": "claude-sonnet-4-5-20250514",
            "tokens_before": 2000,
            "tokens_after": 2500,
            "created_at": "2024-01-15T10:30:00",
            "session_id": "sess-456",
            "task_id": "task-789",
        }
        prompt = Prompt.from_row(row)
        assert prompt.id == "prompt-123"
        assert prompt.agent_type == "review"
        assert prompt.created_at == datetime(2024, 1, 15, 10, 30, 0)
        assert prompt.session_id == "sess-456"
        assert prompt.task_id == "task-789"

    @pytest.mark.unit
    def test_to_row(self) -> None:
        """to_row should serialize to database row."""
        prompt = Prompt(
            id="prompt-123",
            agent_type="dreaming",
            prompt_text="Dream up a feature spec...",
            model="claude-opus-4-5-20250514",
            tokens_before=100,
            tokens_after=500,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            session_id="sess-456",
            task_id=None,
        )
        row = prompt.to_row()
        assert row["id"] == "prompt-123"
        assert row["agent_type"] == "dreaming"
        assert row["created_at"] == "2024-01-15T10:30:00"
        assert row["session_id"] == "sess-456"
        assert row["task_id"] is None

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_row then from_row should produce equivalent object."""
        original = Prompt(
            id="prompt-123",
            agent_type="planning",
            prompt_text="Plan the implementation...",
            model="claude-opus-4-5-20250514",
            tokens_before=1000,
            tokens_after=1500,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            session_id="sess-456",
            task_id="task-789",
        )
        row = original.to_row()
        restored = Prompt.from_row(row)
        assert restored.id == original.id
        assert restored.agent_type == original.agent_type
        assert restored.prompt_text == original.prompt_text
        assert restored.model == original.model
        assert restored.tokens_before == original.tokens_before
        assert restored.tokens_after == original.tokens_after
        assert restored.created_at == original.created_at
        assert restored.session_id == original.session_id
        assert restored.task_id == original.task_id


class TestAgentType:
    """Tests for AgentType type alias."""

    @pytest.mark.unit
    def test_valid_agent_types(self) -> None:
        """AgentType should allow valid values."""
        valid: list[AgentType] = ["dreaming", "planning", "execution", "review"]
        for agent_type in valid:
            prompt = Prompt(
                id="test",
                agent_type=agent_type,
                prompt_text="test",
                model="test",
                tokens_before=0,
                tokens_after=0,
                created_at=datetime.now(),
            )
            assert prompt.agent_type == agent_type
