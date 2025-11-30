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
