"""Tests for CommitRepository CRUD operations."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import Commit, Session
from jiro.db.repository import CommitRepository, SessionRepository


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
def repository(db_with_schema: Database) -> CommitRepository:
    """Provide a CommitRepository instance."""
    return CommitRepository(db_with_schema)


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
def sample_commit() -> Commit:
    """Provide a sample Commit instance."""
    return Commit(
        id="commit-1",
        task_id="task-1",
        sha="abc123def456",
        commit_type="tdd_green",
        message="feat: implement feature X",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestCommitRepositoryCreate:
    """Tests for create() method."""

    @pytest.mark.unit
    def test_create_commit_returns_commit(
        self,
        repository: CommitRepository,
        sample_commit: Commit,
    ) -> None:
        """Should create and return a Commit."""
        result = repository.create(sample_commit)
        assert result.id == sample_commit.id
        assert result.task_id == sample_commit.task_id
        assert result.sha == sample_commit.sha
        assert result.commit_type == sample_commit.commit_type
        assert result.message == sample_commit.message

    @pytest.mark.unit
    def test_create_persists_to_database(
        self,
        repository: CommitRepository,
        sample_commit: Commit,
        db_with_schema: Database,
    ) -> None:
        """Should persist the commit to the database."""
        repository.create(sample_commit)
        # Query directly from database
        rows = list(db_with_schema["commits"].rows_where("id = ?", [sample_commit.id]))
        assert len(rows) == 1
        assert rows[0]["id"] == sample_commit.id
        assert rows[0]["sha"] == sample_commit.sha

    @pytest.mark.unit
    def test_create_with_session_id(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle session_id field."""
        _create_test_session(session_repository, "session-1")
        commit = Commit(
            id="commit-2",
            task_id="task-1",
            sha="xyz789",
            commit_type="bug_fix",
            message="fix: resolve issue",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        result = repository.create(commit)
        assert result.session_id == "session-1"

    @pytest.mark.unit
    def test_create_with_verification_details(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should handle verification command and results."""
        _create_test_session(session_repository, "session-verify")
        commit = Commit(
            id="commit-3",
            task_id="task-1",
            sha="def456",
            commit_type="tdd_red",
            message="test: add failing test",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-verify",
            verification_command="pytest tests/",
            verification_results="PASSED",
            time_taken_seconds=42,
            context_tokens_before=1000,
            context_tokens_after=1500,
        )
        result = repository.create(commit)
        assert result.verification_command == "pytest tests/"
        assert result.verification_results == "PASSED"
        assert result.time_taken_seconds == 42
        assert result.context_tokens_before == 1000
        assert result.context_tokens_after == 1500


class TestCommitRepositoryGet:
    """Tests for get() method."""

    @pytest.mark.unit
    def test_get_existing_commit(
        self,
        repository: CommitRepository,
        sample_commit: Commit,
    ) -> None:
        """Should retrieve an existing commit by id."""
        repository.create(sample_commit)
        result = repository.get(sample_commit.id)
        assert result is not None
        assert result.id == sample_commit.id
        assert result.task_id == sample_commit.task_id
        assert result.sha == sample_commit.sha
        assert result.commit_type == sample_commit.commit_type

    @pytest.mark.unit
    def test_get_nonexistent_commit_returns_none(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should return None for nonexistent commit."""
        result = repository.get("nonexistent-id")
        assert result is None

    @pytest.mark.unit
    def test_get_preserves_datetime_fields(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should correctly deserialize datetime fields."""
        commit = Commit(
            id="commit-4",
            task_id="task-1",
            sha="ghi789",
            commit_type="lint_fix",
            message="chore: format code",
            created_at=datetime(2025, 1, 1, 12, 30, 45),
        )
        repository.create(commit)
        result = repository.get(commit.id)
        assert result is not None
        assert result.created_at == datetime(2025, 1, 1, 12, 30, 45)

    @pytest.mark.unit
    def test_get_with_optional_fields(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should preserve all optional fields on retrieval."""
        _create_test_session(session_repository, "session-2")
        commit = Commit(
            id="commit-5",
            task_id="task-1",
            sha="jkl012",
            commit_type="performance",
            message="perf: optimize algorithm",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
            session_id="session-2",
            verification_command="npm run bench",
            verification_results="10% faster",
            time_taken_seconds=120,
            context_tokens_before=2000,
            context_tokens_after=2500,
        )
        repository.create(commit)
        result = repository.get(commit.id)
        assert result is not None
        assert result.session_id == "session-2"
        assert result.verification_command == "npm run bench"
        assert result.verification_results == "10% faster"
        assert result.time_taken_seconds == 120
        assert result.context_tokens_before == 2000
        assert result.context_tokens_after == 2500


class TestCommitRepositoryGetBySession:
    """Tests for get_by_session() method."""

    @pytest.mark.unit
    def test_get_by_session_returns_commits_for_session(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return commits for a specific session."""
        _create_test_session(session_repository, "session-1")
        _create_test_session(session_repository, "session-2")
        commit1 = Commit(
            id="commit-a",
            task_id="task-1",
            sha="aaa111",
            commit_type="tdd_green",
            message="feat: add feature",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        commit2 = Commit(
            id="commit-b",
            task_id="task-2",
            sha="bbb222",
            commit_type="bug_fix",
            message="fix: bug",
            created_at=datetime(2025, 1, 1, 12, 30, 0),
            session_id="session-1",
        )
        commit3 = Commit(
            id="commit-c",
            task_id="task-3",
            sha="ccc333",
            commit_type="docs",
            message="docs: update readme",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
            session_id="session-2",
        )

        repository.create(commit1)
        repository.create(commit2)
        repository.create(commit3)

        result = repository.get_by_session("session-1")
        assert len(result) == 2
        assert {c.id for c in result} == {"commit-a", "commit-b"}
        assert all(c.session_id == "session-1" for c in result)

    @pytest.mark.unit
    def test_get_by_session_empty_list(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return empty list for session with no commits."""
        _create_test_session(session_repository, "session-1")
        commit = Commit(
            id="commit-x",
            task_id="task-1",
            sha="xxx111",
            commit_type="tdd_red",
            message="test",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session-1",
        )
        repository.create(commit)

        result = repository.get_by_session("session-999")
        assert result == []

    @pytest.mark.unit
    def test_get_by_session_returns_list(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should always return a list."""
        result = repository.get_by_session("nonexistent")
        assert isinstance(result, list)


class TestCommitRepositoryGetByTask:
    """Tests for get_by_task() method."""

    @pytest.mark.unit
    def test_get_by_task_returns_commits_for_task(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should return commits for a specific task."""
        commit1 = Commit(
            id="commit-1",
            task_id="task-100",
            sha="t1c1",
            commit_type="tdd_red",
            message="test",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        commit2 = Commit(
            id="commit-2",
            task_id="task-100",
            sha="t1c2",
            commit_type="tdd_green",
            message="impl",
            created_at=datetime(2025, 1, 1, 12, 30, 0),
        )
        commit3 = Commit(
            id="commit-3",
            task_id="task-200",
            sha="t2c1",
            commit_type="bug_fix",
            message="fix",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
        )

        repository.create(commit1)
        repository.create(commit2)
        repository.create(commit3)

        result = repository.get_by_task("task-100")
        assert len(result) == 2
        assert {c.id for c in result} == {"commit-1", "commit-2"}
        assert all(c.task_id == "task-100" for c in result)

    @pytest.mark.unit
    def test_get_by_task_empty_list(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should return empty list for task with no commits."""
        commit = Commit(
            id="commit-y",
            task_id="task-1",
            sha="yyy111",
            commit_type="tdd_refactor",
            message="refactor",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(commit)

        result = repository.get_by_task("task-999")
        assert result == []

    @pytest.mark.unit
    def test_get_by_task_returns_list(
        self,
        repository: CommitRepository,
    ) -> None:
        """Should always return a list."""
        result = repository.get_by_task("nonexistent")
        assert isinstance(result, list)


class TestCommitRepositoryGetByType:
    """Tests for get_by_type() method."""

    @pytest.mark.unit
    def test_get_by_type_filters_by_session_and_type(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return commits filtered by both session and commit type."""
        _create_test_session(session_repository, "sess-1")
        _create_test_session(session_repository, "sess-2")
        commit1 = Commit(
            id="c1",
            task_id="t1",
            sha="s1",
            commit_type="tdd_red",
            message="m1",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="sess-1",
        )
        commit2 = Commit(
            id="c2",
            task_id="t2",
            sha="s2",
            commit_type="tdd_green",
            message="m2",
            created_at=datetime(2025, 1, 1, 12, 30, 0),
            session_id="sess-1",
        )
        commit3 = Commit(
            id="c3",
            task_id="t3",
            sha="s3",
            commit_type="tdd_red",
            message="m3",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
            session_id="sess-1",
        )
        commit4 = Commit(
            id="c4",
            task_id="t4",
            sha="s4",
            commit_type="tdd_red",
            message="m4",
            created_at=datetime(2025, 1, 1, 13, 30, 0),
            session_id="sess-2",
        )

        repository.create(commit1)
        repository.create(commit2)
        repository.create(commit3)
        repository.create(commit4)

        result = repository.get_by_type("sess-1", "tdd_red")
        assert len(result) == 2
        assert {c.id for c in result} == {"c1", "c3"}
        assert all(c.session_id == "sess-1" and c.commit_type == "tdd_red" for c in result)

    @pytest.mark.unit
    def test_get_by_type_no_matches(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return empty list when no commits match filters."""
        _create_test_session(session_repository, "sess-1")
        commit = Commit(
            id="c",
            task_id="t",
            sha="s",
            commit_type="bug_fix",
            message="m",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="sess-1",
        )
        repository.create(commit)

        result = repository.get_by_type("sess-1", "tdd_red")
        assert result == []

    @pytest.mark.unit
    def test_get_by_type_different_session_same_type(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should not return commits from different sessions."""
        _create_test_session(session_repository, "sess-1")
        _create_test_session(session_repository, "sess-2")
        commit1 = Commit(
            id="c1",
            task_id="t1",
            sha="s1",
            commit_type="tdd_green",
            message="m1",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id="sess-1",
        )
        commit2 = Commit(
            id="c2",
            task_id="t2",
            sha="s2",
            commit_type="tdd_green",
            message="m2",
            created_at=datetime(2025, 1, 1, 12, 30, 0),
            session_id="sess-2",
        )

        repository.create(commit1)
        repository.create(commit2)

        result = repository.get_by_type("sess-1", "tdd_green")
        assert len(result) == 1
        assert result[0].id == "c1"

    @pytest.mark.unit
    def test_get_by_type_all_commit_types(
        self,
        repository: CommitRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should work with all valid commit types."""
        _create_test_session(session_repository, "sess-test")
        commit_types = [
            "docs",
            "tdd_red",
            "tdd_green",
            "tdd_refactor",
            "lint_fix",
            "bug_fix",
            "config",
            "test_only",
            "performance",
        ]

        for i, ctype in enumerate(commit_types):
            commit = Commit(
                id=f"c{i}",
                task_id=f"t{i}",
                sha=f"s{i}",
                commit_type=ctype,  # type: ignore
                message=f"m{i}",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
                session_id="sess-test",
            )
            repository.create(commit)

        for ctype in commit_types:
            result = repository.get_by_type("sess-test", ctype)  # type: ignore
            assert len(result) == 1
            assert result[0].commit_type == ctype
