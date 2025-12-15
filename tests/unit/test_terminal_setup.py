"""Tests for terminal setup command."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.cli.terminal_setup import detect_terminal


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestDetectTerminal:
    """Tests for terminal detection."""

    @pytest.mark.unit
    def test_detect_vscode_terminal(self) -> None:
        """Should detect VS Code terminal."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "vscode", "TERM": "xterm-256color"}):
            assert detect_terminal() == "vscode"

    @pytest.mark.unit
    def test_detect_iterm2_terminal(self) -> None:
        """Should detect iTerm2 terminal."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "iTerm.app", "TERM": "xterm-256color"}):
            assert detect_terminal() == "iterm2"

    @pytest.mark.unit
    def test_detect_ghostty_terminal(self) -> None:
        """Should detect Ghostty terminal."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "ghostty", "TERM": "xterm-ghostty"}):
            assert detect_terminal() == "ghostty"

    @pytest.mark.unit
    def test_detect_wezterm_terminal(self) -> None:
        """Should detect WezTerm terminal."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm", "TERM": "wezterm"}):
            assert detect_terminal() == "wezterm"

    @pytest.mark.unit
    def test_detect_kitty_terminal(self) -> None:
        """Should detect Kitty terminal."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "", "TERM": "xterm-kitty"}):
            assert detect_terminal() == "kitty"

    @pytest.mark.unit
    def test_detect_macos_terminal_app(self) -> None:
        """Should detect macOS Terminal.app."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "Apple_Terminal", "TERM": "xterm-256color"}):
            assert detect_terminal() == "terminal_app"

    @pytest.mark.unit
    def test_detect_unknown_terminal(self) -> None:
        """Should return 'unknown' for unrecognized terminals."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "SomeOther", "TERM": "xterm"}, clear=True):
            assert detect_terminal() == "unknown"

    @pytest.mark.unit
    def test_detect_missing_env_vars(self) -> None:
        """Should handle missing environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            assert detect_terminal() == "unknown"


class TestTerminalSetupCommand:
    """Tests for terminal-setup command."""

    @pytest.mark.unit
    def test_command_exists(self, cli_runner: CliRunner) -> None:
        """Terminal-setup command should be available."""
        result = cli_runner.invoke(app, ["terminal-setup", "--help"])
        assert result.exit_code == 0
        assert "Shift+Enter" in result.stdout or "multiline" in result.stdout.lower()

    @pytest.mark.unit
    def test_shows_vscode_instructions(self, cli_runner: CliRunner) -> None:
        """Should show VS Code instructions when detected."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "vscode"}):
            result = cli_runner.invoke(app, ["terminal-setup"])
            assert result.exit_code == 0
            # Output goes to stderr via Rich Console
            output = result.output
            assert "vscode" in output.lower()
            assert "keybindings.json" in output

    @pytest.mark.unit
    def test_shows_iterm2_instructions(self, cli_runner: CliRunner) -> None:
        """Should show iTerm2 instructions when detected."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "iTerm.app"}):
            result = cli_runner.invoke(app, ["terminal-setup"])
            assert result.exit_code == 0
            output = result.output
            assert "iterm2" in output.lower()
            assert "Preferences" in output or "Key Mappings" in output

    @pytest.mark.unit
    def test_shows_ghostty_instructions(self, cli_runner: CliRunner) -> None:
        """Should show Ghostty instructions when detected."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "ghostty"}):
            result = cli_runner.invoke(app, ["terminal-setup"])
            assert result.exit_code == 0
            output = result.output
            assert "ghostty" in output.lower()

    @pytest.mark.unit
    def test_shows_unknown_instructions(self, cli_runner: CliRunner) -> None:
        """Should show fallback instructions for unknown terminals."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "UnknownTerminal"}, clear=True):
            result = cli_runner.invoke(app, ["terminal-setup"])
            assert result.exit_code == 0
            output = result.output
            # Should mention the fallback behavior
            assert "Meta+Enter" in output or "Alt" in output or "Option" in output

    @pytest.mark.unit
    def test_detects_and_displays_terminal_name(self, cli_runner: CliRunner) -> None:
        """Should display the detected terminal name."""
        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
            result = cli_runner.invoke(app, ["terminal-setup"])
            assert result.exit_code == 0
            output = result.output
            assert "wezterm" in output.lower()
