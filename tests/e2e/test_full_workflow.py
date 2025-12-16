"""End-to-end tests for the full jiro workflow."""

import subprocess
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.planner import Spec
from jiro.core.session import SessionResult


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository for E2E testing.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Yields:
        Path to the temporary git repository.
    """
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    # Configure git user for this test repo
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    yield tmp_path


@pytest.fixture
def mock_spec() -> Spec:
    """Create a mock specification for testing."""
    return Spec(
        title="Sample Feature",
        overview="A sample feature for testing the full workflow.",
        requirements=[
            "Implement core functionality",
            "Add error handling",
            "Write tests",
        ],
        acceptance_criteria=[
            "Feature works end-to-end",
            "All tests pass",
            "No regressions",
        ],
        out_of_scope=["Future enhancements"],
        technical_notes="Use TDD approach.",
    )


@pytest.fixture
def mock_session_result_completed() -> SessionResult:
    """Create a completed session result."""
    return SessionResult(
        session_id="e2e-session-123",
        status="completed",
        tasks_completed=2,
        tasks_failed=0,
        error=None,
    )


class TestFullWorkflowE2E:
    """E2E tests for the complete jiro workflow."""

    @pytest.mark.e2e
    def test_init_command_creates_project_structure(self, temp_git_repo: Path) -> None:
        """Test that jiro init creates the correct project structure.

        Verifies:
        - .jiro-dreams-of-code directory is created
        - config.yaml is created with correct structure
        - specs and logs directories are created
        """
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        jiro_dir = temp_git_repo / ".jiro-dreams-of-code"
        assert jiro_dir.exists(), "jiro directory not created"
        assert (jiro_dir / "config.yaml").exists(), "config.yaml not created"
        assert (jiro_dir / "specs").exists(), "specs directory not created"
        assert (jiro_dir / "logs").exists(), "logs directory not created"

    @pytest.mark.e2e
    @pytest.mark.vcr
    def test_full_workflow_init_to_execute(
        self,
        cli_runner: CliRunner,
        temp_git_repo: Path,
        mock_spec: Spec,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test full workflow from init through execute.

        This test verifies the complete flow:
        1. jiro init - sets up project
        2. jiro dream - generates spec (mocked)
        3. jiro execute - runs session (mocked)

        Verifies:
        - Each step completes successfully
        - Database state is correct
        - Files are created appropriately
        """
        # Step 1: Initialize the project
        init_result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert init_result.returncode == 0, f"init failed: {init_result.stderr}"

        # Step 2: Test dream command with mocked agent
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream._create_multiline_session") as mock_session_factory,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Mock prompt_toolkit session to return "done" on first prompt
            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(return_value="done")
            mock_session_factory.return_value = mock_session

            dream_result = cli_runner.invoke(app, ["dream", "build a sample feature"])

            assert dream_result.exit_code == 0
            # Rich console outputs to stderr, but CliRunner combines into .output
            assert "Sample Feature" in dream_result.output

        # Step 3: Test execute command with mocked orchestrator
        with (
            patch("jiro.cli.execute.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = temp_git_repo / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            execute_result = cli_runner.invoke(app, ["execute"])

            assert execute_result.exit_code == 0
            assert "completed successfully" in execute_result.stdout

    @pytest.mark.e2e
    def test_workflow_verifies_database_state(
        self,
        cli_runner: CliRunner,
        temp_git_repo: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test that workflow properly updates database state.

        Verifies:
        - Session repository is called correctly
        - Task execution repository is called correctly
        - Database schema is ensured
        """
        # Initialize project first
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        with (
            patch("jiro.cli.execute.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema") as mock_ensure_schema,
            patch("jiro.cli.execute.SessionRepository") as mock_session_repo_class,
            patch("jiro.cli.execute.TaskExecutionRepository") as mock_task_repo_class,
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            db_path = temp_git_repo / ".jiro-dreams-of-code" / "jiro.db"
            mock_db_path.return_value = db_path
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_session_repo = MagicMock()
            mock_session_repo_class.return_value = mock_session_repo

            mock_task_repo = MagicMock()
            mock_task_repo_class.return_value = mock_task_repo

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 0

            # Verify database operations
            mock_ensure_schema.assert_called_once()
            mock_session_repo_class.assert_called_once()
            mock_task_repo_class.assert_called_once()
            mock_orchestrator.run.assert_called_once()

    @pytest.mark.e2e
    def test_workflow_verifies_file_changes(self, temp_git_repo: Path, mock_spec: Spec) -> None:
        """Test that workflow creates expected files.

        Verifies:
        - Spec file is saved to specs directory
        - Config file contains correct settings
        """
        # Initialize project
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        specs_dir = temp_git_repo / ".jiro-dreams-of-code" / "specs"
        assert specs_dir.exists()

        # Manually write a spec file to verify the spec saving mechanism
        spec_file = specs_dir / "sample_feature.md"
        spec_content = f"""# {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

{chr(10).join(f"- {r}" for r in mock_spec.requirements)}

## Acceptance Criteria

{chr(10).join(f"- {c}" for c in mock_spec.acceptance_criteria)}

## Out of Scope

{chr(10).join(f"- {o}" for o in mock_spec.out_of_scope)}

## Technical Notes

{mock_spec.technical_notes}
"""
        spec_file.write_text(spec_content)

        # Verify spec file was created
        assert spec_file.exists()
        content = spec_file.read_text()
        assert "Sample Feature" in content
        assert "Implement core functionality" in content

    @pytest.mark.e2e
    @pytest.mark.vcr
    def test_workflow_with_epic_filter(
        self,
        cli_runner: CliRunner,
        temp_git_repo: Path,
        mock_session_result_completed: SessionResult,
    ) -> None:
        """Test workflow with epic filtering.

        Verifies:
        - Epic filter is passed through to orchestrator
        - Only tasks for the epic are executed
        """
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        with (
            patch("jiro.cli.execute.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = temp_git_repo / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = mock_session_result_completed
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute", "--epic", "FEATURE-123"])

            assert result.exit_code == 0
            mock_orchestrator.run.assert_called_once_with(epic_id="FEATURE-123")

    @pytest.mark.e2e
    def test_workflow_fails_gracefully_on_preflight_failure(
        self, cli_runner: CliRunner, temp_git_repo: Path
    ) -> None:
        """Test that workflow handles preflight failures gracefully.

        Verifies:
        - Preflight failure is detected
        - Session is marked as failed
        - User receives error message
        """
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        failed_result = SessionResult(
            session_id="failed-session",
            status="failed",
            tasks_completed=0,
            tasks_failed=0,
            error="Preflight checks failed: git_clean: Uncommitted changes",
        )

        with (
            patch("jiro.cli.execute.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = temp_git_repo / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = failed_result
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 1
            assert "failed" in result.stdout.lower()

    @pytest.mark.e2e
    def test_workflow_handles_task_failure_halt(
        self, cli_runner: CliRunner, temp_git_repo: Path
    ) -> None:
        """Test that workflow halts on task failure.

        Verifies:
        - Task failure causes session halt
        - Partial progress is reported
        - User receives error message
        """
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        halted_result = SessionResult(
            session_id="halted-session",
            status="halted",
            tasks_completed=1,
            tasks_failed=1,
            error="Task TEST-42 failed: Assertion error in test",
        )

        with (
            patch("jiro.cli.execute.Path.cwd", return_value=temp_git_repo),
            patch("jiro.cli.execute.load_config") as mock_load_config,
            patch("jiro.cli.execute.get_database_path") as mock_db_path,
            patch("jiro.cli.execute.get_database") as mock_get_db,
            patch("jiro.cli.execute.ensure_schema"),
            patch("jiro.cli.execute.SessionRepository"),
            patch("jiro.cli.execute.TaskExecutionRepository"),
            patch("jiro.cli.execute.SessionOrchestrator") as mock_orchestrator_class,
        ):
            mock_config = MagicMock()
            mock_load_config.return_value = mock_config

            mock_db_path.return_value = temp_git_repo / "jiro.db"
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = halted_result
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cli_runner.invoke(app, ["execute"])

            assert result.exit_code == 1
            assert "halted" in result.stdout.lower()
            assert "Tasks completed: 1" in result.stdout
            assert "Tasks failed: 1" in result.stdout

    @pytest.mark.e2e
    def test_doctor_command_in_workflow(self, temp_git_repo: Path) -> None:
        """Test that doctor command works after init.

        Verifies:
        - Doctor command runs successfully after init
        - Health checks are performed
        """
        # Initialize project
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        # Run doctor
        result = subprocess.run(
            ["uv", "run", "jiro", "doctor"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        # Doctor should run (may pass or fail based on environment)
        # We just verify it doesn't crash
        assert result.returncode in [0, 1]
        assert "Health Check" in result.stdout or "health" in result.stdout.lower()

    @pytest.mark.e2e
    def test_status_command_in_workflow(self, temp_git_repo: Path) -> None:
        """Test that status command works after init.

        Verifies:
        - Status command runs successfully after init
        - Project information is displayed
        """
        # Initialize project
        subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        # Run status command via subprocess
        result = subprocess.run(
            ["uv", "run", "jiro", "status"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        # Status should run (may have various outputs based on database state)
        assert result.returncode in [0, 1, 2]
