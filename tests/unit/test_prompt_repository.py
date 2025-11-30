"""Tests for PromptRepository CRUD operations."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import Prompt, Session
from jiro.db.repository import PromptRepository, SessionRepository


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
def repository(db_with_schema: Database) -> PromptRepository:
    """Provide a PromptRepository instance."""
    return PromptRepository(db_with_schema)


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
def sample_prompt() -> Prompt:
    """Provide a sample Prompt instance."""
    return Prompt(
        id="prompt-1",
        agent_type="dreaming",
        prompt_text="What should we build?",
        model="claude-sonnet-4-5",
        tokens_before=100,
        tokens_after=150,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestPromptRepositoryCreate:
    """Tests for create() method."""

    @pytest.mark.unit
    def test_create_prompt_returns_prompt(
        self,
        repository: PromptRepository,
        sample_prompt: Prompt,
    ) -> None:
        """Should create and return a Prompt."""
        result = repository.create(sample_prompt)
        assert result.id == sample_prompt.id
        assert result.agent_type == sample_prompt.agent_type
        assert result.prompt_text == sample_prompt.prompt_text
        assert result.model == sample_prompt.model

    @pytest.mark.unit
    def test_create_persists_to_database(
        self,
        repository: PromptRepository,
        sample_prompt: Prompt,
        db_with_schema: Database,
    ) -> None:
        """Should persist the prompt to the database."""
        repository.create(sample_prompt)
        # Query directly from database
        rows = list(db_with_schema["prompts"].rows_where("id = ?", [sample_prompt.id]))
        assert len(rows) == 1
        assert rows[0]["id"] == sample_prompt.id

    @pytest.mark.unit
    def test_create_with_optional_fields(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle optional fields like session_id and task_id."""
        _create_test_session(session_repository, "session-1")
        prompt = Prompt(
            id="prompt-2",
            agent_type="planning",
            prompt_text="How do we implement this?",
            model="claude-sonnet-4-5",
            tokens_before=200,
            tokens_after=300,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
            task_id="task-1",
        )
        result = repository.create(prompt)
        assert result.session_id == "session-1"
        assert result.task_id == "task-1"

    @pytest.mark.unit
    def test_create_with_token_fields(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should correctly store token counts."""
        prompt = Prompt(
            id="prompt-3",
            agent_type="execution",
            prompt_text="Execute the plan",
            model="claude-sonnet-4-5",
            tokens_before=500,
            tokens_after=750,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        result = repository.create(prompt)
        assert result.tokens_before == 500
        assert result.tokens_after == 750


class TestPromptRepositoryGet:
    """Tests for get() method."""

    @pytest.mark.unit
    def test_get_existing_prompt(
        self,
        repository: PromptRepository,
        sample_prompt: Prompt,
    ) -> None:
        """Should retrieve an existing prompt by id."""
        repository.create(sample_prompt)
        result = repository.get(sample_prompt.id)
        assert result is not None
        assert result.id == sample_prompt.id
        assert result.prompt_text == sample_prompt.prompt_text

    @pytest.mark.unit
    def test_get_nonexistent_prompt_returns_none(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should return None for nonexistent prompt."""
        result = repository.get("nonexistent-id")
        assert result is None

    @pytest.mark.unit
    def test_get_preserves_datetime_fields(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should correctly deserialize datetime fields."""
        prompt = Prompt(
            id="prompt-4",
            agent_type="review",
            prompt_text="Review the changes",
            model="claude-sonnet-4-5",
            tokens_before=300,
            tokens_after=400,
            created_at=datetime(2025, 1, 1, 12, 30, 45),
        )
        repository.create(prompt)
        result = repository.get(prompt.id)
        assert result is not None
        assert result.created_at == datetime(2025, 1, 1, 12, 30, 45)

    @pytest.mark.unit
    def test_get_with_all_fields(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should retrieve all fields correctly."""
        _create_test_session(session_repository, "sess-123")
        prompt = Prompt(
            id="prompt-5",
            agent_type="dreaming",
            prompt_text="Build the feature",
            model="claude-haiku-4-5",
            tokens_before=150,
            tokens_after=250,
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            session_id="sess-123",
            task_id="task-456",
        )
        repository.create(prompt)
        result = repository.get(prompt.id)
        assert result is not None
        assert result.agent_type == "dreaming"
        assert result.prompt_text == "Build the feature"
        assert result.model == "claude-haiku-4-5"
        assert result.tokens_before == 150
        assert result.tokens_after == 250
        assert result.session_id == "sess-123"
        assert result.task_id == "task-456"


class TestPromptRepositoryGetBySession:
    """Tests for get_by_session() method."""

    @pytest.mark.unit
    def test_get_by_session_returns_matching_prompts(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return only prompts for the specified session."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        prompts_data = [
            ("prompt-1", "session-1", None),
            ("prompt-2", "session-1", None),
            ("prompt-3", "session-2", None),
            ("prompt-4", "session-1", "task-1"),
        ]

        for pid, sid, tid in prompts_data:
            prompt = Prompt(
                id=pid,
                agent_type="dreaming",
                prompt_text=f"Prompt {pid}",
                model="claude-sonnet-4-5",
                tokens_before=100,
                tokens_after=150,
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id=sid,
                task_id=tid,
            )
            repository.create(prompt)

        result = repository.get_by_session("session-1")
        assert len(result) == 3
        assert all(p.session_id == "session-1" for p in result)
        assert {p.id for p in result} == {"prompt-1", "prompt-2", "prompt-4"}

    @pytest.mark.unit
    def test_get_by_session_empty_result(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return empty list when session has no prompts."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        prompt = Prompt(
            id="prompt-1",
            agent_type="dreaming",
            prompt_text="Test",
            model="claude-sonnet-4-5",
            tokens_before=100,
            tokens_after=150,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        repository.create(prompt)

        result = repository.get_by_session("session-2")
        assert result == []

    @pytest.mark.unit
    def test_get_by_session_returns_list(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should always return a list."""
        result = repository.get_by_session("nonexistent")
        assert isinstance(result, list)


class TestPromptRepositoryGetByTask:
    """Tests for get_by_task() method."""

    @pytest.mark.unit
    def test_get_by_task_returns_matching_prompts(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return only prompts for the specified task."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")
        _create_test_session(session_repository, "session-3")

        prompts_data = [
            ("prompt-1", "session-1", "task-1"),
            ("prompt-2", "session-1", "task-1"),
            ("prompt-3", "session-2", "task-2"),
            ("prompt-4", "session-3", None),
        ]

        for pid, sid, tid in prompts_data:
            prompt = Prompt(
                id=pid,
                agent_type="planning",
                prompt_text=f"Prompt {pid}",
                model="claude-sonnet-4-5",
                tokens_before=100,
                tokens_after=150,
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id=sid,
                task_id=tid,
            )
            repository.create(prompt)

        result = repository.get_by_task("task-1")
        assert len(result) == 2
        assert all(p.task_id == "task-1" for p in result)
        assert {p.id for p in result} == {"prompt-1", "prompt-2"}

    @pytest.mark.unit
    def test_get_by_task_empty_result(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should return empty list when task has no prompts."""
        prompt = Prompt(
            id="prompt-1",
            agent_type="execution",
            prompt_text="Test",
            model="claude-sonnet-4-5",
            tokens_before=100,
            tokens_after=150,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            task_id="task-1",
        )
        repository.create(prompt)

        result = repository.get_by_task("task-2")
        assert result == []

    @pytest.mark.unit
    def test_get_by_task_handles_none_task_id(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should not return prompts with None task_id."""
        prompt1 = Prompt(
            id="prompt-1",
            agent_type="dreaming",
            prompt_text="No task",
            model="claude-sonnet-4-5",
            tokens_before=100,
            tokens_after=150,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            task_id=None,
        )
        prompt2 = Prompt(
            id="prompt-2",
            agent_type="planning",
            prompt_text="With task",
            model="claude-sonnet-4-5",
            tokens_before=100,
            tokens_after=150,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            task_id="task-1",
        )
        repository.create(prompt1)
        repository.create(prompt2)

        result = repository.get_by_task("task-1")
        assert len(result) == 1
        assert result[0].id == "prompt-2"


class TestPromptRepositoryGetTotalTokens:
    """Tests for get_total_tokens() method."""

    @pytest.mark.unit
    def test_get_total_tokens_sums_output_tokens(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should sum tokens_after for a session."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        prompts_data = [
            ("prompt-1", "session-1", 100, 150),
            ("prompt-2", "session-1", 200, 300),
            ("prompt-3", "session-2", 300, 400),
        ]

        for pid, sid, tokens_before, tokens_after in prompts_data:
            prompt = Prompt(
                id=pid,
                agent_type="dreaming",
                prompt_text=f"Prompt {pid}",
                model="claude-sonnet-4-5",
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id=sid,
            )
            repository.create(prompt)

        # Sum of tokens_after for session-1: 150 + 300 = 450
        result = repository.get_total_tokens("session-1")
        assert result == 450

    @pytest.mark.unit
    def test_get_total_tokens_empty_session(
        self,
        repository: PromptRepository,
    ) -> None:
        """Should return 0 for session with no prompts."""
        result = repository.get_total_tokens("nonexistent-session")
        assert result == 0

    @pytest.mark.unit
    def test_get_total_tokens_single_prompt(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle single prompt correctly."""
        _create_test_session(session_repository, "session-1")

        prompt = Prompt(
            id="prompt-1",
            agent_type="review",
            prompt_text="Review code",
            model="claude-sonnet-4-5",
            tokens_before=250,
            tokens_after=500,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        repository.create(prompt)

        result = repository.get_total_tokens("session-1")
        assert result == 500

    @pytest.mark.unit
    def test_get_total_tokens_multiple_sessions(
        self,
        repository: PromptRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should correctly aggregate tokens per session."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")

        # Session 1: 100 + 200 = 300
        for i in range(2):
            prompt = Prompt(
                id=f"s1-prompt-{i}",
                agent_type="dreaming",
                prompt_text=f"Session 1 prompt {i}",
                model="claude-sonnet-4-5",
                tokens_before=50,
                tokens_after=100 + i * 100,
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id="session-1",
            )
            repository.create(prompt)

        # Session 2: 400 + 500 = 900
        for i in range(2):
            prompt = Prompt(
                id=f"s2-prompt-{i}",
                agent_type="planning",
                prompt_text=f"Session 2 prompt {i}",
                model="claude-sonnet-4-5",
                tokens_before=100,
                tokens_after=400 + i * 100,
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id="session-2",
            )
            repository.create(prompt)

        assert repository.get_total_tokens("session-1") == 300
        assert repository.get_total_tokens("session-2") == 900
