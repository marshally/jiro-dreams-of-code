"""Tests for doctor command health checks."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.cli.doctor import (
    DoctorResult,
    FixResult,
    check_api_key,
    check_beads,
    check_claude_sdk,
    check_config,
    check_git,
    check_lint_command,
    check_python_version,
    check_test_command,
    fix_missing_config,
    run_doctor,
)
from jiro.config.schema import Config
from jiro.core.session import CheckResult


class TestCheckPythonVersion:
    """Tests for check_python_version."""

    @pytest.mark.unit
    def test_python_version_meets_minimum(self) -> None:
        """Should pass if Python version >= 3.10."""
        result = check_python_version()
        assert isinstance(result, CheckResult)
        assert result.name == "python_version"
        # Current running Python should be >= 3.10
        assert result.passed is True
        assert result.error is None

    @pytest.mark.unit
    def test_python_version_result_structure(self) -> None:
        """CheckResult should have correct structure."""
        result = check_python_version()
        assert hasattr(result, "name")
        assert hasattr(result, "passed")
        assert hasattr(result, "error")
        assert isinstance(result.passed, bool)


class TestCheckClaudeSDK:
    """Tests for check_claude_sdk."""

    @pytest.mark.unit
    def test_claude_sdk_installed(self) -> None:
        """Should pass if claude_agent_sdk is importable."""
        # Mock successful import
        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            result = check_claude_sdk()
            assert isinstance(result, CheckResult)
            assert result.name == "claude_sdk"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_claude_sdk_missing(self) -> None:
        """Should fail if claude_agent_sdk cannot be imported."""
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'claude_agent_sdk'")
        ):
            result = check_claude_sdk()
            assert result.passed is False
            assert result.error is not None
            assert "claude" in result.error.lower()


class TestCheckAPIKey:
    """Tests for check_api_key."""

    @pytest.mark.unit
    def test_api_key_exists(self) -> None:
        """Should pass if ANTHROPIC_API_KEY is set."""
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-12345"}),
            patch("jiro.cli.doctor.get_api_key", return_value="test-key-12345"),
        ):
            result = check_api_key()
            assert isinstance(result, CheckResult)
            assert result.name == "api_key"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_api_key_missing(self) -> None:
        """Should fail if ANTHROPIC_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove the API key if it exists
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with patch("jiro.cli.doctor.get_api_key", return_value=None):
                result = check_api_key()
                assert result.passed is False
                assert result.error is not None
                assert "keyring" in result.error or "ANTHROPIC_API_KEY" in result.error

    @pytest.mark.unit
    def test_api_key_empty(self) -> None:
        """Should fail if ANTHROPIC_API_KEY is empty."""
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}),
            patch("jiro.cli.doctor.get_api_key", return_value=None),
        ):
            result = check_api_key()
            assert result.passed is False
            assert result.error is not None


class TestCheckGit:
    """Tests for check_git."""

    @pytest.mark.unit
    def test_git_installed(self) -> None:
        """Should pass if git command is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="git version 2.40.0")
            result = check_git()
            assert isinstance(result, CheckResult)
            assert result.name == "git"
            assert result.passed is True
            assert result.error is None
            mock_run.assert_called_once()

    @pytest.mark.unit
    def test_git_not_available(self) -> None:
        """Should fail if git command is not available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=127)
            result = check_git()
            assert result.passed is False
            assert result.error is not None
            assert "git" in result.error.lower()

    @pytest.mark.unit
    def test_git_exception(self) -> None:
        """Should fail if subprocess raises exception."""
        with patch("subprocess.run", side_effect=Exception("Command not found")):
            result = check_git()
            assert result.passed is False
            assert result.error is not None


class TestCheckTestCommand:
    """Tests for check_test_command."""

    @pytest.mark.unit
    def test_test_command_works(self) -> None:
        """Should pass if test command executes successfully."""
        config = Config()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_test_command(config)
            assert isinstance(result, CheckResult)
            assert result.name == "test_command"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_test_command_fails(self) -> None:
        """Should fail if test command returns non-zero exit code."""
        config = Config()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="test failed")
            result = check_test_command(config)
            assert result.passed is False
            assert result.error is not None

    @pytest.mark.unit
    def test_test_command_exception(self) -> None:
        """Should fail if test command raises exception."""
        config = Config()
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result = check_test_command(config)
            assert result.passed is False
            assert result.error is not None


class TestCheckLintCommand:
    """Tests for check_lint_command."""

    @pytest.mark.unit
    def test_lint_command_works(self) -> None:
        """Should pass if lint command executes successfully."""
        config = Config()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_lint_command(config)
            assert isinstance(result, CheckResult)
            assert result.name == "lint_command"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_lint_command_fails(self) -> None:
        """Should fail if lint command returns non-zero exit code."""
        config = Config()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="lint failed")
            result = check_lint_command(config)
            assert result.passed is False
            assert result.error is not None

    @pytest.mark.unit
    def test_lint_command_exception(self) -> None:
        """Should fail if lint command raises exception."""
        config = Config()
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result = check_lint_command(config)
            assert result.passed is False
            assert result.error is not None


