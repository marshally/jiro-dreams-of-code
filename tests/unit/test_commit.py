"""Tests for commit creation functions."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlite_utils import Database

from jiro.db.database import ensure_schema, get_database
from jiro.db.models import Commit
from jiro.db.repository import CommitRepository


class TestCreateDocsCommit:
    """Tests for create_docs_commit() function."""

    @pytest.fixture
    def db_with_schema(self, tmp_path: Path) -> Database:
        """Provide a database with schema initialized."""
        db = get_database(tmp_path / "test.db")
        ensure_schema(db)
        return db

    @pytest.fixture
    def commit_repository(self, db_with_schema: Database) -> CommitRepository:
        """Provide a CommitRepository instance."""
        return CommitRepository(db_with_schema)

    @pytest.mark.unit
    def test_validates_only_markdown_files(self, commit_repository: CommitRepository) -> None:
        """Should raise ValidationError if non-markdown files are staged."""
        from jiro.core.commit import ValidationError, create_docs_commit

        with patch("jiro.core.commit.subprocess.run") as mock_run:
            # Mock git diff to return a Python file
            mock_run.return_value = MagicMock(
                stdout="src/main.py\n",
                returncode=0,
            )

            with pytest.raises(ValidationError) as exc_info:
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="mkdocs serve",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

            assert "non-documentation files" in str(exc_info.value)

    @pytest.mark.unit
    def test_allows_markdown_files(self, commit_repository: CommitRepository) -> None:
        """Should allow .md files in docs commit."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git diff to return markdown files
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\nDOCS/api.md\n", returncode=0)
                # Mock git commit
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template rendering
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add documentation"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs serve",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            assert result is not None
            assert result.task_id == "task-1"

    @pytest.mark.unit
    def test_renders_template_with_context(self, commit_repository: CommitRepository) -> None:
        """Should render template with all provided context variables."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git diff
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                return MagicMock(stdout="abc123def456", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add documentation"
            mock_load_template.return_value = mock_template

            create_docs_commit(
                task_id="task-1",
                task_type="feature",
                reason="Add API documentation",
                verification_command="mkdocs build",
                verification_results="Built successfully",
                time_taken_seconds=120,
                context_tokens_before=2000,
                context_tokens_after=2500,
                repository=commit_repository,
            )

            # Verify template was loaded with correct name
            mock_load_template.assert_called_once_with("commit/docs.txt.j2")

            # Verify template.render was called with correct context
            call_args = mock_template.render.call_args
            assert call_args is not None
            kwargs = call_args.kwargs if call_args.kwargs else call_args[0]

            # Should have all required fields
            assert "task_id" in kwargs
            assert kwargs["task_id"] == "task-1"
            assert kwargs["task_type"] == "feature"
            assert kwargs["reason"] == "Add API documentation"
            assert kwargs["verification_command"] == "mkdocs build"
            assert kwargs["verification_results"] == "Built successfully"
            assert kwargs["time_taken_seconds"] == 120
            assert kwargs["context_tokens_before"] == 2000
            assert kwargs["context_tokens_after"] == 2500

    @pytest.mark.unit
    def test_creates_git_commit(self, commit_repository: CommitRepository) -> None:
        """Should create a git commit with rendered message."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "commit" in cmd:
                    # Return commit SHA
                    return MagicMock(stdout="abc123def456", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            commit_message = "📝 docs(task-1): Add documentation\n\nDetails here"
            mock_template.render.return_value = commit_message
            mock_load_template.return_value = mock_template

            create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            # Verify git commit was called with the rendered message
            commit_calls = [call for call in mock_run.call_args_list if "commit" in call[0][0]]
            assert len(commit_calls) > 0

    @pytest.mark.unit
    def test_records_commit_in_database(
        self, commit_repository: CommitRepository, db_with_schema: Database
    ) -> None:
        """Should record the commit in the database."""
        from jiro.core.commit import create_docs_commit
        from jiro.db.models import Session
        from jiro.db.repository import SessionRepository

        # Create a session first (to satisfy foreign key constraint)
        session_repo = SessionRepository(db_with_schema)
        session = Session(
            id="session-1",
            branch_name="test-branch",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        session_repo.create(session)

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "rev-parse" in cmd or "log" in cmd:
                    return MagicMock(stdout="abc123def456\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs serve",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
                session_id="session-1",
            )

            # Verify commit was recorded
            assert result is not None
            assert result.task_id == "task-1"
            assert result.commit_type == "docs"
            assert result.message == "📝 docs(task-1): Add docs"
            assert result.sha == "abc123def456"

            # Verify it's in the database
            persisted = commit_repository.get(result.id)
            assert persisted is not None
            assert persisted.task_id == "task-1"

    @pytest.mark.unit
    def test_returns_commit_object(self, commit_repository: CommitRepository) -> None:
        """Should return a Commit object."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "rev-parse" in cmd:
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            assert isinstance(result, Commit)
            assert result.commit_type == "docs"

    @pytest.mark.unit
    def test_includes_optional_metadata(
        self, commit_repository: CommitRepository, db_with_schema: Database
    ) -> None:
        """Should include optional metadata fields in Commit."""
        from jiro.core.commit import create_docs_commit
        from jiro.db.models import Session
        from jiro.db.repository import SessionRepository

        # Create a session first (to satisfy foreign key constraint)
        session_repo = SessionRepository(db_with_schema)
        session = Session(
            id="session-1",
            branch_name="test-branch",
            status="running",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        session_repo.create(session)

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "rev-parse" in cmd:
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs build",
                verification_results="Built successfully",
                time_taken_seconds=120,
                context_tokens_before=2000,
                context_tokens_after=2500,
                repository=commit_repository,
                session_id="session-1",
            )

            # Verify optional fields
            assert result.verification_command == "mkdocs build"
            assert result.verification_results == "Built successfully"
            assert result.time_taken_seconds == 120
            assert result.context_tokens_before == 2000
            assert result.context_tokens_after == 2500
            assert result.session_id == "session-1"

    @pytest.mark.unit
    def test_raises_validation_error_on_python_files(
        self, commit_repository: CommitRepository
    ) -> None:
        """Should raise ValidationError for Python files."""
        from jiro.core.commit import ValidationError, create_docs_commit

        with patch("jiro.core.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="src/app.py\nsrc/main.py\n",
                returncode=0,
            )

            with pytest.raises(ValidationError):
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

    @pytest.mark.unit
    def test_allows_various_doc_extensions(self, commit_repository: CommitRepository) -> None:
        """Should allow various documentation file extensions."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(
                        stdout="README.md\nCHANGELOG.txt\ndocs/guide.rst\n",
                        returncode=0,
                    )
                elif "rev-parse" in cmd:
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="mkdocs",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            # Should not raise ValidationError
            assert result is not None

    @pytest.mark.unit
    def test_handles_files_without_extension(self, commit_repository: CommitRepository) -> None:
        """Should reject files without extensions as non-documentation files."""
        from jiro.core.commit import ValidationError, create_docs_commit

        with patch("jiro.core.commit.subprocess.run") as mock_run:
            # Mock git diff to return files without extensions
            mock_run.return_value = MagicMock(
                stdout="README\nLICENSE\n",
                returncode=0,
            )

            with pytest.raises(ValidationError):
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

    @pytest.mark.unit
    def test_raises_error_when_getting_staged_files_fails(
        self, commit_repository: CommitRepository
    ) -> None:
        """Should raise RuntimeError when git diff command fails."""
        from jiro.core.commit import create_docs_commit

        with patch("jiro.core.commit.subprocess.run") as mock_run:
            # Mock git diff to fail
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="fatal: not a git repository",
                returncode=1,
            )

            with pytest.raises(RuntimeError) as exc_info:
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

            assert "Failed to get staged files" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_error_when_git_commit_fails(self, commit_repository: CommitRepository) -> None:
        """Should raise RuntimeError when git commit command fails."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "commit" in cmd:
                    # Fail on commit
                    return MagicMock(
                        stdout="",
                        stderr="nothing to commit",
                        returncode=1,
                    )
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            with pytest.raises(RuntimeError) as exc_info:
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

            assert "Failed to create git commit" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_error_when_getting_commit_sha_fails(
        self, commit_repository: CommitRepository
    ) -> None:
        """Should raise RuntimeError when rev-parse command fails."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(stdout="README.md\n", returncode=0)
                elif "commit" in cmd:
                    return MagicMock(stdout="", returncode=0)
                elif "rev-parse" in cmd:
                    # Fail on rev-parse
                    return MagicMock(
                        stdout="",
                        stderr="fatal: not a git repository",
                        returncode=1,
                    )
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            with pytest.raises(RuntimeError) as exc_info:
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

            assert "Failed to get commit SHA" in str(exc_info.value)

    @pytest.mark.unit
    def test_empty_staged_files_is_allowed(self, commit_repository: CommitRepository) -> None:
        """Should allow empty staged files list (edge case)."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    # Return empty list (no staged files)
                    return MagicMock(stdout="", returncode=0)
                elif "rev-parse" in cmd:
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="test",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            assert result is not None
            assert result.commit_type == "docs"

    @pytest.mark.unit
    def test_case_insensitive_extension_handling(self, commit_repository: CommitRepository) -> None:
        """Should handle file extensions case-insensitively."""
        from jiro.core.commit import create_docs_commit

        with (
            patch("jiro.core.commit.subprocess.run") as mock_run,
            patch("jiro.core.commit.load_template") as mock_load_template,
        ):
            # Mock git operations
            def run_side_effect(cmd, **kwargs):
                if "--name-only" in cmd:
                    return MagicMock(
                        stdout="README.MD\nDOCS/GUIDE.TXT\nfile.RST\n",
                        returncode=0,
                    )
                elif "rev-parse" in cmd:
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(stdout="", returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock template
            mock_template = MagicMock()
            mock_template.render.return_value = "📝 docs(task-1): Add docs"
            mock_load_template.return_value = mock_template

            result = create_docs_commit(
                task_id="task-1",
                task_type="docs",
                reason="Add documentation",
                verification_command="test",
                verification_results="OK",
                time_taken_seconds=60,
                context_tokens_before=1000,
                context_tokens_after=1100,
                repository=commit_repository,
            )

            # Should not raise ValidationError
            assert result is not None

    @pytest.mark.unit
    def test_rejects_mixed_valid_and_invalid_files(
        self, commit_repository: CommitRepository
    ) -> None:
        """Should reject if any non-doc files are present alongside doc files."""
        from jiro.core.commit import ValidationError, create_docs_commit

        with patch("jiro.core.commit.subprocess.run") as mock_run:
            # Mix of valid and invalid files
            mock_run.return_value = MagicMock(
                stdout="README.md\nsrc/main.py\nDOCS/guide.txt\n",
                returncode=0,
            )

            with pytest.raises(ValidationError) as exc_info:
                create_docs_commit(
                    task_id="task-1",
                    task_type="docs",
                    reason="Add documentation",
                    verification_command="test",
                    verification_results="OK",
                    time_taken_seconds=60,
                    context_tokens_before=1000,
                    context_tokens_after=1100,
                    repository=commit_repository,
                )

            assert "non-documentation files" in str(exc_info.value)
            assert "main.py" in str(exc_info.value)
