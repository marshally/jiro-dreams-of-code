"""Tests for auth manager module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from jiro.auth.manager import (
    get_api_key,
    is_key_stored,
    remove_api_key,
    store_api_key,
)


class TestStoreApiKey:
    """Tests for store_api_key function."""

    @pytest.mark.unit
    def test_store_api_key_success(self) -> None:
        """Store API key successfully in keyring."""
        with patch("jiro.auth.manager.keyring.set_password") as mock_set:
            result = store_api_key("sk-test-key-12345")
            mock_set.assert_called_once_with(
                "jiro-dreams-of-code", "anthropic", "sk-test-key-12345"
            )
            assert result is True

    @pytest.mark.unit
    def test_store_api_key_strips_whitespace(self) -> None:
        """Store API key strips surrounding whitespace."""
        with patch("jiro.auth.manager.keyring.set_password") as mock_set:
            store_api_key("  sk-test-key  \n")
            mock_set.assert_called_once_with(
                "jiro-dreams-of-code", "anthropic", "sk-test-key"
            )

    @pytest.mark.unit
    def test_store_api_key_empty_raises_error(self) -> None:
        """Store API key raises ValueError for empty key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            store_api_key("")

    @pytest.mark.unit
    def test_store_api_key_whitespace_only_raises_error(self) -> None:
        """Store API key raises ValueError for whitespace-only key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            store_api_key("   \n  ")

    @pytest.mark.unit
    def test_store_api_key_keyring_unavailable(self) -> None:
        """Store API key returns False when keyring is unavailable."""
        with patch(
            "jiro.auth.manager.keyring.set_password", side_effect=Exception("Keyring error")
        ):
            result = store_api_key("sk-test-key")
            assert result is False

    @pytest.mark.unit
    def test_store_api_key_logs_success(self) -> None:
        """Store API key logs successful storage."""
        with patch("jiro.auth.manager.keyring.set_password"):
            with patch("jiro.auth.manager.logger.info") as mock_log:
                store_api_key("sk-test-key")
                mock_log.assert_called_once()
                call_kwargs = mock_log.call_args[1]
                assert call_kwargs.get("service") == "jiro-dreams-of-code"

    @pytest.mark.unit
    def test_store_api_key_logs_failure(self) -> None:
        """Store API key logs warning when keyring is unavailable."""
        with patch(
            "jiro.auth.manager.keyring.set_password", side_effect=Exception("Keyring error")
        ):
            with patch("jiro.auth.manager.logger.warning") as mock_log:
                store_api_key("sk-test-key")
                mock_log.assert_called_once()
                call_kwargs = mock_log.call_args[1]
                assert "error" in call_kwargs


class TestGetApiKey:
    """Tests for get_api_key function."""

    @pytest.mark.unit
    def test_get_api_key_from_keyring(self) -> None:
        """Get API key from keyring when available."""
        with patch(
            "jiro.auth.manager.keyring.get_password", return_value="sk-keyring-key"
        ):
            with patch.dict(os.environ, {}, clear=True):
                result = get_api_key()
                assert result == "sk-keyring-key"

    @pytest.mark.unit
    def test_get_api_key_from_environment_fallback(self) -> None:
        """Get API key from environment when keyring unavailable."""
        with patch("jiro.auth.manager.keyring.get_password", return_value=None):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
                result = get_api_key()
                assert result == "sk-env-key"

    @pytest.mark.unit
    def test_get_api_key_prefers_keyring_over_env(self) -> None:
        """Get API key prefers keyring over environment variable."""
        with patch(
            "jiro.auth.manager.keyring.get_password", return_value="sk-keyring-key"
        ):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
                result = get_api_key()
                assert result == "sk-keyring-key"

    @pytest.mark.unit
    def test_get_api_key_strips_env_whitespace(self) -> None:
        """Get API key strips whitespace from environment variable."""
        with patch("jiro.auth.manager.keyring.get_password", return_value=None):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "  sk-env-key  "}):
                result = get_api_key()
                assert result == "sk-env-key"

    @pytest.mark.unit
    def test_get_api_key_returns_none_when_not_found(self) -> None:
        """Get API key returns None when not found in keyring or environment."""
        with patch("jiro.auth.manager.keyring.get_password", return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                result = get_api_key()
                assert result is None

    @pytest.mark.unit
    def test_get_api_key_ignores_keyring_errors(self) -> None:
        """Get API key ignores keyring errors and uses environment fallback."""
        with patch(
            "jiro.auth.manager.keyring.get_password", side_effect=Exception("Keyring error")
        ):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
                result = get_api_key()
                assert result == "sk-env-key"

    @pytest.mark.unit
    def test_get_api_key_logs_source_keyring(self) -> None:
        """Get API key logs when retrieved from keyring."""
        with patch(
            "jiro.auth.manager.keyring.get_password", return_value="sk-keyring-key"
        ):
            with patch.dict(os.environ, {}, clear=True):
                with patch("jiro.auth.manager.logger.debug") as mock_log:
                    get_api_key()
                    mock_log.assert_called_once()
                    call_kwargs = mock_log.call_args[1]
                    assert call_kwargs.get("service") == "jiro-dreams-of-code"

    @pytest.mark.unit
    def test_get_api_key_logs_source_environment(self) -> None:
        """Get API key logs when retrieved from environment."""
        with patch("jiro.auth.manager.keyring.get_password", return_value=None):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env-key"}):
                with patch("jiro.auth.manager.logger.debug") as mock_log:
                    get_api_key()
                    mock_log.assert_called_once()
                    call_kwargs = mock_log.call_args[1]
                    assert call_kwargs.get("variable") == "ANTHROPIC_API_KEY"


class TestRemoveApiKey:
    """Tests for remove_api_key function."""

    @pytest.mark.unit
    def test_remove_api_key_success(self) -> None:
        """Remove API key successfully from keyring."""
        with patch("jiro.auth.manager.keyring.delete_password"):
            result = remove_api_key()
            assert result is True

    @pytest.mark.unit
    def test_remove_api_key_not_found(self) -> None:
        """Remove API key returns False when key not found."""
        import keyring.errors

        with patch(
            "jiro.auth.manager.keyring.delete_password",
            side_effect=keyring.errors.PasswordDeleteError(),
        ):
            result = remove_api_key()
            assert result is False

    @pytest.mark.unit
    def test_remove_api_key_keyring_error(self) -> None:
        """Remove API key returns False on keyring error."""
        with patch(
            "jiro.auth.manager.keyring.delete_password", side_effect=Exception("Keyring error")
        ):
            result = remove_api_key()
            assert result is False

    @pytest.mark.unit
    def test_remove_api_key_logs_success(self) -> None:
        """Remove API key logs successful removal."""
        with patch("jiro.auth.manager.keyring.delete_password"):
            with patch("jiro.auth.manager.logger.info") as mock_log:
                remove_api_key()
                mock_log.assert_called_once()
                call_kwargs = mock_log.call_args[1]
                assert call_kwargs.get("service") == "jiro-dreams-of-code"

    @pytest.mark.unit
    def test_remove_api_key_logs_not_found(self) -> None:
        """Remove API key logs when key not found."""
        import keyring.errors

        with patch(
            "jiro.auth.manager.keyring.delete_password",
            side_effect=keyring.errors.PasswordDeleteError(),
        ):
            with patch("jiro.auth.manager.logger.debug") as mock_log:
                remove_api_key()
                mock_log.assert_called_once()


class TestIsKeyStored:
    """Tests for is_key_stored function."""

    @pytest.mark.unit
    def test_is_key_stored_true(self) -> None:
        """Is key stored returns True when key exists in keyring."""
        with patch("jiro.auth.manager.keyring.get_password", return_value="sk-key"):
            result = is_key_stored()
            assert result is True

    @pytest.mark.unit
    def test_is_key_stored_false_none(self) -> None:
        """Is key stored returns False when keyring returns None."""
        with patch("jiro.auth.manager.keyring.get_password", return_value=None):
            result = is_key_stored()
            assert result is False

    @pytest.mark.unit
    def test_is_key_stored_false_error(self) -> None:
        """Is key stored returns False when keyring error occurs."""
        with patch(
            "jiro.auth.manager.keyring.get_password", side_effect=Exception("Keyring error")
        ):
            result = is_key_stored()
            assert result is False

    @pytest.mark.unit
    def test_is_key_stored_logs_error(self) -> None:
        """Is key stored logs error when keyring check fails."""
        with patch(
            "jiro.auth.manager.keyring.get_password", side_effect=Exception("Keyring error")
        ):
            with patch("jiro.auth.manager.logger.debug") as mock_log:
                is_key_stored()
                mock_log.assert_called_once()
