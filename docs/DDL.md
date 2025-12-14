# Database Design (DDL)

> Data Definition Language for jiro's SQLite database.

## Overview

Jiro uses SQLite via `sqlite-utils` for storing execution state, context tracking, and audit history. Each jiro-managed project has its own database:

- Normal mode: `.jiro-dreams-of-code/jiro.db`
- Stealth mode: `~/.jiro-dreams-of-code/$PROJECT/jiro.db`

## Tables

### sessions

Tracks execution sessions—each `jiro execute` run creates a session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID for the session |
| `epic_id` | TEXT | | Epic filter if `--epic` was specified |
| `branch_name` | TEXT | NOT NULL | Git branch for this session |
| `status` | TEXT | NOT NULL | `running`, `completed`, `failed`, `halted` |
| `started_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `ended_at` | TEXT | | ISO 8601 timestamp when session ended |
| `preflight_passed_at` | TEXT | | When session preflight completed |
| `halt_reason` | TEXT | | Reason if status is `halted` |

**Status values:**

- `running` - Session is actively executing tasks
- `completed` - All tasks finished successfully
- `failed` - Session failed (tests, lint, etc.)
- `halted` - Human intervention required

### prompts

Records every prompt sent to an agent for context tracking and debugging.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID for the prompt |
| `session_id` | TEXT | REFERENCES sessions(id) | Parent session |
| `task_id` | TEXT | | Associated task (from beads) |
| `agent_type` | TEXT | NOT NULL | `dreaming`, `planning`, `execution`, `review` |
| `prompt_text` | TEXT | NOT NULL | Full prompt content |
| `model` | TEXT | NOT NULL | Model used (e.g., `claude-opus-4-5`) |
| `tokens_before` | INTEGER | NOT NULL | Context tokens before this prompt |
| `tokens_after` | INTEGER | NOT NULL | Context tokens after response |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |

### task_executions

Tracks the execution lifecycle of each task.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID for the execution record |
| `task_id` | TEXT | NOT NULL | Task ID from beads |
| `session_id` | TEXT | REFERENCES sessions(id) | Parent session |
| `phase` | TEXT | NOT NULL | `preflight`, `executing`, `postflight` |
| `started_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `ended_at` | TEXT | | ISO 8601 timestamp when phase ended |
| `status` | TEXT | NOT NULL | `running`, `success`, `failed`, `halted` |
| `halt_reason` | TEXT | | Reason if status is `halted` |

**Phase values:**

- `preflight` - Running relevant tests, lint, planning enhancement
- `executing` - Agent is executing the task
- `postflight` - Review validation, final tests, recording results

### commits

Records every commit created during execution with full audit trail.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID for the commit record |
| `task_id` | TEXT | NOT NULL | Task ID from beads |
| `session_id` | TEXT | REFERENCES sessions(id) | Parent session |
| `commit_type` | TEXT | NOT NULL | Commit type (see below) |
| `message` | TEXT | NOT NULL | Full commit message |
| `status` | TEXT | NOT NULL | `pending`, `committed` |
| `sha` | TEXT | | Git commit SHA (NULL until committed) |
| `metadata` | TEXT | NOT NULL | JSON structured data for step-specific info |
| `verification_command` | TEXT | | Command used to verify |
| `verification_results` | TEXT | | Output of verification command |
| `time_taken_seconds` | INTEGER | | Seconds spent on this commit |
| `context_tokens_before` | INTEGER | | Tokens before this work |
| `context_tokens_after` | INTEGER | | Tokens after this work |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |

**Status values:**

- `pending` - Commit record created, verification passed, git commit not yet executed
- `committed` - Git commit succeeded, sha is populated

**Commit type values:**

- `docs` - Documentation only (steel thread)
- `tdd_red` - Failing test (future)
- `tdd_green` - Minimal passing code (future)
- `tdd_refactor` - Behavior-neutral refactor (future)
- `lint_fix` - Single lint error fix (future)
- `bug_fix` - Bug fix (future)
- `config` - Configuration change (future)
- `test_only` - Adding tests to existing code (future)
- `performance` - Optimization (future)

______________________________________________________________________

## SQL Schema

