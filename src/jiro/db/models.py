"""Database models for jiro."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SessionStatus = Literal["running", "completed", "failed", "halted"]
AgentType = Literal["dreaming", "planning", "execution", "review"]
TaskPhase = Literal["preflight", "executing", "postflight"]
TaskStatus = Literal["running", "success", "failed", "halted"]


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
