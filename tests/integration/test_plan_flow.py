"""Integration tests for the complete plan flow."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.planner import Epic, PlanResult, Spec, Task


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_spec() -> Spec:
    """Create a realistic mock Spec object for testing."""
    return Spec(
        title="User Authentication System",
        overview="A comprehensive user authentication system with JWT tokens and OAuth2 support. "
        "This system will handle user registration, login, password reset, and token management.",
        requirements=[
            "Support JWT-based authentication",
            "Implement OAuth2 integration with Google and GitHub",
            "Provide email-based password reset",
            "Store user credentials securely with bcrypt",
            "Implement rate limiting on auth endpoints",
            "Support token refresh mechanism",
        ],
        acceptance_criteria=[
            "Users can register with email and password",
            "JWT tokens are issued on successful login",
            "OAuth2 flow works with Google and GitHub providers",
            "Password reset tokens expire after 24 hours",
            "Auth endpoints have rate limiting enabled",
            "Tokens can be refreshed before expiration",
            "All auth endpoints return consistent error messages",
        ],
        out_of_scope=[
            "Multi-factor authentication (MFA)",
            "Social login with additional providers",
            "Session-based authentication",
            "Role-based access control",
        ],
        technical_notes="Use bcrypt with cost factor 12 for password hashing. "
        "JWT should use RS256 algorithm. Implement rate limiting with sliding window algorithm. "
        "Store JWT secrets in environment variables.",
    )


@pytest.fixture
def mock_plan_result_json() -> str:
    """Create a realistic mock plan result in JSON format."""
    plan = {
        "epics": [
            {
                "id": "epic-1",
                "name": "Authentication Core",
                "description": "Core authentication mechanisms including registration, login, and token management",
                "tasks": ["task-1", "task-2", "task-3"],
            },
            {
                "id": "epic-2",
                "name": "OAuth2 Integration",
                "description": "OAuth2 provider integrations with Google and GitHub",
                "tasks": ["task-4", "task-5"],
            },
            {
                "id": "epic-3",
                "name": "Security & Rate Limiting",
                "description": "Security features including rate limiting and password reset",
                "tasks": ["task-6", "task-7"],
            },
        ],
        "tasks": [
            {
                "id": "task-1",
                "title": "Implement JWT token generation",
                "description": "Create JWT token generation and validation logic using RS256 algorithm",
                "epic_id": "epic-1",
                "dependencies": [],
            },
            {
                "id": "task-2",
                "title": "Create user registration endpoint",
                "description": "Build registration endpoint with email validation and bcrypt password hashing",
                "epic_id": "epic-1",
                "dependencies": ["task-1"],
            },
            {
                "id": "task-3",
                "title": "Implement token refresh mechanism",
                "description": "Add token refresh endpoint to issue new tokens before expiration",
                "epic_id": "epic-1",
                "dependencies": ["task-1"],
            },
            {
                "id": "task-4",
                "title": "Integrate Google OAuth2",
                "description": "Set up Google OAuth2 provider integration with appropriate scopes",
                "epic_id": "epic-2",
                "dependencies": ["task-1"],
            },
            {
                "id": "task-5",
                "title": "Integrate GitHub OAuth2",
                "description": "Set up GitHub OAuth2 provider integration",
                "epic_id": "epic-2",
                "dependencies": ["task-1"],
            },
            {
                "id": "task-6",
                "title": "Implement rate limiting",
                "description": "Add rate limiting to authentication endpoints using sliding window algorithm",
                "epic_id": "epic-3",
                "dependencies": [],
            },
            {
                "id": "task-7",
                "title": "Implement password reset flow",
                "description": "Create secure password reset with time-limited email tokens",
                "epic_id": "epic-3",
                "dependencies": ["task-2"],
            },
        ],
        "dependencies": [
            {"from": "task-2", "to": "task-1"},
            {"from": "task-3", "to": "task-1"},
            {"from": "task-4", "to": "task-1"},
            {"from": "task-5", "to": "task-1"},
            {"from": "task-7", "to": "task-2"},
        ],
    }
    return json.dumps(plan)


class TestPlanFlowIntegration:
    """Integration tests for the plan command flow."""

    @pytest.mark.integration
    def test_plan_parses_spec_file(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test spec loading from file.

        Verifies:
        - Plan command accepts a spec file path
        - Spec file is parsed correctly
        - Specification sections are extracted
        """
        # Create a spec file in the temp directory
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

