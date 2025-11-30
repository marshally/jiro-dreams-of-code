"""Tests for project name derivation from git remote."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.core.project import get_project_name_from_git


class TestGetProjectNameFromGit:
    """Tests for get_project_name_from_git function."""

    @pytest.mark.unit
    def test_ssh_url_with_git_suffix(self) -> None:
        """SSH URL with .git suffix."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="git@github.com:user/repo.git\n",
            )
            result = get_project_name_from_git(Path("/some/path"))
            assert result == "repo"

    @pytest.mark.unit
    def test_https_url_with_git_suffix(self) -> None:
        """HTTPS URL with .git suffix."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/user/repo.git\n",
            )
            result = get_project_name_from_git(Path("/some/path"))
            assert result == "repo"

    @pytest.mark.unit
    def test_https_url_without_git_suffix(self) -> None:
        """HTTPS URL without .git suffix."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/user/repo\n",
            )
            result = get_project_name_from_git(Path("/some/path"))
            assert result == "repo"

    @pytest.mark.unit
    def test_gitlab_ssh_url(self) -> None:
        """GitLab SSH URL."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="git@gitlab.com:group/subgroup/project.git\n",
            )
            result = get_project_name_from_git(Path("/some/path"))
            assert result == "project"

    @pytest.mark.unit
    def test_no_remote_returns_directory_name(self, tmp_path: Path) -> None:
        """No remote should return directory name."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128,  # Git error code
                stdout="",
            )
            result = get_project_name_from_git(tmp_path)
            assert result == tmp_path.name

    @pytest.mark.unit
    def test_empty_remote_returns_directory_name(self, tmp_path: Path) -> None:
        """Empty remote output should return directory name."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
            )
            result = get_project_name_from_git(tmp_path)
            assert result == tmp_path.name

    @pytest.mark.unit
    def test_passes_correct_cwd_to_git(self) -> None:
        """Should pass project_root as cwd to git command."""
        with patch("jiro.core.project.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="git@github.com:user/repo.git\n",
            )
            project_root = Path("/my/project")
            get_project_name_from_git(project_root)
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == project_root
