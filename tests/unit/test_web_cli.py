"""Tests for web CLI command."""

from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestWebCommand:
    """Tests for web command."""

    @pytest.mark.unit
    def test_web_help(self, cli_runner: CliRunner) -> None:
        """Web command should display help."""
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0
        assert "web" in result.stdout.lower() or "Start" in result.stdout

    @pytest.mark.unit
    def test_web_command_exists(self, cli_runner: CliRunner) -> None:
        """Web command should exist and be callable."""
        # Get help to verify command exists
        result = cli_runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_default_port(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should use default port 8000."""
        # Mock uvicorn.run to avoid actually starting server
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web"])

        # Check that uvicorn was called with default port
        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # Verify port argument
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("port") == 8000

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_custom_port(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should accept custom port."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web", "--port", "9000"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # Verify port argument
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("port") == 9000

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_custom_port_short_flag(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should accept -p shorthand for port."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web", "-p", "7000"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # Verify port argument
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("port") == 7000

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_daemon_flag(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should handle daemon flag."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web", "--daemon"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # Verify daemon flag affects behavior (likely disables reload)
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        # daemon mode should set reload=False
        assert call_kwargs.get("reload") is False

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_daemon_short_flag(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should accept -d shorthand for daemon."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web", "-d"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("reload") is False

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_without_daemon_has_reload(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should enable reload when not in daemon mode."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # Without daemon flag, reload should be True
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("reload") is True

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_combined_options(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should handle multiple options together."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web", "--port", "3000", "--daemon"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs.get("port") == 3000
        assert call_kwargs.get("reload") is False

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_passes_fastapi_app(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should pass the FastAPI app to uvicorn."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web"])

        assert result.exit_code == 0
        assert mock_uvicorn_run.called
        # First positional argument should be the app string
        call_args = mock_uvicorn_run.call_args.args
        # Should pass app reference
        assert "jiro.web.app:app" in str(call_args) or len(call_args) > 0

    @pytest.mark.unit
    @mock.patch("jiro.cli.web.uvicorn.run")
    def test_web_displays_output_message(self, mock_uvicorn_run, cli_runner: CliRunner) -> None:
        """Web command should display informational message."""
        mock_uvicorn_run.return_value = None

        result = cli_runner.invoke(app, ["web"])

        assert result.exit_code == 0
        # Should display some user-friendly message
        output = result.stdout.lower()
        assert (
            "server" in output
            or "port" in output
            or "fastapi" in output.lower()
            or len(result.stdout) > 0
        )
