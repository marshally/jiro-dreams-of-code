"""Database models for jiro."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SessionStatus = Literal["running", "completed", "failed", "halted"]


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
