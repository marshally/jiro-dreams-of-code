"""Tests for mode CLI commands."""

from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


class TestModeCommand:
    """Tests for mode command."""

    @pytest.mark.unit
    def test_mode_help(self, cli_runner: CliRunner) -> None:
        """Mode command should display help."""
        result = cli_runner.invoke(app, ["mode", "--help"])
        assert result.exit_code == 0
        assert "stealth" in result.stdout.lower() or "mode" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_no_argument_shows_current_mode_local(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command with no argument should show current mode (local)."""
        # Setup mock to show local mode is active
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = tmp_path / "home"

        result = cli_runner.invoke(app, ["mode"])
        assert result.exit_code == 0
        assert "local" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_no_argument_shows_current_mode_stealth(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command with no argument should show current mode (stealth)."""
        # Setup mock to show stealth mode is active
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"
        stealth_dir = home_dir / ".jiro-dreams-of-code" / "project"
        stealth_dir.mkdir(parents=True)

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode"])
        assert result.exit_code == 0
        assert "stealth" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_no_argument_no_directory(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should handle case where no mode directory exists."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        home_dir = tmp_path / "home"

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode"])
        assert result.exit_code == 0
        # Should indicate no mode is currently set

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_to_stealth_with_confirmation(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should switch to stealth mode with confirmation."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()
        (local_dir / "jiro.db").touch()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth"], input="y\n")
        assert result.exit_code == 0
        # Should show confirmation prompt
        assert "confirm" in result.stdout.lower() or "migrate" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_to_stealth_with_yes_flag(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should skip confirmation with --yes flag."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()
        (local_dir / "jiro.db").touch()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth", "--yes"])
        assert result.exit_code == 0
        # Should not prompt for confirmation
        mock_copytree.assert_called()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_to_local_with_confirmation(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should switch to local mode with confirmation."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        home_dir = tmp_path / "home"
        stealth_dir = home_dir / ".jiro-dreams-of-code" / "project"
        stealth_dir.mkdir(parents=True)
        (stealth_dir / "jiro.db").touch()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "local"], input="y\n")
        assert result.exit_code == 0
        # Should show confirmation prompt
        assert "confirm" in result.stdout.lower() or "migrate" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_to_local_with_yes_flag(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should skip confirmation with --yes flag."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        home_dir = tmp_path / "home"
        stealth_dir = home_dir / ".jiro-dreams-of-code" / "project"
        stealth_dir.mkdir(parents=True)
        (stealth_dir / "jiro.db").touch()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "local", "--yes"])
        assert result.exit_code == 0
        # Should not prompt for confirmation
        mock_copytree.assert_called()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_decline_confirmation(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should cancel switch if user declines confirmation."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth"], input="n\n")
        assert result.exit_code == 0
        # Should cancel the switch
        assert "cancel" in result.stdout.lower() or "aborted" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_already_in_target_mode(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should notify if already in target mode."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = tmp_path / "home"

        result = cli_runner.invoke(app, ["mode", "local"])
        assert result.exit_code == 0
        # Should notify already in that mode
        assert "already" in result.stdout.lower() or "local" in result.stdout.lower()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_migration_copies_files(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should copy files during migration."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()
        (local_dir / "jiro.db").touch()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth", "--yes"])
        assert result.exit_code == 0
        # copytree should be called to migrate data
        mock_copytree.assert_called()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.shutil.copytree")
    @mock.patch("jiro.cli.mode.shutil.rmtree")
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_migration_removes_old_directory(
        self, mock_cwd, mock_home, mock_rmtree, mock_copytree, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should remove old directory after migration."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_dir = project_root / ".jiro-dreams-of-code"
        local_dir.mkdir()
        (local_dir / "jiro.db").touch()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth", "--yes"])
        assert result.exit_code == 0
        # rmtree should be called to remove old directory
        mock_rmtree.assert_called()

    @pytest.mark.unit
    @mock.patch("jiro.cli.mode.Path.home")
    @mock.patch("jiro.cli.mode.Path.cwd")
    def test_mode_switch_to_same_mode_stealth_to_stealth(
        self, mock_cwd, mock_home, cli_runner: CliRunner, tmp_path
    ) -> None:
        """Mode command should handle switching to same mode (stealth to stealth)."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        home_dir = tmp_path / "home"
        stealth_dir = home_dir / ".jiro-dreams-of-code" / "project"
        stealth_dir.mkdir(parents=True)

        mock_cwd.return_value = project_root
        mock_home.return_value = home_dir

        result = cli_runner.invoke(app, ["mode", "stealth"])
        assert result.exit_code == 0
        # Should indicate already in stealth mode
        assert "already" in result.stdout.lower() or "stealth" in result.stdout.lower()
