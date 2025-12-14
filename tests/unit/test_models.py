"""Tests for database models."""

from datetime import datetime

import pytest

from jiro.db.models import (
    AgentType,
    Commit,
    CommitStatus,
    CommitType,
    Prompt,
    Session,
    SessionStatus,
    TaskExecution,
    TaskPhase,
    TaskStatus,
)


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


class TestTaskExecution:
    """Tests for TaskExecution dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """TaskExecution should require core fields."""
        task_exec = TaskExecution(
            id="exec-123",
            task_id="task-456",
            phase="executing",
            status="running",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert task_exec.id == "exec-123"
        assert task_exec.task_id == "task-456"
        assert task_exec.phase == "executing"
        assert task_exec.status == "running"
        assert task_exec.started_at == datetime(2024, 1, 15, 10, 30, 0)

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        task_exec = TaskExecution(
            id="exec-123",
            task_id="task-456",
            phase="preflight",
            status="running",
            started_at=datetime.now(),
        )
        assert task_exec.session_id is None
        assert task_exec.ended_at is None
        assert task_exec.halt_reason is None

    @pytest.mark.unit
    def test_from_row(self) -> None:
        """from_row should deserialize from database row."""
        row = {
            "id": "exec-123",
            "task_id": "task-456",
            "phase": "postflight",
            "status": "success",
            "started_at": "2024-01-15T10:30:00",
            "session_id": "sess-789",
            "ended_at": "2024-01-15T10:45:00",
            "halt_reason": None,
        }
        task_exec = TaskExecution.from_row(row)
        assert task_exec.id == "exec-123"
        assert task_exec.task_id == "task-456"
        assert task_exec.phase == "postflight"
        assert task_exec.status == "success"
        assert task_exec.started_at == datetime(2024, 1, 15, 10, 30, 0)
        assert task_exec.session_id == "sess-789"
        assert task_exec.ended_at == datetime(2024, 1, 15, 10, 45, 0)

    @pytest.mark.unit
    def test_to_row(self) -> None:
        """to_row should serialize to database row."""
        task_exec = TaskExecution(
            id="exec-123",
            task_id="task-456",
            phase="executing",
            status="running",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
            session_id="sess-789",
            ended_at=None,
            halt_reason=None,
        )
        row = task_exec.to_row()
        assert row["id"] == "exec-123"
        assert row["task_id"] == "task-456"
        assert row["phase"] == "executing"
        assert row["status"] == "running"
        assert row["started_at"] == "2024-01-15T10:30:00"
        assert row["session_id"] == "sess-789"
        assert row["ended_at"] is None
        assert row["halt_reason"] is None

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_row then from_row should produce equivalent object."""
        original = TaskExecution(
            id="exec-123",
            task_id="task-456",
            phase="postflight",
            status="halted",
            started_at=datetime(2024, 1, 15, 10, 30, 0),
            session_id="sess-789",
            ended_at=datetime(2024, 1, 15, 11, 0, 0),
            halt_reason="Tests failed",
        )
        row = original.to_row()
        restored = TaskExecution.from_row(row)
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.phase == original.phase
        assert restored.status == original.status
        assert restored.started_at == original.started_at
        assert restored.session_id == original.session_id
        assert restored.ended_at == original.ended_at
        assert restored.halt_reason == original.halt_reason


class TestTaskPhase:
    """Tests for TaskPhase type alias."""

    @pytest.mark.unit
    def test_valid_phases(self) -> None:
        """TaskPhase should allow valid values."""
        valid: list[TaskPhase] = ["preflight", "executing", "postflight"]
        for phase in valid:
            task_exec = TaskExecution(
                id="test",
                task_id="task-1",
                phase=phase,
                status="running",
                started_at=datetime.now(),
            )
            assert task_exec.phase == phase


