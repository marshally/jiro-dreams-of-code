"""Tests for completions CLI commands."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestCompletionsCommand:
    """Tests for completions command."""

    @pytest.mark.unit
    def test_completions_help(self, cli_runner: CliRunner) -> None:
        """Completions help should be available."""
        result = cli_runner.invoke(app, ["completions", "--help"])
        assert result.exit_code == 0
        assert "install" in result.stdout
        assert "show" in result.stdout

    @pytest.mark.unit
    def test_completions_without_subcommand(self, cli_runner: CliRunner) -> None:
        """Completions without subcommand should show usage info."""
        result = cli_runner.invoke(app, ["completions"])
        assert result.exit_code == 0
        assert "Shell Completions" in result.stdout
        assert "jiro completions install" in result.stdout
        assert "jiro completions show" in result.stdout


class TestCompletionsInstallCommand:
    """Tests for completions install command."""

    @pytest.mark.unit
    def test_completions_install_help(self, cli_runner: CliRunner) -> None:
        """Completions install help should be available."""
        result = cli_runner.invoke(app, ["completions", "install", "--help"])
        assert result.exit_code == 0
        assert "Install shell completions" in result.stdout
        assert "--shell" in result.stdout

    @pytest.mark.unit
    def test_completions_install_success(self, cli_runner: CliRunner) -> None:
        """Completions install should succeed with valid shell."""
        with patch("typer._completion_shared.install", return_value=("zsh", "/path/to/completion")):
            result = cli_runner.invoke(app, ["completions", "install", "--shell", "zsh"])
            assert result.exit_code == 0
            assert "Installed zsh completion" in result.stdout

    @pytest.mark.unit
    def test_completions_install_failure(self, cli_runner: CliRunner) -> None:
        """Completions install should handle errors."""
        with patch(
            "typer._completion_shared.install",
            side_effect=RuntimeError("Shell not detected"),
        ):
            result = cli_runner.invoke(app, ["completions", "install"])
            assert result.exit_code == 1
            assert "Error" in result.stdout


class TestCompletionsShowCommand:
    """Tests for completions show command."""

    @pytest.mark.unit
    def test_completions_show_help(self, cli_runner: CliRunner) -> None:
        """Completions show help should be available."""
        result = cli_runner.invoke(app, ["completions", "show", "--help"])
        assert result.exit_code == 0
        assert "Show the completion script" in result.stdout
        assert "--shell" in result.stdout

    @pytest.mark.unit
    def test_completions_show_zsh(self, cli_runner: CliRunner) -> None:
        """Completions show should output zsh script."""
        result = cli_runner.invoke(app, ["completions", "show", "--shell", "zsh"])
        assert result.exit_code == 0
        assert "#compdef jiro" in result.stdout
        assert "_jiro_completion" in result.stdout

    @pytest.mark.unit
    def test_completions_show_bash(self, cli_runner: CliRunner) -> None:
        """Completions show should output bash script."""
        result = cli_runner.invoke(app, ["completions", "show", "--shell", "bash"])
        assert result.exit_code == 0
        assert "_jiro_completion" in result.stdout
        assert "complete" in result.stdout


class TestNoDefaultCompletionOptions:
    """Test that default Typer completion options are disabled."""

    @pytest.mark.unit
    def test_no_install_completion_option(self, cli_runner: CliRunner) -> None:
        """--install-completion option should not exist."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--install-completion" not in result.stdout

    @pytest.mark.unit
    def test_no_show_completion_option(self, cli_runner: CliRunner) -> None:
        """--show-completion option should not exist."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--show-completion" not in result.stdout
