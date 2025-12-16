"""Tests for auth CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestAuthLoginCommand:
    """Tests for auth login command."""

    @pytest.mark.unit
    def test_auth_login_help(self, cli_runner: CliRunner) -> None:
        """Auth login help should be available."""
        result = cli_runner.invoke(app, ["auth", "login", "--help"])
        assert result.exit_code == 0
        assert "Store API key in system keyring" in result.stdout

    @pytest.mark.unit
    def test_auth_login_with_key_option(self, cli_runner: CliRunner) -> None:
        """Auth login should accept API key via --key option."""
        with patch("jiro.cli.auth.store_api_key", return_value=True):
            result = cli_runner.invoke(app, ["auth", "login", "--key", "sk-test-key"])
            assert result.exit_code == 0
            assert "stored securely" in result.stdout

    @pytest.mark.unit
    def test_auth_login_with_short_key_option(self, cli_runner: CliRunner) -> None:
        """Auth login should accept API key via -k option."""
        with patch("jiro.cli.auth.store_api_key", return_value=True):
            result = cli_runner.invoke(app, ["auth", "login", "-k", "sk-test-key"])
            assert result.exit_code == 0
            assert "stored securely" in result.stdout

    @pytest.mark.unit
    def test_auth_login_prompt_for_key(self, cli_runner: CliRunner) -> None:
        """Auth login should prompt for key if not provided."""
        with patch("jiro.cli.auth.store_api_key", return_value=True):
            result = cli_runner.invoke(app, ["auth", "login"], input="sk-test-key\n")
            assert result.exit_code == 0
            assert "stored securely" in result.stdout

    @pytest.mark.unit
    def test_auth_login_empty_key_error(self, cli_runner: CliRunner) -> None:
        """Auth login should reject empty key."""
        with patch("jiro.cli.auth.store_api_key", return_value=True):
            result = cli_runner.invoke(app, ["auth", "login", "--key", ""])
            assert result.exit_code == 1
            assert "cannot be empty" in result.stdout

    @pytest.mark.unit
    def test_auth_login_whitespace_key_error(self, cli_runner: CliRunner) -> None:
        """Auth login should reject whitespace-only key."""
        with patch("jiro.cli.auth.store_api_key", return_value=True):
            result = cli_runner.invoke(app, ["auth", "login", "--key", "   "])
            assert result.exit_code == 1
            assert "cannot be empty" in result.stdout

    @pytest.mark.unit
    def test_auth_login_keyring_unavailable(self, cli_runner: CliRunner) -> None:
        """Auth login should warn if keyring unavailable."""
        with patch("jiro.cli.auth.store_api_key", return_value=False):
            result = cli_runner.invoke(app, ["auth", "login", "--key", "sk-test-key"])
            assert result.exit_code == 0
            assert "Warning" in result.stdout or "warning" in result.stdout.lower()

    @pytest.mark.unit
    def test_auth_login_exception_handling(self, cli_runner: CliRunner) -> None:
        """Auth login should handle exceptions gracefully."""
        with patch("jiro.cli.auth.store_api_key", side_effect=Exception("Keyring error")):
            result = cli_runner.invoke(app, ["auth", "login", "--key", "sk-test-key"])
            assert result.exit_code == 1
            assert "Error" in result.stdout

    @pytest.mark.unit
    def test_auth_login_user_abort(self, cli_runner: CliRunner) -> None:
        """Auth login should handle user abort gracefully."""
        with patch("jiro.cli.auth.typer.prompt", side_effect=typer.Abort()):
            result = cli_runner.invoke(app, ["auth", "login"])
            assert result.exit_code == 1


class TestAuthLogoutCommand:
    """Tests for auth logout command."""

    @pytest.mark.unit
    def test_auth_logout_help(self, cli_runner: CliRunner) -> None:
        """Auth logout help should be available."""
        result = cli_runner.invoke(app, ["auth", "logout", "--help"])
        assert result.exit_code == 0
        assert "Remove API key" in result.stdout

    @pytest.mark.unit
    def test_auth_logout_success(self, cli_runner: CliRunner) -> None:
        """Auth logout should remove API key when user confirms."""
        with patch("jiro.cli.auth.is_key_stored", return_value=True):
            with patch("jiro.cli.auth.remove_api_key", return_value=True):
                result = cli_runner.invoke(app, ["auth", "logout"], input="y\n")
                assert result.exit_code == 0
                assert "removed" in result.stdout

    @pytest.mark.unit
    def test_auth_logout_user_cancels(self, cli_runner: CliRunner) -> None:
        """Auth logout should not remove key if user cancels."""
        with patch("jiro.cli.auth.is_key_stored", return_value=True):
            with patch("jiro.cli.auth.remove_api_key") as mock_remove:
                result = cli_runner.invoke(app, ["auth", "logout"], input="n\n")
                assert result.exit_code == 0
                assert "Cancelled" in result.stdout
                mock_remove.assert_not_called()

    @pytest.mark.unit
    def test_auth_logout_no_key_stored(self, cli_runner: CliRunner) -> None:
        """Auth logout should inform user if no key is stored."""
        with patch("jiro.cli.auth.is_key_stored", return_value=False):
            result = cli_runner.invoke(app, ["auth", "logout"])
            assert result.exit_code == 0
            assert "No API key" in result.stdout

    @pytest.mark.unit
    def test_auth_logout_failure(self, cli_runner: CliRunner) -> None:
        """Auth logout should show error if removal fails."""
        with patch("jiro.cli.auth.is_key_stored", return_value=True):
            with patch("jiro.cli.auth.remove_api_key", return_value=False):
                result = cli_runner.invoke(app, ["auth", "logout"], input="y\n")
                assert result.exit_code == 1
                assert "Failed" in result.stdout

    @pytest.mark.unit
    def test_auth_logout_exception_handling(self, cli_runner: CliRunner) -> None:
        """Auth logout should handle exceptions gracefully."""
        with patch("jiro.cli.auth.is_key_stored", side_effect=Exception("Keyring error")):
            result = cli_runner.invoke(app, ["auth", "logout"])
            assert result.exit_code == 1
            assert "Error" in result.stdout


class TestAuthStatusCommand:
    """Tests for auth status command."""

    @pytest.mark.unit
    def test_auth_status_help(self, cli_runner: CliRunner) -> None:
        """Auth status help should be available."""
        result = cli_runner.invoke(app, ["auth", "status", "--help"])
        assert result.exit_code == 0
        assert "authentication status" in result.stdout or "status" in result.stdout.lower()

    @pytest.mark.unit
    def test_auth_status_key_stored_and_available(self, cli_runner: CliRunner) -> None:
        """Auth status should show key stored in keyring."""
        with patch("jiro.cli.auth.is_key_stored", return_value=True):
            with patch("jiro.cli.auth.get_api_key", return_value="sk-test-key"):
                result = cli_runner.invoke(app, ["auth", "status"])
                assert result.exit_code == 0
                assert "keyring" in result.stdout
                assert "available" in result.stdout or "✓" in result.stdout

    @pytest.mark.unit
    def test_auth_status_no_key_stored(self, cli_runner: CliRunner) -> None:
        """Auth status should show warning when no key is stored."""
        with patch("jiro.cli.auth.is_key_stored", return_value=False):
            with patch("jiro.cli.auth.get_api_key", return_value=None):
                result = cli_runner.invoke(app, ["auth", "status"])
                assert result.exit_code == 0
                assert "No API key" in result.stdout or "not found" in result.stdout.lower()

    @pytest.mark.unit
    def test_auth_status_key_in_environment(self, cli_runner: CliRunner) -> None:
        """Auth status should show key available from environment."""
        with patch("jiro.cli.auth.is_key_stored", return_value=False):
            with patch("jiro.cli.auth.get_api_key", return_value="sk-env-key"):
                result = cli_runner.invoke(app, ["auth", "status"])
                assert result.exit_code == 0
                assert "available" in result.stdout or "✓" in result.stdout

    @pytest.mark.unit
    def test_auth_status_exception_handling(self, cli_runner: CliRunner) -> None:
        """Auth status should handle exceptions gracefully."""
        with patch("jiro.cli.auth.is_key_stored", side_effect=Exception("Keyring error")):
            result = cli_runner.invoke(app, ["auth", "status"])
            assert result.exit_code == 1
            assert "Error" in result.stdout


class TestAuthCommandIntegration:
    """Integration tests for auth commands."""

    @pytest.mark.unit
    def test_auth_subcommand_exists(self, cli_runner: CliRunner) -> None:
        """Auth subcommand should be available in main CLI."""
        result = cli_runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.stdout
        assert "logout" in result.stdout
        assert "status" in result.stdout

    @pytest.mark.unit
    def test_auth_without_subcommand(self, cli_runner: CliRunner) -> None:
        """Auth without subcommand should show help."""
        result = cli_runner.invoke(app, ["auth"])
        # Exit code 0 or 2 is acceptable (0 for help, 2 for missing subcommand)
        assert result.exit_code in (0, 2)
        assert "login" in result.stdout or "commands" in result.stdout.lower()