class TestTaskStatus:
    """Tests for TaskStatus type alias."""

    @pytest.mark.unit
    def test_valid_statuses(self) -> None:
        """TaskStatus should allow valid values."""
        valid: list[TaskStatus] = ["running", "success", "failed", "halted"]
        for status in valid:
            task_exec = TaskExecution(
                id="test",
                task_id="task-1",
                phase="executing",
                status=status,
                started_at=datetime.now(),
            )
            assert task_exec.status == status


class TestCommit:
    """Tests for Commit dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """Commit should require core fields."""
        commit = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="docs",
            message="Add documentation for feature X",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        assert commit.id == "commit-123"
        assert commit.task_id == "task-456"
        assert commit.commit_type == "docs"
        assert commit.message == "Add documentation for feature X"
        assert commit.created_at == datetime(2024, 1, 15, 10, 30, 0)

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None or default values."""
        commit = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="tdd_red",
            message="Add failing test",
            created_at=datetime.now(),
        )
        # status defaults to "pending"
        assert commit.status == "pending"
        # sha defaults to None (not committed yet)
        assert commit.sha is None
        # metadata defaults to empty dict
        assert commit.metadata == {}
        # Other optional fields default to None
        assert commit.session_id is None
        assert commit.verification_command is None
        assert commit.verification_results is None
        assert commit.time_taken_seconds is None
        assert commit.context_tokens_before is None
        assert commit.context_tokens_after is None

    @pytest.mark.unit
    def test_from_row(self) -> None:
        """from_row should deserialize from database row."""
        row = {
            "id": "commit-123",
            "task_id": "task-456",
            "commit_type": "tdd_green",
            "message": "Implement feature",
            "created_at": "2024-01-15T10:30:00",
            "status": "committed",
            "sha": "abc123def456",
            "metadata": '{"test_file": "test_foo.py", "test_name": "test_bar"}',
            "session_id": "sess-789",
            "verification_command": "pytest tests/",
            "verification_results": "All tests passed",
            "time_taken_seconds": 120,
            "context_tokens_before": 5000,
            "context_tokens_after": 7500,
        }
        commit = Commit.from_row(row)
        assert commit.id == "commit-123"
        assert commit.task_id == "task-456"
        assert commit.commit_type == "tdd_green"
        assert commit.message == "Implement feature"
        assert commit.created_at == datetime(2024, 1, 15, 10, 30, 0)
        assert commit.status == "committed"
        assert commit.sha == "abc123def456"
        assert commit.metadata == {"test_file": "test_foo.py", "test_name": "test_bar"}
        assert commit.session_id == "sess-789"
        assert commit.verification_command == "pytest tests/"
        assert commit.verification_results == "All tests passed"
        assert commit.time_taken_seconds == 120
        assert commit.context_tokens_before == 5000
        assert commit.context_tokens_after == 7500

    @pytest.mark.unit
    def test_from_row_pending_status(self) -> None:
        """from_row should handle pending commits with null sha."""
        row = {
            "id": "commit-123",
            "task_id": "task-456",
            "commit_type": "tdd_red",
            "message": "Add failing test",
            "created_at": "2024-01-15T10:30:00",
            "status": "pending",
            "sha": None,
            "metadata": "{}",
        }
        commit = Commit.from_row(row)
        assert commit.status == "pending"
        assert commit.sha is None
        assert commit.metadata == {}

    @pytest.mark.unit
    def test_from_row_backward_compatibility(self) -> None:
        """from_row should default status to 'committed' for old rows."""
        row = {
            "id": "commit-123",
            "task_id": "task-456",
            "sha": "abc123def456",
            "commit_type": "docs",
            "message": "Legacy commit",
            "created_at": "2024-01-15T10:30:00",
            # No status or metadata fields (legacy row)
        }
        commit = Commit.from_row(row)
        assert commit.status == "committed"
        assert commit.sha == "abc123def456"
        assert commit.metadata == {}

    @pytest.mark.unit
    def test_to_row(self) -> None:
        """to_row should serialize to database row."""
        commit = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="tdd_refactor",
            message="Refactor code",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            status="committed",
            sha="abc123def456",
            metadata={"refactor_type": "extract_method"},
            session_id="sess-789",
            verification_command="pytest",
            verification_results="OK",
            time_taken_seconds=60,
            context_tokens_before=3000,
            context_tokens_after=3500,
        )
        row = commit.to_row()
        assert row["id"] == "commit-123"
        assert row["task_id"] == "task-456"
        assert row["commit_type"] == "tdd_refactor"
        assert row["message"] == "Refactor code"
        assert row["created_at"] == "2024-01-15T10:30:00"
        assert row["status"] == "committed"
        assert row["sha"] == "abc123def456"
        assert row["metadata"] == '{"refactor_type": "extract_method"}'
        assert row["session_id"] == "sess-789"
        assert row["verification_command"] == "pytest"
        assert row["verification_results"] == "OK"
        assert row["time_taken_seconds"] == 60
        assert row["context_tokens_before"] == 3000
        assert row["context_tokens_after"] == 3500

    @pytest.mark.unit
    def test_to_row_pending(self) -> None:
        """to_row should handle pending commits with null sha."""
        commit = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="tdd_red",
            message="Add failing test",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            status="pending",
            sha=None,
            metadata={},
        )
        row = commit.to_row()
        assert row["status"] == "pending"
        assert row["sha"] is None
        assert row["metadata"] == "{}"

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_row then from_row should produce equivalent object."""
        original = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="lint_fix",
            message="Fix linting errors",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            status="committed",
            sha="abc123def456789",
            metadata={"lint_rule": "E501", "file": "src/foo.py"},
            session_id="sess-789",
            verification_command="ruff check .",
            verification_results="No errors",
            time_taken_seconds=15,
            context_tokens_before=2000,
            context_tokens_after=2100,
        )
        row = original.to_row()
        restored = Commit.from_row(row)
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.commit_type == original.commit_type
        assert restored.message == original.message
        assert restored.created_at == original.created_at
        assert restored.status == original.status
        assert restored.sha == original.sha
        assert restored.metadata == original.metadata
        assert restored.session_id == original.session_id
        assert restored.verification_command == original.verification_command
        assert restored.verification_results == original.verification_results
        assert restored.time_taken_seconds == original.time_taken_seconds
        assert restored.context_tokens_before == original.context_tokens_before
        assert restored.context_tokens_after == original.context_tokens_after

    @pytest.mark.unit
    def test_roundtrip_pending(self) -> None:
        """Pending commits should roundtrip correctly."""
        original = Commit(
            id="commit-123",
            task_id="task-456",
            commit_type="tdd_red",
            message="Add failing test",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            status="pending",
            sha=None,
            metadata={"test_name": "test_foo"},
        )
        row = original.to_row()
        restored = Commit.from_row(row)
        assert restored.status == original.status
        assert restored.sha == original.sha
        assert restored.metadata == original.metadata


class TestCommitStatus:
    """Tests for CommitStatus type alias."""

    @pytest.mark.unit
    def test_valid_statuses(self) -> None:
        """CommitStatus should allow valid values."""
        valid: list[CommitStatus] = ["pending", "committed"]
        for status in valid:
            commit = Commit(
                id="test",
                task_id="task-1",
                commit_type="docs",
                message="test",
                created_at=datetime.now(),
                status=status,
            )
            assert commit.status == status


class TestCommitType:
    """Tests for CommitType type alias."""

    @pytest.mark.unit
    def test_valid_commit_types(self) -> None:
        """CommitType should allow valid values."""
        valid: list[CommitType] = [
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
        for commit_type in valid:
            commit = Commit(
                id="test",
                task_id="task-1",
                commit_type=commit_type,
                message="test",
                created_at=datetime.now(),
            )
            assert commit.commit_type == commit_type
