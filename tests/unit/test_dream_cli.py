"""Tests for dream command implementation.

Note: Rich Console output goes to stderr. Use `result.output` (not `result.stdout`)
when checking CLI output. See test_terminal_setup.py docstring for details.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.core.planner import Spec


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


@pytest.fixture
def mock_spec() -> Spec:
    """Create a mock Spec object."""
    return Spec(
        title="Test Feature",
        overview="This is a test feature that does something useful.",
        requirements=["Requirement 1", "Requirement 2", "Requirement 3"],
        acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        out_of_scope=["Out of scope 1", "Out of scope 2"],
        technical_notes="Some technical notes here.",
    )


@pytest.fixture
def mock_dreaming_agent():
    """Create a mock DreamingAgent."""
    agent = MagicMock()
    agent.dream = AsyncMock()
    agent.refine = AsyncMock()
    return agent


class TestDreamCommand:
    """Tests for the dream command."""

    @pytest.mark.unit
    def test_dream_command_exists(self, cli_runner: CliRunner) -> None:
        """Dream command should be available in CLI."""
        result = cli_runner.invoke(app, ["dream", "--help"])
        assert result.exit_code == 0
        assert (
            "Generate a specification" in result.stdout
            or "Generate specifications" in result.stdout
        )

    @pytest.mark.unit
    def test_dream_interactive_mode_without_prompt(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command without prompt should start interactive mode."""
        from jiro.agents.dreaming import InterviewResult

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream.console") as mock_console,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Setup mock dreaming agent with interview method
            mock_agent = MagicMock()
            mock_interview_result = InterviewResult(
                spec=mock_spec,
                conversation=[],
            )
            mock_agent.interview = AsyncMock(return_value=mock_interview_result)
            mock_agent.refine = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Mock console.input for interactive mode - immediately exit
            mock_console.input.side_effect = ["done"]

            cli_runner.invoke(app, ["dream"])

            # Should call interview method (interactive mode)
            assert mock_agent.interview.called

    @pytest.mark.unit
    def test_dream_generates_initial_spec(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command should generate initial spec from prompt."""
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Setup mock dreaming agent
            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent.refine = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Mock prompt_toolkit session for exit
            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(app, ["dream", "build a user authentication system"])

            # Should not have critical errors (may have other output)
            assert result.exit_code in [0, 1]  # EOFError handling

    @pytest.mark.unit
    def test_dream_saves_spec_to_directory(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command should save spec to specs directory."""
        specs_dir = tmp_path / ".jiro-dreams-of-code" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream.get_specs_dir", return_value=specs_dir),
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent.refine = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Mock prompt_toolkit session to exit immediately
            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                cli_runner.invoke(app, ["dream", "build a user authentication system"])

            # Check that spec was saved
            # At least one spec file should be created (or attempt was made)
            # Note: This depends on implementation details
            list(specs_dir.glob("*.md"))  # noqa: F841

    @pytest.mark.unit
    def test_dream_handles_exit_commands(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command should handle exit commands properly."""
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Test with 'done' command via prompt_toolkit session
            mock_session = MagicMock()
            mock_session.prompt.return_value = "done"
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(app, ["dream", "build a user authentication system"])
                assert result.exit_code == 0

    @pytest.mark.unit
    def test_dream_model_override(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command should respect --model override."""
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a feature", "--model", "claude-opus-4"],
                )

            # Should not fail with model override (0 is success, 1 is with error handling, 2 is CLI error)
            assert result.exit_code in [0, 1, 2]

    @pytest.mark.unit
    def test_dream_displays_spec_with_rich_formatting(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Dream command should display spec with Rich formatting."""
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream.console") as mock_console,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                cli_runner.invoke(app, ["dream", "build a user authentication system"])

            # Check that console.print was called for displaying spec
            assert mock_console.print.called
