"""Tests for database wrapper."""

from pathlib import Path

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database


class TestGetDatabase:
    """Tests for get_database function."""

    @pytest.mark.unit
    def test_returns_database_instance(self, tmp_path: Path) -> None:
        """Should return a Database instance."""
        db_path = tmp_path / "test.db"
        db = get_database(db_path)
        assert isinstance(db, Database)

    @pytest.mark.unit
    def test_creates_database_file(self, tmp_path: Path) -> None:
        """Should create the database file."""
        db_path = tmp_path / "test.db"
        get_database(db_path)
        assert db_path.exists()

    @pytest.mark.unit
    def test_foreign_keys_enabled(self, tmp_path: Path) -> None:
        """Should enable foreign keys."""
        db_path = tmp_path / "test.db"
        db = get_database(db_path)
        result = db.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1


class TestEnsureSchema:
    """Tests for ensure_schema function."""

    @pytest.mark.unit
    def test_creates_sessions_table(self, tmp_path: Path) -> None:
        """Should create sessions table."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        assert "sessions" in db.table_names()

    @pytest.mark.unit
    def test_creates_prompts_table(self, tmp_path: Path) -> None:
        """Should create prompts table."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        assert "prompts" in db.table_names()

    @pytest.mark.unit
    def test_creates_task_executions_table(self, tmp_path: Path) -> None:
        """Should create task_executions table."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        assert "task_executions" in db.table_names()

    @pytest.mark.unit
    def test_creates_commits_table(self, tmp_path: Path) -> None:
        """Should create commits table."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        assert "commits" in db.table_names()

    @pytest.mark.unit
    def test_sessions_has_correct_columns(self, tmp_path: Path) -> None:
        """Sessions table should have correct columns."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        columns = {col.name for col in db["sessions"].columns}
        expected = {
            "id",
            "epic_id",
            "branch_name",
            "status",
            "started_at",
            "ended_at",
            "preflight_passed_at",
            "halt_reason",
        }
        assert columns == expected

    @pytest.mark.unit
    def test_prompts_has_foreign_key_to_sessions(self, tmp_path: Path) -> None:
        """Prompts should have foreign key to sessions."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        fks = db["prompts"].foreign_keys
        session_fk = [fk for fk in fks if fk.other_table == "sessions"]
        assert len(session_fk) == 1

    @pytest.mark.unit
    def test_creates_indexes(self, tmp_path: Path) -> None:
        """Should create indexes for common queries."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        # Get all index names
        indexes = {
            row[1]
            for row in db.execute(
                "SELECT * FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            ).fetchall()
        }
        expected_indexes = {
            "idx_sessions_status",
            "idx_prompts_session",
            "idx_prompts_task",
            "idx_task_executions_session",
            "idx_task_executions_task",
            "idx_commits_session",
            "idx_commits_task",
        }
        assert expected_indexes.issubset(indexes)

    @pytest.mark.unit
    def test_idempotent(self, tmp_path: Path) -> None:
        """Calling ensure_schema multiple times should not error."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        ensure_schema(db)  # Should not raise
        assert "sessions" in db.table_names()
