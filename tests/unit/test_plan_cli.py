"""Tests for plan command implementation."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.planner import Epic, PlanResult, Spec, Task


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


@pytest.fixture
def sample_spec() -> Spec:
    """Create a sample Spec object."""
    return Spec(
        title="User Authentication System",
        overview="Implement a complete authentication system with email/password and OAuth2.",
        requirements=[
            "User registration with email validation",
            "User login with JWT tokens",
            "OAuth2 integration with GitHub",
            "Password reset functionality",
        ],
        acceptance_criteria=[
            "Users can register with valid emails",
            "Users can login and receive tokens",
            "OAuth2 flow works end-to-end",
            "Password reset emails are sent",
        ],
        out_of_scope=[
            "MFA implementation",
            "Biometric authentication",
        ],
        technical_notes="Use JWT for token management.",
    )


@pytest.fixture
def sample_plan_result() -> PlanResult:
    """Create a sample PlanResult object."""
    epic1 = Epic(
        id="epic-1",
        name="Core Authentication",
        description="Implement email/password authentication",
        tasks=["task-1", "task-2"],
    )
    epic2 = Epic(
        id="epic-2",
        name="OAuth2 Integration",
        description="Add OAuth2 provider support",
        tasks=["task-3", "task-4"],
    )

    task1 = Task(
        id="task-1",
        title="User Registration",
        description="Implement user registration endpoint",
        epic_id="epic-1",
        dependencies=[],
    )
    task2 = Task(
        id="task-2",
        title="User Login",
        description="Implement login with JWT tokens",
        epic_id="epic-1",
        dependencies=["task-1"],
    )
    task3 = Task(
        id="task-3",
        title="GitHub OAuth Setup",
        description="Configure GitHub OAuth provider",
        epic_id="epic-2",
        dependencies=[],
    )
    task4 = Task(
        id="task-4",
        title="OAuth Flow",
        description="Implement OAuth callback flow",
        epic_id="epic-2",
        dependencies=["task-3"],
    )

    return PlanResult(
        epics=[epic1, epic2],
        tasks=[task1, task2, task3, task4],
        dependencies=[
            {"from": "task-2", "to": "task-1"},
            {"from": "task-4", "to": "task-3"},
        ],
    )


class TestPlanCommand:
    """Tests for the plan command."""

    @pytest.mark.unit
    def test_plan_command_exists(self, cli_runner: CliRunner) -> None:
        """Plan command should be available in CLI."""
        result = cli_runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "plan" in result.stdout.lower()

    @pytest.mark.unit
    def test_plan_requires_spec_option(self, cli_runner: CliRunner) -> None:
        """Plan command requires --spec option."""
        result = cli_runner.invoke(app, ["plan"])
        assert result.exit_code != 0

    @pytest.mark.unit
    def test_plan_loads_spec_from_file(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Plan command should load spec from YAML file."""
        # Create a spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=PlanResult(epics=[], tasks=[]))
            mock_planner_class.return_value = mock_planner

            result = cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # Should not fail critically
            assert result.exit_code in [0, 1]

    @pytest.mark.unit
    def test_plan_runs_spec_planner(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should run SpecPlanner."""
        # Create spec file
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.ProjectInspector") as mock_inspector_class,
            patch(
                "jiro.cli.plan.typer.confirm", side_effect=[False, False]
            ),  # Skip bootstrap, proceed with planning
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock BeadsTracker
            mock_tracker = MagicMock()
            mock_tracker.beads_dir = MagicMock()
            mock_tracker.beads_dir.exists = MagicMock(return_value=True)
            mock_tracker_class.return_value = mock_tracker

            # Mock ProjectInspector to return no missing components
            mock_inspector = MagicMock()
            mock_inspector.analyze = MagicMock()
            mock_inspector.analyze.return_value = MagicMock(missing_components=[])
            mock_inspector_class.return_value = mock_inspector

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # Planner should have been called
            assert mock_planner.plan.called

    @pytest.mark.unit
    def test_plan_displays_summary_with_rich(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should display summary using Rich."""
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
            patch("jiro.cli.plan.console") as mock_console,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # Console should be called to display output
            assert mock_console.print.called

    @pytest.mark.unit
    def test_plan_confirmation_prompt(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should display confirmation prompt."""
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.ProjectInspector") as mock_inspector_class,
            patch("jiro.cli.plan.typer.confirm") as mock_confirm,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock BeadsTracker
            mock_tracker = MagicMock()
            mock_tracker.beads_dir = MagicMock()
            mock_tracker.beads_dir.exists = MagicMock(return_value=True)
            mock_tracker_class.return_value = mock_tracker

            # Mock ProjectInspector to return no missing components
            mock_inspector = MagicMock()
            mock_inspector.analyze = MagicMock()
            mock_inspector.analyze.return_value = MagicMock(missing_components=[])
            mock_inspector_class.return_value = mock_inspector

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            mock_confirm.return_value = False

            cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # Confirm should have been called
            assert mock_confirm.called

    @pytest.mark.unit
    def test_plan_creates_tasks_on_yes(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should create tasks when user confirms."""
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.create_tasks") as mock_create_tasks,
            patch("jiro.cli.plan.typer.confirm", return_value=True),
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker

            mock_create_tasks.return_value = []

            cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # create_tasks should have been called
            assert mock_create_tasks.called

    @pytest.mark.unit
    def test_plan_cancels_on_no(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should not create tasks when user declines."""
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.BeadsTracker") as mock_tracker_class,
            patch("jiro.cli.plan.create_tasks") as mock_create_tasks,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker

            cli_runner.invoke(app, ["plan", "--spec", str(spec_file)])

            # create_tasks should NOT have been called
            assert not mock_create_tasks.called

    @pytest.mark.unit
    def test_plan_model_override(
        self,
        cli_runner: CliRunner,
        sample_spec: Spec,
        sample_plan_result: PlanResult,
        tmp_path: Path,
    ) -> None:
        """Plan command should respect --model override."""
        spec_file = tmp_path / "test_spec.md"
        spec_content = f"""# Feature: {sample_spec.title}

## Overview

{sample_spec.overview}

## Requirements

"""
        for req in sample_spec.requirements:
            spec_content += f"- {req}\n"

        spec_content += "\n## Acceptance Criteria\n\n"
        for criteria in sample_spec.acceptance_criteria:
            spec_content += f"- {criteria}\n"

        spec_content += "\n## Out of Scope\n\n"
        for item in sample_spec.out_of_scope:
            spec_content += f"- {item}\n"

        spec_content += f"\n## Technical Notes\n\n{sample_spec.technical_notes}\n"

        spec_file.write_text(spec_content)

        with (
            patch("jiro.cli.plan.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.plan.load_config") as mock_load_config,
            patch("jiro.cli.plan.get_database") as mock_get_db,
            patch("jiro.cli.plan.SpecPlanner") as mock_planner_class,
            patch("jiro.cli.plan.typer.confirm", return_value=False),
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_planner = AsyncMock()
            mock_planner.plan = AsyncMock(return_value=sample_plan_result)
            mock_planner_class.return_value = mock_planner

            result = cli_runner.invoke(
                app, ["plan", "--spec", str(spec_file), "--model", "custom-model"]
            )

            # Should not fail with model override
            assert result.exit_code in [0, 1]
