"""Tests for ExecutionPlanRepository CRUD operations."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import ExecutionPlan, Session
from jiro.db.repository import ExecutionPlanRepository, SessionRepository


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
def repository(db_with_schema: Database) -> ExecutionPlanRepository:
    """Provide an ExecutionPlanRepository instance."""
    return ExecutionPlanRepository(db_with_schema)


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
def sample_plan() -> ExecutionPlan:
    """Provide a sample ExecutionPlan instance."""
    return ExecutionPlan(
        id="plan-1",
        task_id="task-1",
        plan_json='{"steps": ["step1", "step2"], "files": ["src/foo.py"]}',
        created_at=datetime(2025, 1, 1, 12, 0, 0),
    )


class TestExecutionPlanRepositoryCreate:
    """Tests for create() method."""

    @pytest.mark.unit
    def test_create_plan_returns_plan(
        self,
        repository: ExecutionPlanRepository,
        sample_plan: ExecutionPlan,
    ) -> None:
        """Should create and return an ExecutionPlan."""
        result = repository.create(sample_plan)
        assert result.id == sample_plan.id
        assert result.task_id == sample_plan.task_id
        assert result.plan_json == sample_plan.plan_json

    @pytest.mark.unit
    def test_create_persists_to_database(
        self,
        repository: ExecutionPlanRepository,
        sample_plan: ExecutionPlan,
        db_with_schema: Database,
    ) -> None:
        """Should persist the plan to the database."""
        repository.create(sample_plan)
        rows = list(db_with_schema["execution_plans"].rows)
        assert len(rows) == 1
        assert rows[0]["id"] == sample_plan.id

    @pytest.mark.unit
    def test_create_with_session_id(
        self,
        repository: ExecutionPlanRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should create plan with session reference."""
        session = _create_test_session(session_repository, "sess-1")
        plan = ExecutionPlan(
            id="plan-1",
            task_id="task-1",
            plan_json='{"steps": []}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id=session.id,
        )
        result = repository.create(plan)
        assert result.session_id == session.id


class TestExecutionPlanRepositoryGet:
    """Tests for get() method."""

    @pytest.mark.unit
    def test_get_existing_plan(
        self,
        repository: ExecutionPlanRepository,
        sample_plan: ExecutionPlan,
    ) -> None:
        """Should retrieve an existing plan by ID."""
        repository.create(sample_plan)
        result = repository.get(sample_plan.id)
        assert result is not None
        assert result.id == sample_plan.id
        assert result.task_id == sample_plan.task_id
        assert result.plan_json == sample_plan.plan_json

    @pytest.mark.unit
    def test_get_nonexistent_plan(
        self,
        repository: ExecutionPlanRepository,
    ) -> None:
        """Should return None for nonexistent plan."""
        result = repository.get("nonexistent")
        assert result is None


class TestExecutionPlanRepositoryGetBySession:
    """Tests for get_by_session() method."""

    @pytest.mark.unit
    def test_get_by_session_returns_plans(
        self,
        repository: ExecutionPlanRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should return plans for a specific session."""
        session = _create_test_session(session_repository, "sess-1")
        plan1 = ExecutionPlan(
            id="plan-1",
            task_id="task-1",
            plan_json='{"steps": ["a"]}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id=session.id,
        )
        plan2 = ExecutionPlan(
            id="plan-2",
            task_id="task-2",
            plan_json='{"steps": ["b"]}',
            created_at=datetime(2025, 1, 1, 12, 5, 0),
            session_id=session.id,
        )
        repository.create(plan1)
        repository.create(plan2)

        results = repository.get_by_session(session.id)
        assert len(results) == 2
        assert {p.id for p in results} == {"plan-1", "plan-2"}

    @pytest.mark.unit
    def test_get_by_session_excludes_other_sessions(
        self,
        repository: ExecutionPlanRepository,
        session_repository: SessionRepository,
    ) -> None:
        """Should not return plans from other sessions."""
        session1 = _create_test_session(session_repository, "sess-1")
        session2 = _create_test_session(session_repository, "sess-2")
        plan1 = ExecutionPlan(
            id="plan-1",
            task_id="task-1",
            plan_json='{"steps": []}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id=session1.id,
        )
        plan2 = ExecutionPlan(
            id="plan-2",
            task_id="task-2",
            plan_json='{"steps": []}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            session_id=session2.id,
        )
        repository.create(plan1)
        repository.create(plan2)

        results = repository.get_by_session(session1.id)
        assert len(results) == 1
        assert results[0].id == "plan-1"

    @pytest.mark.unit
    def test_get_by_session_empty(
        self,
        repository: ExecutionPlanRepository,
    ) -> None:
        """Should return empty list for session with no plans."""
        results = repository.get_by_session("nonexistent")
        assert results == []


class TestExecutionPlanRepositoryGetByTask:
    """Tests for get_by_task() method."""

    @pytest.mark.unit
    def test_get_by_task_returns_plans(
        self,
        repository: ExecutionPlanRepository,
    ) -> None:
        """Should return plans for a specific task."""
        plan1 = ExecutionPlan(
            id="plan-1",
            task_id="task-1",
            plan_json='{"steps": ["a"]}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        plan2 = ExecutionPlan(
            id="plan-2",
            task_id="task-1",
            plan_json='{"steps": ["b"]}',
            created_at=datetime(2025, 1, 1, 12, 5, 0),
        )
        repository.create(plan1)
        repository.create(plan2)

        results = repository.get_by_task("task-1")
        assert len(results) == 2
        assert {p.id for p in results} == {"plan-1", "plan-2"}

    @pytest.mark.unit
    def test_get_by_task_excludes_other_tasks(
        self,
        repository: ExecutionPlanRepository,
    ) -> None:
        """Should not return plans from other tasks."""
        plan1 = ExecutionPlan(
            id="plan-1",
            task_id="task-1",
            plan_json='{"steps": []}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        plan2 = ExecutionPlan(
            id="plan-2",
            task_id="task-2",
            plan_json='{"steps": []}',
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        repository.create(plan1)
        repository.create(plan2)

        results = repository.get_by_task("task-1")
        assert len(results) == 1
        assert results[0].id == "plan-1"

    @pytest.mark.unit
    def test_get_by_task_empty(
        self,
        repository: ExecutionPlanRepository,
    ) -> None:
        """Should return empty list for task with no plans."""
        results = repository.get_by_task("nonexistent")
        assert results == []
