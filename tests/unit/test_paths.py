"""Tests for path resolution."""

from pathlib import Path
from unittest.mock import patch

import pytest

from jiro.core.paths import (
    get_config_path,
    get_database_path,
    get_jiro_dir,
    get_logs_dir,
    get_specs_dir,
)


class TestGetJiroDir:
    """Tests for get_jiro_dir function."""

    @pytest.mark.unit
    def test_normal_mode_returns_local_dir(self, tmp_path: Path) -> None:
        """Normal mode should return .jiro-dreams-of-code in project root."""
        result = get_jiro_dir(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code"

    @pytest.mark.unit
    def test_stealth_mode_returns_home_dir(self, tmp_path: Path) -> None:
        """Stealth mode should return ~/.jiro-dreams-of-code/$PROJECT/."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_jiro_dir(
                project_root=Path("/some/path/myproject"),
                stealth=True,
                project_name="myproject",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myproject"

    @pytest.mark.unit
    def test_stealth_mode_uses_project_name(self, tmp_path: Path) -> None:
        """Stealth mode should use provided project name."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_jiro_dir(
                project_root=Path("/any/path"),
                stealth=True,
                project_name="custom-project",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "custom-project"

    @pytest.mark.unit
    def test_stealth_mode_defaults_to_project_root_name(self, tmp_path: Path) -> None:
        """Stealth mode should fallback to project_root.name if project_name not provided."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_dir = Path("/some/path/test-project")
            result = get_jiro_dir(
                project_root=project_dir,
                stealth=True,
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "test-project"

    @pytest.mark.unit
    def test_normal_mode_stealth_false_explicit(self, tmp_path: Path) -> None:
        """Explicitly setting stealth=False should use local path."""
        result = get_jiro_dir(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code"
        assert str(result).startswith(str(tmp_path))


class TestGetDatabasePath:
    """Tests for get_database_path function."""

    @pytest.mark.unit
    def test_normal_mode(self, tmp_path: Path) -> None:
        """Database path in normal mode."""
        result = get_database_path(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code" / "jiro.db"

    @pytest.mark.unit
    def test_stealth_mode(self, tmp_path: Path) -> None:
        """Database path in stealth mode."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_database_path(
                project_root=Path("/some/path"),
                stealth=True,
                project_name="myproject",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myproject" / "jiro.db"

    @pytest.mark.unit
    def test_database_path_uses_jiro_dir(self, tmp_path: Path) -> None:
        """Database path should use jiro.db filename."""
        result = get_database_path(project_root=tmp_path, stealth=False)
        assert result.name == "jiro.db"

    @pytest.mark.unit
    def test_stealth_mode_defaults_to_project_root_name(self, tmp_path: Path) -> None:
        """Stealth mode database path should use project root name as fallback."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_dir = Path("/some/path/myapp")
            result = get_database_path(
                project_root=project_dir,
                stealth=True,
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myapp" / "jiro.db"


class TestGetConfigPath:
    """Tests for get_config_path function."""

    @pytest.mark.unit
    def test_normal_mode(self, tmp_path: Path) -> None:
        """Config path in normal mode."""
        result = get_config_path(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code" / "config.yaml"

    @pytest.mark.unit
    def test_stealth_mode(self, tmp_path: Path) -> None:
        """Config path in stealth mode."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_config_path(
                project_root=Path("/some/path"),
                stealth=True,
                project_name="myproject",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myproject" / "config.yaml"

    @pytest.mark.unit
    def test_config_path_filename(self, tmp_path: Path) -> None:
        """Config path should have correct filename."""
        result = get_config_path(project_root=tmp_path, stealth=False)
        assert result.name == "config.yaml"

    @pytest.mark.unit
    def test_stealth_mode_defaults_to_project_root_name(self, tmp_path: Path) -> None:
        """Stealth mode config path should use project root name as fallback."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_dir = Path("/some/path/myapp")
            result = get_config_path(
                project_root=project_dir,
                stealth=True,
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myapp" / "config.yaml"


class TestGetSpecsDir:
    """Tests for get_specs_dir function."""

    @pytest.mark.unit
    def test_normal_mode(self, tmp_path: Path) -> None:
        """Specs dir in normal mode."""
        result = get_specs_dir(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code" / "specs"

    @pytest.mark.unit
    def test_stealth_mode(self, tmp_path: Path) -> None:
        """Specs dir in stealth mode."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_specs_dir(
                project_root=Path("/some/path"),
                stealth=True,
                project_name="myproject",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myproject" / "specs"

    @pytest.mark.unit
    def test_specs_dir_name(self, tmp_path: Path) -> None:
        """Specs path should have correct directory name."""
        result = get_specs_dir(project_root=tmp_path, stealth=False)
        assert result.name == "specs"

    @pytest.mark.unit
    def test_stealth_mode_defaults_to_project_root_name(self, tmp_path: Path) -> None:
        """Stealth mode specs path should use project root name as fallback."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_dir = Path("/some/path/myapp")
            result = get_specs_dir(
                project_root=project_dir,
                stealth=True,
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myapp" / "specs"


class TestGetLogsDir:
    """Tests for get_logs_dir function."""

    @pytest.mark.unit
    def test_normal_mode(self, tmp_path: Path) -> None:
        """Logs dir in normal mode."""
        result = get_logs_dir(project_root=tmp_path, stealth=False)
        assert result == tmp_path / ".jiro-dreams-of-code" / "logs"

    @pytest.mark.unit
    def test_stealth_mode(self, tmp_path: Path) -> None:
        """Logs dir in stealth mode."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            result = get_logs_dir(
                project_root=Path("/some/path"),
                stealth=True,
                project_name="myproject",
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myproject" / "logs"

    @pytest.mark.unit
    def test_logs_dir_name(self, tmp_path: Path) -> None:
        """Logs path should have correct directory name."""
        result = get_logs_dir(project_root=tmp_path, stealth=False)
        assert result.name == "logs"

    @pytest.mark.unit
    def test_stealth_mode_defaults_to_project_root_name(self, tmp_path: Path) -> None:
        """Stealth mode logs path should use project root name as fallback."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_dir = Path("/some/path/myapp")
            result = get_logs_dir(
                project_root=project_dir,
                stealth=True,
            )
            assert result == tmp_path / ".jiro-dreams-of-code" / "myapp" / "logs"


class TestPathConsistency:
    """Tests for consistency across path functions."""

    @pytest.mark.unit
    def test_all_paths_share_jiro_dir_base(self, tmp_path: Path) -> None:
        """All paths should be under the jiro directory."""
        jiro_dir = get_jiro_dir(project_root=tmp_path, stealth=False)
        db_path = get_database_path(project_root=tmp_path, stealth=False)
        config_path = get_config_path(project_root=tmp_path, stealth=False)
        specs_dir = get_specs_dir(project_root=tmp_path, stealth=False)
        logs_dir = get_logs_dir(project_root=tmp_path, stealth=False)

        assert jiro_dir in db_path.parents
        assert jiro_dir in config_path.parents
        assert jiro_dir in specs_dir.parents
        assert jiro_dir in logs_dir.parents

    @pytest.mark.unit
    def test_normal_and_stealth_use_different_roots(self, tmp_path: Path) -> None:
        """Normal and stealth modes should use different root directories."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            normal_db = get_database_path(project_root=Path("/project"), stealth=False)
            stealth_db = get_database_path(
                project_root=Path("/project"),
                stealth=True,
                project_name="myapp",
            )

            # Normal mode uses /project
            assert "project" in str(normal_db)
            # Stealth mode uses home
            assert str(tmp_path) in str(stealth_db)

    @pytest.mark.unit
    def test_stealth_mode_separation_by_project(self, tmp_path: Path) -> None:
        """Different projects in stealth mode should have separate directories."""
        with patch("jiro.core.paths.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            project_root = Path("/some/path")

            app1_db = get_database_path(
                project_root=project_root,
                stealth=True,
                project_name="app1",
            )
            app2_db = get_database_path(
                project_root=project_root,
                stealth=True,
                project_name="app2",
            )

            assert "app1" in str(app1_db)
            assert "app2" in str(app2_db)
            assert str(app1_db) != str(app2_db)
