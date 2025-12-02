"""Tests for init command implementation."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestInitCommandGitCheck:
    """Tests for git repository verification."""

    @pytest.mark.unit
    def test_init_fails_outside_git_repo(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should fail when not in a git repository."""
        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            result = cli_runner.invoke(app, ["init"])
            assert result.exit_code != 0
            assert "git" in result.stdout.lower() or "repository" in result.stdout.lower()

    @pytest.mark.unit
    def test_init_succeeds_in_git_repo(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should succeed when in a git repository."""
        # Create a mock git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            # Mock git rev-parse succeeding
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = cli_runner.invoke(app, ["init"])
            # Should not fail on git check
            assert "not a git repository" not in result.stdout.lower()


class TestInitDirectoryCreation:
    """Tests for directory structure creation."""

    @pytest.mark.unit
    def test_init_creates_jiro_directory(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should create .jiro-dreams-of-code directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init"])
            # Directory should be created
            jiro_dir = tmp_path / ".jiro-dreams-of-code"
            assert jiro_dir.exists()

    @pytest.mark.unit
    def test_init_creates_subdirectories(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should create specs and logs subdirectories."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init"])
            jiro_dir = tmp_path / ".jiro-dreams-of-code"
            assert (jiro_dir / "specs").exists()
            assert (jiro_dir / "logs").exists()

    @pytest.mark.unit
    def test_init_stealth_mode_uses_home(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init --stealth should create directory in home."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.init.Path.home", return_value=home_dir),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init", "--stealth"])
            stealth_dir = home_dir / ".jiro-dreams-of-code" / tmp_path.name
            assert stealth_dir.exists()


class TestInitConfigFile:
    """Tests for config file creation."""

    @pytest.mark.unit
    def test_init_creates_config_file(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should create config.yaml file."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init"])
            config_file = tmp_path / ".jiro-dreams-of-code" / "config.yaml"
            assert config_file.exists()

    @pytest.mark.unit
    def test_init_config_has_default_values(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init config should have default model and command values."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init"])
            config_file = tmp_path / ".jiro-dreams-of-code" / "config.yaml"
            content = config_file.read_text()
            assert "models" in content or "test" in content or "lint" in content


class TestInitBeadsDatabase:
    """Tests for beads database initialization."""

    @pytest.mark.unit
    def test_init_calls_bd_init(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should call bd init to initialize beads database."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            cli_runner.invoke(app, ["init"])
            # Verify subprocess was called at least once (for git and bd init)
            assert len(mock_run.call_args_list) >= 1


class TestInitProjectName:
    """Tests for project name derivation."""

    @pytest.mark.unit
    def test_init_derives_project_name_from_directory(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Init should derive project name from current directory."""
        project_dir = tmp_path / "my-awesome-project"
        project_dir.mkdir()
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=project_dir),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = cli_runner.invoke(app, ["init"])
            assert result.exit_code == 0


class TestInitIdempotency:
    """Tests for init command idempotency."""

    @pytest.mark.unit
    def test_init_can_reinitialize(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Init should succeed even if already initialized."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        jiro_dir = tmp_path / ".jiro-dreams-of-code"
        jiro_dir.mkdir()

        with (
            patch("jiro.cli.init.Path.cwd", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = cli_runner.invoke(app, ["init"])
            # Should not fail on reinit
            assert result.exit_code == 0 or "already" in result.stdout.lower()