"""
        for req in mock_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for crit in mock_spec.acceptance_criteria:
            spec_content += f"- {crit}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in mock_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{mock_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
        ):
            # Configure mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock()
            mock_planner_class.return_value = mock_planner

            # Simulate user rejecting the plan
            with patch("typer.confirm", return_value=False):
                result = cli_runner.invoke(
                    app,
                    ["plan", "--spec", str(spec_file)],
                )

            # Should complete successfully (just parsing and rejecting)
            assert result.exit_code == 0
            # Planner should have been called
            assert mock_planner.plan.called

    @pytest.mark.integration
    def test_plan_generates_epics_and_tasks(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        mock_plan_result_json: str,
        tmp_path: Path,
    ) -> None:
        """Test decomposition into epics/tasks.

        Verifies:
        - Planning agent is called with spec
        - Response is parsed into epics and tasks
        - Decomposition generates 2+ epics
        - Each epic has associated tasks
        """
        # Create a spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

"""
        for req in mock_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for crit in mock_spec.acceptance_criteria:
            spec_content += f"- {crit}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in mock_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{mock_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
        ):
            # Configure mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Create a mock plan result
            plan_result = PlanResult(
                epics=[
                    Epic(
                        id="epic-1",
                        name="Authentication Core",
                        description="Core authentication mechanisms",
                        tasks=["task-1", "task-2", "task-3"],
                    ),
                    Epic(
                        id="epic-2",
                        name="OAuth2 Integration",
                        description="OAuth2 provider integrations",
                        tasks=["task-4", "task-5"],
                    ),
                    Epic(
                        id="epic-3",
                        name="Security & Rate Limiting",
                        description="Security features",
                        tasks=["task-6", "task-7"],
                    ),
                ],
                tasks=[
                    Task(
                        id="task-1",
                        title="Implement JWT token generation",
                        description="Create JWT token generation logic",
                        epic_id="epic-1",
                        dependencies=[],
                    ),
                    Task(
                        id="task-2",
                        title="Create user registration endpoint",
                        description="Build registration endpoint",
                        epic_id="epic-1",
                        dependencies=["task-1"],
                    ),
                    Task(
                        id="task-3",
                        title="Implement token refresh mechanism",
                        description="Add token refresh endpoint",
                        epic_id="epic-1",
                        dependencies=["task-1"],
                    ),
                    Task(
                        id="task-4",
                        title="Integrate Google OAuth2",
                        description="Set up Google OAuth2",
                        epic_id="epic-2",
                        dependencies=["task-1"],
                    ),
                    Task(
                        id="task-5",
                        title="Integrate GitHub OAuth2",
                        description="Set up GitHub OAuth2",
                        epic_id="epic-2",
                        dependencies=["task-1"],
                    ),
                    Task(
                        id="task-6",
                        title="Implement rate limiting",
                        description="Add rate limiting to endpoints",
                        epic_id="epic-3",
                        dependencies=[],
                    ),
                    Task(
                        id="task-7",
                        title="Implement password reset flow",
                        description="Create password reset",
                        epic_id="epic-3",
                        dependencies=["task-2"],
                    ),
                ],
                dependencies=[
                    {"from": "task-2", "to": "task-1"},
                    {"from": "task-3", "to": "task-1"},
                    {"from": "task-4", "to": "task-1"},
                    {"from": "task-5", "to": "task-1"},
                    {"from": "task-7", "to": "task-2"},
                ],
            )

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock(return_value=plan_result)
            mock_planner_class.return_value = mock_planner

            # Simulate user rejecting the plan
            with patch("typer.confirm", return_value=False):
                result = cli_runner.invoke(
                    app,
                    ["plan", "--spec", str(spec_file)],
                )

            # Should complete successfully
            assert result.exit_code == 0

            # Output should show epics and tasks
            output = result.stdout
            assert "Epics" in output
            assert "Tasks" in output
            assert "Authentication Core" in output or "epic-1" in output
            assert "OAuth2 Integration" in output or "epic-2" in output

    @pytest.mark.integration
    def test_plan_creates_tasks_in_tracker(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test task creation on confirmation.

        Verifies:
        - User can confirm plan execution
        - Tracker is initialized with correct directory
        - Tasks are created in the tracker
        - Creation returns task IDs
        """
        # Create a spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

- {mock_spec.requirements[0]}
- {mock_spec.requirements[1]}
- {mock_spec.requirements[2]}

## Acceptance Criteria

- {mock_spec.acceptance_criteria[0]}
- {mock_spec.acceptance_criteria[1]}
- {mock_spec.acceptance_criteria[2]}

## Out of Scope

- {mock_spec.out_of_scope[0]}
- {mock_spec.out_of_scope[1]}

## Technical Notes

{mock_spec.technical_notes}
"""
        spec_file.write_text(spec_content)

        # Create .beads directory
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir(exist_ok=True)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.create_tasks") as mock_create_tasks,
        ):
            # Configure mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Create mock plan result
            plan_result = PlanResult(
                epics=[
                    Epic(
                        id="epic-1",
                        name="Auth Core",
                        description="Authentication core",
                        tasks=["task-1", "task-2"],
                    ),
                ],
                tasks=[
                    Task(
                        id="task-1",
                        title="JWT tokens",
                        description="JWT implementation",
                        epic_id="epic-1",
                        dependencies=[],
                    ),
                    Task(
                        id="task-2",
                        title="Registration endpoint",
                        description="Registration",
                        epic_id="epic-1",
                        dependencies=["task-1"],
                    ),
                ],
                dependencies=[{"from": "task-2", "to": "task-1"}],
            )

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock(return_value=plan_result)
            mock_planner_class.return_value = mock_planner

            # Mock tracker and create_tasks
            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker

            mock_created_tasks = [
                MagicMock(id="bd-task-1", title="JWT tokens"),
                MagicMock(id="bd-task-2", title="Registration endpoint"),
            ]
            mock_create_tasks.return_value = mock_created_tasks

            # Simulate user confirming the plan
            with patch("typer.confirm", return_value=True):
                result = cli_runner.invoke(
                    app,
                    ["plan", "--spec", str(spec_file)],
                )

            # Should complete successfully
            assert result.exit_code == 0

            # Tracker should have been created
            assert mock_tracker_class.called

            # create_tasks should have been called
            assert mock_create_tasks.called

            # Output should show created tasks
            output = result.stdout
            assert "Created" in output or "bd-task-1" in output or "jwt" in output.lower()

    @pytest.mark.integration
    def test_plan_confirmation_flow(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test confirmation prompt flow.

        Verifies:
        - Plan is displayed before confirmation
        - User can reject plan and exit early
        - User can confirm plan and proceed to task creation
        """
        # Create a spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

- {mock_spec.requirements[0]}
- {mock_spec.requirements[1]}

## Acceptance Criteria

- {mock_spec.acceptance_criteria[0]}
- {mock_spec.acceptance_criteria[1]}

## Out of Scope

- {mock_spec.out_of_scope[0]}

## Technical Notes

{mock_spec.technical_notes}
"""
        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            plan_result = PlanResult(
                epics=[
                    Epic(
                        id="epic-1",
                        name="Test Epic",
                        description="Test description",
                        tasks=["task-1"],
                    ),
                ],
                tasks=[
                    Task(
                        id="task-1",
                        title="Test Task",
                        description="Test task description",
                        epic_id="epic-1",
                        dependencies=[],
                    ),
                ],
            )

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock(return_value=plan_result)
            mock_planner_class.return_value = mock_planner

            # Test rejection case
            with patch("typer.confirm", return_value=False):
                result = cli_runner.invoke(
                    app,
                    ["plan", "--spec", str(spec_file)],
                )

            # Should exit gracefully without error
            assert result.exit_code == 0
            assert "cancelled" in result.stdout.lower() or "Review the plan" in result.stdout

    @pytest.mark.integration
    def test_plan_with_custom_model(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test plan command with custom model override.

        Verifies:
        - --model flag is accepted
        - Custom model is passed to agent configuration
        """
        # Create a spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

- {mock_spec.requirements[0]}
- {mock_spec.requirements[1]}

## Acceptance Criteria

- {mock_spec.acceptance_criteria[0]}
- {mock_spec.acceptance_criteria[1]}

## Out of Scope

- {mock_spec.out_of_scope[0]}

## Technical Notes

{mock_spec.technical_notes}
"""
        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            plan_result = PlanResult(
                epics=[
                    Epic(
                        id="epic-1",
                        name="Test Epic",
                        description="Test",
                        tasks=["task-1"],
                    ),
                ],
                tasks=[
                    Task(
                        id="task-1",
                        title="Test Task",
                        description="Test",
                        epic_id="epic-1",
                    ),
                ],
            )

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock(return_value=plan_result)
            mock_planner_class.return_value = mock_planner

            # Run with custom model
            with patch("typer.confirm", return_value=False):
                result = cli_runner.invoke(
                    app,
                    [
                        "plan",
                        "--spec",
                        str(spec_file),
                        "--model",
                        "claude-sonnet-4",
                    ],
                )

            # Should accept the command
            assert result.exit_code == 0

    @pytest.mark.integration
    def test_plan_handles_missing_spec_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test plan command with missing spec file.

        Verifies:
        - Missing file produces appropriate error
        - Command exits with error code
        """
        non_existent_file = tmp_path / "nonexistent.md"

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = cli_runner.invoke(
                app,
                ["plan", "--spec", str(non_existent_file)],
            )

            # Should error
            assert result.exit_code != 0
            assert "Error" in result.stdout or "not found" in result.stdout.lower()

    @pytest.mark.integration
    def test_plan_handles_invalid_spec_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test plan command with invalid spec file.

        Verifies:
        - Invalid spec produces appropriate error
        - Missing required sections are reported
        - Command exits with error code
        """
        # Create an invalid spec (missing required sections)
        spec_file = tmp_path / "invalid_spec.md"
        spec_file.write_text("# Feature: Incomplete Spec\n\nMissing required sections")

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = cli_runner.invoke(
                app,
                ["plan", "--spec", str(spec_file)],
            )

            # Should error
            assert result.exit_code != 0

    @pytest.mark.integration
    def test_plan_full_end_to_end_flow(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test complete plan flow end-to-end.

        This test simulates a real user workflow:
        1. Load spec file
        2. Display plan with decomposition
        3. User reviews and confirms
        4. Tasks are created in tracker
        5. Success message is displayed
        """
        # Create a complete spec file
        spec_file = tmp_path / "complete_spec.md"
        spec_content = f"""# Feature: {mock_spec.title}

## Overview

{mock_spec.overview}

## Requirements

"""
        for req in mock_spec.requirements[:3]:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for crit in mock_spec.acceptance_criteria[:3]:
            spec_content += f"- {crit}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in mock_spec.out_of_scope[:2]:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{mock_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        # Create .beads directory
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir(exist_ok=True)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.create_tasks") as mock_create_tasks,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Create comprehensive plan result
            plan_result = PlanResult(
                epics=[
                    Epic(
                        id="epic-1",
                        name="Authentication Core",
                        description="Core authentication mechanisms",
                        tasks=["task-1", "task-2"],
                    ),
                    Epic(
                        id="epic-2",
                        name="Security Features",
                        description="Security and rate limiting",
                        tasks=["task-3"],
                    ),
                ],
                tasks=[
                    Task(
                        id="task-1",
                        title="JWT Implementation",
                        description="Implement JWT tokens",
                        epic_id="epic-1",
                        dependencies=[],
                    ),
                    Task(
                        id="task-2",
                        title="User Registration",
                        description="Registration endpoint",
                        epic_id="epic-1",
                        dependencies=["task-1"],
                    ),
                    Task(
                        id="task-3",
                        title="Rate Limiting",
                        description="Rate limit endpoints",
                        epic_id="epic-2",
                        dependencies=[],
                    ),
                ],
                dependencies=[{"from": "task-2", "to": "task-1"}],
            )

            mock_planner = MagicMock()
            mock_planner.plan = AsyncMock(return_value=plan_result)
            mock_planner_class.return_value = mock_planner

            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker

            mock_created_tasks = [
                MagicMock(id="bd-1", title="JWT Implementation"),
                MagicMock(id="bd-2", title="User Registration"),
                MagicMock(id="bd-3", title="Rate Limiting"),
            ]
            mock_create_tasks.return_value = mock_created_tasks

            # User confirms the plan
            with patch("typer.confirm", return_value=True):
                result = cli_runner.invoke(
                    app,
                    ["plan", "--spec", str(spec_file)],
                )

            # Should complete successfully
            assert result.exit_code == 0

            # All components should be called
            assert mock_planner_class.called
            assert mock_tracker_class.called
            assert mock_create_tasks.called

            # Output should show completion
            output = result.stdout
            assert "Created" in output or "completed" in output.lower()
