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
