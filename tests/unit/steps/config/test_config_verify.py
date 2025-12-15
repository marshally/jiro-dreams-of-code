"""Tests for ConfigVerify class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.steps.config.config_result import ConfigResult
from jiro.steps.config.config_verify import CONFIG_EXTENSIONS, SPECIAL_CONFIG_FILES, ConfigVerify
from jiro.steps.types import VerificationError
from jiro.verifications.base import Verification


class TestConfigVerifyIsVerification:
    """Test that ConfigVerify is a proper Verification subclass."""

    def test_is_verification_subclass(self):
        """ConfigVerify should inherit from Verification."""
        assert issubclass(ConfigVerify, Verification)

    def test_can_instantiate(self):
        """Should be able to instantiate ConfigVerify."""
        verify = ConfigVerify()
        assert isinstance(verify, ConfigVerify)


class TestConfigVerifyExtensions:
    """Test config file extension recognition."""

    def test_has_standard_extensions(self):
        """Should have standard config extensions."""
        assert ".yaml" in CONFIG_EXTENSIONS
        assert ".yml" in CONFIG_EXTENSIONS
        assert ".toml" in CONFIG_EXTENSIONS
        assert ".json" in CONFIG_EXTENSIONS
        assert ".ini" in CONFIG_EXTENSIONS
        assert ".env" in CONFIG_EXTENSIONS

    def test_has_special_config_files(self):
        """Should have special config files."""
        assert "dockerfile" in SPECIAL_CONFIG_FILES
        assert "makefile" in SPECIAL_CONFIG_FILES
        assert "pyproject.toml" in SPECIAL_CONFIG_FILES
        assert ".gitignore" in SPECIAL_CONFIG_FILES


class TestConfigVerifyIsConfigFile:
    """Test the _verify_is_config_file method."""

    def test_yaml_extensions(self):
        """Should recognize .yaml and .yml files."""
        verify = ConfigVerify()
        # Should not raise
        verify._verify_is_config_file("config.yaml")
        verify._verify_is_config_file("config.yml")
        verify._verify_is_config_file("settings.yaml")

    def test_toml_files(self):
        """Should recognize .toml files."""
        verify = ConfigVerify()
        verify._verify_is_config_file("pyproject.toml")
        verify._verify_is_config_file("config.toml")

    def test_json_files(self):
        """Should recognize .json files."""
        verify = ConfigVerify()
        verify._verify_is_config_file("config.json")
        verify._verify_is_config_file("package.json")

    def test_ini_cfg_conf_files(self):
        """Should recognize .ini, .cfg, .conf files."""
        verify = ConfigVerify()
        verify._verify_is_config_file("config.ini")
        verify._verify_is_config_file("setup.cfg")
        verify._verify_is_config_file("app.conf")

    def test_env_files(self):
        """Should recognize .env files."""
        verify = ConfigVerify()
        verify._verify_is_config_file(".env")
        verify._verify_is_config_file(".env.local")
        verify._verify_is_config_file(".env.example")

    def test_special_config_files(self):
        """Should recognize special config files."""
        verify = ConfigVerify()
        verify._verify_is_config_file("Dockerfile")
        verify._verify_is_config_file("dockerfile")
        verify._verify_is_config_file("Makefile")
        verify._verify_is_config_file("makefile")
        verify._verify_is_config_file(".gitignore")
        verify._verify_is_config_file(".editorconfig")

    def test_case_insensitive(self):
        """Should recognize config files case-insensitively."""
        verify = ConfigVerify()
        verify._verify_is_config_file("CONFIG.YAML")
        verify._verify_is_config_file("DOCKERFILE")
        verify._verify_is_config_file("MAKEFILE")

    def test_non_config_file_raises_error(self):
        """Should raise VerificationError for non-config files."""
        verify = ConfigVerify()
        with pytest.raises(VerificationError) as exc_info:
            verify._verify_is_config_file("script.py")
        assert "Non-config file changed" in str(exc_info.value)

    def test_non_config_various_files(self):
        """Should reject various non-config file types."""
        verify = ConfigVerify()
        with pytest.raises(VerificationError):
            verify._verify_is_config_file("script.js")
        with pytest.raises(VerificationError):
            verify._verify_is_config_file("README.md")
        with pytest.raises(VerificationError):
            verify._verify_is_config_file("src/app.py")


class TestConfigVerifyGetConfigType:
    """Test the _get_config_type method."""

    def test_yaml_type(self):
        """Should identify yaml config type."""
        verify = ConfigVerify()
        assert verify._get_config_type("config.yaml") == "yaml"
        assert verify._get_config_type("settings.yml") == "yml"

    def test_json_type(self):
        """Should identify json config type."""
        verify = ConfigVerify()
        assert verify._get_config_type("config.json") == "json"

    def test_toml_type(self):
        """Should identify toml config type."""
        verify = ConfigVerify()
        assert verify._get_config_type("pyproject.toml") == "toml"

    def test_ini_type(self):
        """Should identify ini config type."""
        verify = ConfigVerify()
        assert verify._get_config_type("setup.ini") == "ini"

    def test_env_type(self):
        """Should identify env config type."""
        verify = ConfigVerify()
        assert verify._get_config_type(".env") == "env"

    def test_special_config_types(self):
        """Should identify special config file types."""
        verify = ConfigVerify()
        assert verify._get_config_type("dockerfile") == "dockerfile"
        assert verify._get_config_type("Dockerfile") == "dockerfile"
        assert verify._get_config_type("makefile") == "makefile"
        assert verify._get_config_type("Makefile") == "makefile"


class TestConfigVerifyVerify:
    """Test the verify method."""

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_success_single_file(self, mock_run):
        """Should verify config change successfully."""
        mock_run.return_value = MagicMock(
            stdout="config.yaml",
            stderr="",
            returncode=0,
        )

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification_result = verify.verify(result=result)

        assert verification_result.success is True
        assert "yaml" in verification_result.verification_output

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_success_multiple_files(self, mock_run):
        """Should verify multiple config changes."""
        mock_run.return_value = MagicMock(
            stdout="config.yaml\nsettings.json\n.env",
            stderr="",
            returncode=0,
        )

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml"), Path("settings.json"), Path(".env")],
            config_files_changed=3,
            config_types=["yaml", "json", "env"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        verification_result = verify.verify(result=result)

        assert verification_result.success is True

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_fails_git_diff_not_matching(self, mock_run):
        """Should fail when git diff doesn't match result."""
        mock_run.return_value = MagicMock(
            stdout="config.yaml\nsettings.json",
            stderr="",
            returncode=0,
        )

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify.verify(result=result)
        assert "git diff does not match changed_files" in str(exc_info.value)

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_fails_non_config_file(self, mock_run):
        """Should fail when non-config file is changed."""
        mock_run.return_value = MagicMock(
            stdout="config.yaml\nscript.py",
            stderr="",
            returncode=0,
        )

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml"), Path("script.py")],
            config_files_changed=2,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify.verify(result=result)
        assert "Non-config file changed" in str(exc_info.value)

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_fails_count_mismatch(self, mock_run):
        """Should fail when config file count doesn't match."""
        mock_run.return_value = MagicMock(
            stdout="config.yaml",
            stderr="",
            returncode=0,
        )

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=5,  # Wrong count
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError) as exc_info:
            verify.verify(result=result)
        assert "Config file count mismatch" in str(exc_info.value)

    @patch("jiro.steps.config.config_verify.subprocess.run")
    def test_verify_fails_git_diff_error(self, mock_run):
        """Should fail when git diff command fails."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(127, "git", stderr="git not found")

        verify = ConfigVerify()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )

        with pytest.raises(VerificationError):
            verify.verify(result=result)
