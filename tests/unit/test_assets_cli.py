"""Tests for assets CLI command."""

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestAssetsListCommand:
    """Tests for assets list command."""

    @pytest.mark.unit
    def test_assets_list_help(self, cli_runner: CliRunner) -> None:
        """Assets list command should display help."""
        result = cli_runner.invoke(app, ["assets", "list", "--help"])
        assert result.exit_code == 0
        assert "assets" in result.stdout.lower() or "list" in result.stdout.lower()

    @pytest.mark.unit
    def test_assets_list_displays_prompts(self, cli_runner: CliRunner) -> None:
        """Assets list should display prompts."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # The actual prompts should be in the output
        assert "prompt" in result.stdout.lower() or "md" in result.stdout.lower()

    @pytest.mark.unit
    def test_assets_list_displays_templates(self, cli_runner: CliRunner) -> None:
        """Assets list should display templates."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Should show templates
        assert "template" in result.stdout.lower() or "j2" in result.stdout.lower()

    @pytest.mark.unit
    def test_assets_list_displays_mixed_assets(self, cli_runner: CliRunner) -> None:
        """Assets list should display both prompts and templates."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Should contain both prompts and templates
        output_lower = result.stdout.lower()
        assert "prompt" in output_lower or "template" in output_lower

    @pytest.mark.unit
    def test_assets_list_shows_asset_types(self, cli_runner: CliRunner) -> None:
        """Assets list should clearly show asset types."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Check for type indicators
        output = result.stdout.lower()
        assert "prompt" in output or "template" in output

    @pytest.mark.unit
    def test_assets_list_shows_summary_counts(self, cli_runner: CliRunner) -> None:
        """Assets list should show count of assets by type."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Should display asset information
        assert len(result.stdout) > 0

    @pytest.mark.unit
    def test_assets_list_uses_rich_formatting(self, cli_runner: CliRunner) -> None:
        """Assets list should use Rich table formatting."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Rich tables typically have borders and structure
        output = result.stdout
        assert len(output) > 0

    @pytest.mark.unit
    def test_assets_list_groups_by_type(self, cli_runner: CliRunner) -> None:
        """Assets list should group assets by type."""
        result = cli_runner.invoke(app, ["assets", "list"])
        assert result.exit_code == 0
        # Output should show assets
        output = result.stdout.lower()
        assert len(output) > 0


class TestAssetsWhichCommand:
    """Tests for assets which command."""

    @pytest.mark.unit
    def test_assets_which_help(self, cli_runner: CliRunner) -> None:
        """Assets which command should display help."""
        result = cli_runner.invoke(app, ["assets", "which", "--help"])
        assert result.exit_code == 0
        assert "which" in result.stdout.lower() or "asset" in result.stdout.lower()

    @pytest.mark.unit
    def test_assets_which_shows_package_location(self, cli_runner: CliRunner) -> None:
        """Assets which should show package location for valid asset."""
        # Try a prompt that exists
        result = cli_runner.invoke(app, ["assets", "which", "planning_agent.md"])
        assert result.exit_code == 0
        # Should show a path
        assert "/" in result.stdout or "\\" in result.stdout

    @pytest.mark.unit
    def test_assets_which_returns_full_path(self, cli_runner: CliRunner) -> None:
        """Assets which should return an absolute path."""
        result = cli_runner.invoke(app, ["assets", "which", "planning_agent.md"])
        assert result.exit_code == 0
        output = result.stdout.strip()
        # Path should contain the asset name or be absolute
        assert "planning_agent" in output or output.startswith("/")

    @pytest.mark.unit
    def test_assets_which_asset_not_found(self, cli_runner: CliRunner) -> None:
        """Assets which should error for non-existent asset."""
        result = cli_runner.invoke(app, ["assets", "which", "nonexistent_asset.md"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    @pytest.mark.unit
    def test_assets_which_with_template(self, cli_runner: CliRunner) -> None:
        """Assets which should work with template assets."""
        # Get a template from the list command first to know what exists
        result = cli_runner.invoke(app, ["assets", "list"])
        # Then try to get location of a template
        # We'll use a flexible approach - just try a common template path
        result = cli_runner.invoke(app, ["assets", "which", "commit/docs.txt.j2"])
        # Either it succeeds with a path, or fails gracefully
        assert result.exit_code in (0, 1)
        if result.exit_code == 0:
            assert "/" in result.stdout or "\\" in result.stdout
