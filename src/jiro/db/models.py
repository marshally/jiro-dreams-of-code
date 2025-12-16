"""Database models for jiro."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

SessionStatus = Literal["running", "completed", "failed", "halted"]
AgentType = Literal["dreaming", "planning", "execution", "review"]
TaskPhase = Literal["preflight", "executing", "postflight"]
TaskStatus = Literal["running", "success", "failed", "halted"]
CommitStatus = Literal["pending", "committed"]
CommitType = Literal[
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


@dataclass
class Session:
    """Represents an execution session.

    A session is a single invocation of `jiro execute`. It tracks the overall
    state of task execution including preflight checks and completion status.
    """

    id: str
    branch_name: str
    status: SessionStatus
    started_at: datetime
    epic_id: str | None = None
    ended_at: datetime | None = None
    preflight_passed_at: datetime | None = None
    halt_reason: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """Deserialize from a database row.

        Args:
            row: Dictionary from sqlite-utils query.

        Returns:
            Session instance.
        """
        return cls(
            id=row["id"],
            branch_name=row["branch_name"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            epic_id=row.get("epic_id"),
            ended_at=(datetime.fromisoformat(row["ended_at"]) if row.get("ended_at") else None),
            preflight_passed_at=(
                datetime.fromisoformat(row["preflight_passed_at"])
                if row.get("preflight_passed_at")
                else None
            ),
            halt_reason=row.get("halt_reason"),
        )

    def to_row(self) -> dict:
        """Serialize to a database row.

        Returns:
            Dictionary suitable for sqlite-utils insert/update.
        """
        return {
            "id": self.id,
            "branch_name": self.branch_name,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "epic_id": self.epic_id,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "preflight_passed_at": (
                self.preflight_passed_at.isoformat() if self.preflight_passed_at else None
            ),
            "halt_reason": self.halt_reason,
        }


@dataclass
class Prompt:
    """Represents a prompt sent to an agent.

    Records every prompt sent to an agent for context tracking and debugging.
    """

    id: str
    agent_type: AgentType
    prompt_text: str
    model: str
    tokens_before: int
    tokens_after: int
    created_at: datetime
    session_id: str | None = None
    task_id: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Prompt":
        """Deserialize from a database row.

        Args:
            row: Dictionary from sqlite-utils query.

        Returns:
            Prompt instance.
        """
        return cls(
            id=row["id"],
            agent_type=row["agent_type"],
            prompt_text=row["prompt_text"],
            model=row["model"],
            tokens_before=row["tokens_before"],
            tokens_after=row["tokens_after"],
            created_at=datetime.fromisoformat(row["created_at"]),
            session_id=row.get("session_id"),
            task_id=row.get("task_id"),
        )

    def to_row(self) -> dict:
        """Serialize to a database row.

        Returns:
            Dictionary suitable for sqlite-utils insert/update.
        """
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "prompt_text": self.prompt_text,
            "model": self.model,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
            "task_id": self.task_id,
        }


@dataclass
class TaskExecution:
    """Represents the execution lifecycle of a task.

    Tracks each phase of task execution (preflight, executing, postflight)
    and their outcomes.
    """

    id: str
    task_id: str
    phase: TaskPhase
    status: TaskStatus
    started_at: datetime
    session_id: str | None = None
    ended_at: datetime | None = None
    halt_reason: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "TaskExecution":
        """Deserialize from a database row.

        Args:
            row: Dictionary from sqlite-utils query.

        Returns:
            TaskExecution instance.
        """
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            phase=row["phase"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            session_id=row.get("session_id"),
            ended_at=(datetime.fromisoformat(row["ended_at"]) if row.get("ended_at") else None),
            halt_reason=row.get("halt_reason"),
        )

    def to_row(self) -> dict:
        """Serialize to a database row.

        Returns:
            Dictionary suitable for sqlite-utils insert/update.
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "phase": self.phase,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "session_id": self.session_id,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "halt_reason": self.halt_reason,
        }


@dataclass
class Commit:
    """Represents a git commit created during task execution.

    Records every commit with verification details and context token tracking.

    The status field tracks the commit lifecycle:
    - 'pending': Commit record created, but git commit not yet executed
    - 'committed': Git commit succeeded, sha is populated

    The sha field is nullable because:
    - Set to None when status='pending' (before git commit)
    - Populated when status='committed' (after git commit succeeds)

    The metadata field stores step-specific structured data as JSON.
    """

    id: str
    task_id: str
    commit_type: CommitType
    message: str
    created_at: datetime
    status: CommitStatus = "pending"
    sha: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    verification_command: str | None = None
    verification_results: str | None = None
    time_taken_seconds: int | None = None
    context_tokens_before: int | None = None
    context_tokens_after: int | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Commit":
        """Deserialize from a database row.

        Args:
            row: Dictionary from sqlite-utils query.

        Returns:
            Commit instance.
        """
        # Handle metadata JSON deserialization
        metadata_raw = row.get("metadata")
        if metadata_raw is None:
            metadata = {}
        elif isinstance(metadata_raw, str):
            metadata = json.loads(metadata_raw)
        else:
            metadata = metadata_raw

        return cls(
            id=row["id"],
            task_id=row["task_id"],
            commit_type=row["commit_type"],
            message=row["message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row.get("status", "committed"),  # Default for backward compatibility
            sha=row.get("sha"),
            metadata=metadata,
            session_id=row.get("session_id"),
            verification_command=row.get("verification_command"),
            verification_results=row.get("verification_results"),
            time_taken_seconds=row.get("time_taken_seconds"),
            context_tokens_before=row.get("context_tokens_before"),
            context_tokens_after=row.get("context_tokens_after"),
        )

    def to_row(self) -> dict:
        """Serialize to a database row.

        Returns:
            Dictionary suitable for sqlite-utils insert/update.
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "commit_type": self.commit_type,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "sha": self.sha,
            "metadata": json.dumps(self.metadata),
            "session_id": self.session_id,
            "verification_command": self.verification_command,
            "verification_results": self.verification_results,
            "time_taken_seconds": self.time_taken_seconds,
            "context_tokens_before": self.context_tokens_before,
            "context_tokens_after": self.context_tokens_after,
        }


@dataclass
class ExecutionPlan:
    """Represents an execution plan generated by the planning agent.

    Stores the structured plan output from the planning agent, which includes
    specific files, line numbers, and step-by-step execution instructions.
    """

    id: str
    task_id: str
    plan_json: str
    created_at: datetime
    session_id: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "ExecutionPlan":
        """Deserialize from a database row.

        Args:
            row: Dictionary from sqlite-utils query.

        Returns:
            ExecutionPlan instance.
        """
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            plan_json=row["plan_json"],
            created_at=datetime.fromisoformat(row["created_at"]),
            session_id=row.get("session_id"),
        )

    def to_row(self) -> dict:
        """Serialize to a database row.

        Returns:
            Dictionary suitable for sqlite-utils insert/update.
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "plan_json": self.plan_json,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
        }