```sql
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    epic_id TEXT,
    branch_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'halted')),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    preflight_passed_at TEXT,
    halt_reason TEXT
);

-- Prompts table
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    task_id TEXT,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('dreaming', 'planning', 'execution', 'review')),
    prompt_text TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_before INTEGER NOT NULL,
    tokens_after INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- Task executions table
CREATE TABLE IF NOT EXISTS task_executions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id),
    phase TEXT NOT NULL CHECK (phase IN ('preflight', 'executing', 'postflight')),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed', 'halted')),
    halt_reason TEXT
);

-- Commits table
CREATE TABLE IF NOT EXISTS commits (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id),
    commit_type TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'committed')),
    sha TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    verification_command TEXT,
    verification_results TEXT,
    time_taken_seconds INTEGER,
    context_tokens_before INTEGER,
    context_tokens_after INTEGER,
    created_at TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_prompts_session ON prompts(session_id);
CREATE INDEX IF NOT EXISTS idx_prompts_task ON prompts(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_session ON task_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_task ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_commits_session ON commits(session_id);
CREATE INDEX IF NOT EXISTS idx_commits_task ON commits(task_id);
```

______________________________________________________________________

## Python Models

```python
import json
from dataclasses import dataclass, asdict, field
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
        return cls(
            id=row["id"],
            branch_name=row["branch_name"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            epic_id=row.get("epic_id"),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row.get("ended_at") else None,
            preflight_passed_at=datetime.fromisoformat(row["preflight_passed_at"])
            if row.get("preflight_passed_at")
            else None,
            halt_reason=row.get("halt_reason"),
        )

    def to_row(self) -> dict:
        return {
            "id": self.id,
            "branch_name": self.branch_name,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "epic_id": self.epic_id,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "preflight_passed_at": self.preflight_passed_at.isoformat()
            if self.preflight_passed_at
            else None,
            "halt_reason": self.halt_reason,
        }


@dataclass
class Prompt:
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
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            phase=row["phase"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            session_id=row.get("session_id"),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row.get("ended_at") else None,
            halt_reason=row.get("halt_reason"),
        )

    def to_row(self) -> dict:
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
```

______________________________________________________________________

## sqlite-utils Usage

```python
from sqlite_utils import Database
from pathlib import Path


def get_database(db_path: Path) -> Database:
    """Get database connection with foreign keys enabled."""
    db = Database(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def ensure_schema(db: Database) -> None:
    """Create tables if they don't exist."""

    # Sessions
    db["sessions"].create(
        {
            "id": str,
            "epic_id": str,
            "branch_name": str,
            "status": str,
            "started_at": str,
            "ended_at": str,
            "preflight_passed_at": str,
            "halt_reason": str,
        },
        pk="id",
        if_not_exists=True,
    )

    # Prompts
    db["prompts"].create(
        {
            "id": str,
            "session_id": str,
            "task_id": str,
            "agent_type": str,
            "prompt_text": str,
            "model": str,
            "tokens_before": int,
            "tokens_after": int,
            "created_at": str,
        },
        pk="id",
        foreign_keys=[("session_id", "sessions", "id")],
        if_not_exists=True,
    )

    # Task executions
    db["task_executions"].create(
        {
            "id": str,
            "task_id": str,
            "session_id": str,
            "phase": str,
            "started_at": str,
            "ended_at": str,
            "status": str,
            "halt_reason": str,
        },
        pk="id",
        foreign_keys=[("session_id", "sessions", "id")],
        if_not_exists=True,
    )

    # Commits
    db["commits"].create(
        {
            "id": str,
            "task_id": str,
            "session_id": str,
            "commit_type": str,
            "message": str,
            "status": str,
            "sha": str,
            "metadata": str,
            "verification_command": str,
            "verification_results": str,
            "time_taken_seconds": int,
            "context_tokens_before": int,
            "context_tokens_after": int,
            "created_at": str,
        },
        pk="id",
        foreign_keys=[("session_id", "sessions", "id")],
        if_not_exists=True,
    )
```

______________________________________________________________________

## Common Queries

```python
# Get active session
active = list(db["sessions"].rows_where("status = ?", ["running"]))

# Get all prompts for a session
prompts = list(db["prompts"].rows_where("session_id = ?", [session_id]))

# Calculate total tokens used in session
total_tokens = db.execute(
    """
    SELECT SUM(tokens_after - tokens_before) as total
    FROM prompts
    WHERE session_id = ?
""",
    [session_id],
).fetchone()["total"]

# Get commits for a task
commits = list(db["commits"].rows_where("task_id = ?", [task_id], order_by="created_at"))

# Count commits by type
by_type = db.execute(
    """
    SELECT commit_type, COUNT(*) as count
    FROM commits
    WHERE session_id = ?
    GROUP BY commit_type
""",
    [session_id],
).fetchall()

# Get halted sessions with reasons
halted = list(
    db["sessions"].rows_where(
        "status = ?", ["halted"], select="id, branch_name, halt_reason, started_at"
    )
)
```