class TestCheckBeads:
    """Tests for check_beads."""

    @pytest.mark.unit
    def test_beads_available(self) -> None:
        """Should pass if bd command is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="bd version 1.0.0")
            result = check_beads()
            assert isinstance(result, CheckResult)
            assert result.name == "beads"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_beads_not_available(self) -> None:
        """Should fail if bd command is not available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=127)
            result = check_beads()
            assert result.passed is False
            assert result.error is not None
            assert "bd" in result.error.lower() or "beads" in result.error.lower()

    @pytest.mark.unit
    def test_beads_exception(self) -> None:
        """Should fail if subprocess raises exception."""
        with patch("subprocess.run", side_effect=Exception("Command error")):
            result = check_beads()
            assert result.passed is False
            assert result.error is not None


class TestCheckConfig:
    """Tests for check_config."""

    @pytest.mark.unit
    def test_config_loads(self) -> None:
        """Should pass if config can be loaded."""
        with patch("jiro.cli.doctor.load_config") as mock_load:
            mock_load.return_value = Config()
            result = check_config()
            assert isinstance(result, CheckResult)
            assert result.name == "config"
            assert result.passed is True
            assert result.error is None

    @pytest.mark.unit
    def test_config_fails_to_load(self) -> None:
        """Should fail if config loading raises exception."""
        with patch("jiro.cli.doctor.load_config", side_effect=Exception("Config error")):
            result = check_config()
            assert result.passed is False
            assert result.error is not None

    @pytest.mark.unit
    def test_config_missing_file(self) -> None:
        """Should fail if config file does not exist."""
        with patch("jiro.cli.doctor.load_config", side_effect=FileNotFoundError("No config")):
            result = check_config()
            assert result.passed is False
            assert result.error is not None


class TestDoctorResult:
    """Tests for DoctorResult dataclass."""

    @pytest.mark.unit
    def test_doctor_result_all_pass(self) -> None:
        """DoctorResult should indicate success when all checks pass."""
        checks = {
            "python_version": CheckResult("python_version", True),
            "claude_sdk": CheckResult("claude_sdk", True),
            "api_key": CheckResult("api_key", True),
        }
        result = DoctorResult(passed=True, checks=checks, errors=[])
        assert result.passed is True
        assert len(result.checks) == 3
        assert len(result.errors) == 0

    @pytest.mark.unit
    def test_doctor_result_with_errors(self) -> None:
        """DoctorResult should track errors from failed checks."""
        checks = {
            "python_version": CheckResult("python_version", True),
            "api_key": CheckResult("api_key", False, "API key not set"),
        }
        errors = ["api_key: API key not set"]
        result = DoctorResult(passed=False, checks=checks, errors=errors)
        assert result.passed is False
        assert len(result.errors) == 1
        assert "API key not set" in result.errors[0]


