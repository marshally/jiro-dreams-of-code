"""Database wrapper using sqlite-utils."""

from pathlib import Path

from sqlite_utils import Database


def get_database(db_path: Path) -> Database:
    """Get database connection with foreign keys enabled.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Database instance with foreign keys enabled.
    """
    db = Database(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def ensure_schema(db: Database) -> None:
    """Create tables if they don't exist.

    Creates the four main tables for jiro:
    - sessions: Execution sessions
    - prompts: Agent prompts and responses
    - task_executions: Task execution lifecycle
    - commits: Git commits with metadata

    Args:
        db: Database instance.
    """
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

    # Execution plans
    db["execution_plans"].create(
        {
            "id": str,
            "task_id": str,
            "session_id": str,
            "plan_json": str,
            "created_at": str,
        },
        pk="id",
        foreign_keys=[("session_id", "sessions", "id")],
        if_not_exists=True,
    )

    # Create indexes for common queries
    _create_indexes(db)


def _create_indexes(db: Database) -> None:
    """Create indexes for common queries.

    Args:
        db: Database instance.
    """
    indexes = [
        ("idx_sessions_status", "sessions", "status"),
        ("idx_prompts_session", "prompts", "session_id"),
        ("idx_prompts_task", "prompts", "task_id"),
        ("idx_task_executions_session", "task_executions", "session_id"),
        ("idx_task_executions_task", "task_executions", "task_id"),
        ("idx_commits_session", "commits", "session_id"),
        ("idx_commits_task", "commits", "task_id"),
        ("idx_execution_plans_session", "execution_plans", "session_id"),
        ("idx_execution_plans_task", "execution_plans", "task_id"),
    ]

    for index_name, table, column in indexes:
        db.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"  # noqa: S608
        )