class TestRunDoctor:
    """Tests for run_doctor orchestration."""

    @pytest.mark.unit
    def test_run_doctor_all_pass(self) -> None:
        """run_doctor should return success when all checks pass."""
        with (
            patch("jiro.cli.doctor.check_python_version") as mock_py,
            patch("jiro.cli.doctor.check_claude_sdk") as mock_sdk,
            patch("jiro.cli.doctor.check_api_key") as mock_key,
            patch("jiro.cli.doctor.check_git") as mock_git,
            patch("jiro.cli.doctor.check_test_command") as mock_test,
            patch("jiro.cli.doctor.check_lint_command") as mock_lint,
            patch("jiro.cli.doctor.check_beads") as mock_beads,
            patch("jiro.cli.doctor.check_config") as mock_config,
            patch("jiro.cli.doctor.check_gitignore") as mock_gitignore,
        ):
            # All checks pass
            check_obj = CheckResult("test", True)
            mock_py.return_value = check_obj
            mock_sdk.return_value = check_obj
            mock_key.return_value = check_obj
            mock_git.return_value = check_obj
            mock_test.return_value = check_obj
            mock_lint.return_value = check_obj
            mock_beads.return_value = check_obj
            mock_config.return_value = check_obj
            mock_gitignore.return_value = check_obj

            result = run_doctor()
            assert isinstance(result, DoctorResult)
            assert result.passed is True
            assert len(result.checks) == 9
            assert len(result.errors) == 0

    @pytest.mark.unit
    def test_run_doctor_some_fail(self) -> None:
        """run_doctor should return failure when any check fails."""
        with (
            patch("jiro.cli.doctor.check_python_version") as mock_py,
            patch("jiro.cli.doctor.check_claude_sdk") as mock_sdk,
            patch("jiro.cli.doctor.check_api_key") as mock_key,
            patch("jiro.cli.doctor.check_git") as mock_git,
            patch("jiro.cli.doctor.check_test_command") as mock_test,
            patch("jiro.cli.doctor.check_lint_command") as mock_lint,
            patch("jiro.cli.doctor.check_beads") as mock_beads,
            patch("jiro.cli.doctor.check_config") as mock_config,
            patch("jiro.cli.doctor.check_gitignore") as mock_gitignore,
        ):
            # api_key check fails
            pass_check = CheckResult("test", True)
            fail_check = CheckResult("api_key", False, "API key not set")

            mock_py.return_value = pass_check
            mock_sdk.return_value = pass_check
            mock_key.return_value = fail_check
            mock_git.return_value = pass_check
            mock_test.return_value = pass_check
            mock_lint.return_value = pass_check
            mock_beads.return_value = pass_check
            mock_config.return_value = pass_check
            mock_gitignore.return_value = pass_check

            result = run_doctor()
            assert result.passed is False
            assert len(result.checks) == 9
            assert len(result.errors) >= 1
            assert any("api_key" in error for error in result.errors)

    @pytest.mark.unit
    def test_run_doctor_returns_all_checks(self) -> None:
        """run_doctor should return all 9 checks."""
        with (
            patch("jiro.cli.doctor.check_python_version") as mock_py,
            patch("jiro.cli.doctor.check_claude_sdk") as mock_sdk,
            patch("jiro.cli.doctor.check_api_key") as mock_key,
            patch("jiro.cli.doctor.check_git") as mock_git,
            patch("jiro.cli.doctor.check_test_command") as mock_test,
            patch("jiro.cli.doctor.check_lint_command") as mock_lint,
            patch("jiro.cli.doctor.check_beads") as mock_beads,
            patch("jiro.cli.doctor.check_config") as mock_config,
            patch("jiro.cli.doctor.check_gitignore") as mock_gitignore,
        ):
            check_obj = CheckResult("test", True)
            mock_py.return_value = check_obj
            mock_sdk.return_value = check_obj
            mock_key.return_value = check_obj
            mock_git.return_value = check_obj
            mock_test.return_value = check_obj
            mock_lint.return_value = check_obj
            mock_beads.return_value = check_obj
            mock_config.return_value = check_obj
            mock_gitignore.return_value = check_obj

            result = run_doctor()

            # Verify all 9 checks are present
            expected_checks = {
                "python_version",
                "claude_sdk",
                "api_key",
                "git",
                "test_command",
                "lint_command",
                "beads",
                "config",
                "gitignore",
            }
            assert expected_checks == set(result.checks.keys())


class TestFixResult:
    """Tests for FixResult dataclass."""

    @pytest.mark.unit
    def test_fix_result_creation(self) -> None:
        """FixResult should be created with fix data."""
        result = FixResult(
            config_created=True,
            errors=[],
        )
        assert result.config_created is True
        assert result.errors == []

    @pytest.mark.unit
    def test_fix_result_with_errors(self) -> None:
        """FixResult should track errors from failed fixes."""
        result = FixResult(
            config_created=False,
            errors=["Failed to create config"],
        )
        assert result.config_created is False
        assert len(result.errors) == 1
        assert "Failed to create config" in result.errors


class TestFixMissingConfig:
    """Tests for fix_missing_config function."""

    @pytest.mark.unit
    def test_create_missing_config(self, tmp_path: Path, monkeypatch) -> None:
        """Should create missing config with default values."""
        # Set up fake home directory for stealth mode
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Config should not exist initially
        from jiro.core.paths import get_config_path

        config_path = get_config_path(project_root, stealth=True, project_name="test-project")
        assert not config_path.exists()

        # Fix missing config
        result = fix_missing_config(project_root, "test-project")

        # Verify config was created
        assert config_path.exists()
        assert result is True

    @pytest.mark.unit
    def test_skip_existing_config(self, tmp_path: Path, monkeypatch) -> None:
        """Should not overwrite existing config."""
        # Set up fake home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create existing config
        from jiro.core.paths import get_config_path

        config_path = get_config_path(project_root, stealth=True, project_name="test-project")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("existing: true\n")

        # Fix missing config
        result = fix_missing_config(project_root, "test-project")

        # Should return False (not created)
        assert result is False

        # Verify original config unchanged
        assert "existing: true" in config_path.read_text()

    @pytest.mark.unit
    def test_default_to_cwd(self, tmp_path: Path, monkeypatch) -> None:
        """Should default to current working directory."""
        # Set up fake home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        project_root = tmp_path / "project"
        project_root.mkdir()
        monkeypatch.chdir(project_root)

        # Fix missing config without specifying path
        result = fix_missing_config()

        # Verify config was created
        from jiro.core.paths import get_config_path

        config_path = get_config_path(project_root, stealth=True, project_name="project")
        assert config_path.exists()
        assert result is True

    @pytest.mark.unit
    def test_config_has_valid_structure(self, tmp_path: Path, monkeypatch) -> None:
        """Created config should have valid YAML structure."""
        # Set up fake home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Fix missing config
        fix_missing_config(project_root, "test-project")

        # Verify config can be loaded
        from jiro.config.loader import load_config

        config = load_config(project_root, "test-project")
        assert config is not None
        assert hasattr(config, "commands")
        assert hasattr(config, "models")
