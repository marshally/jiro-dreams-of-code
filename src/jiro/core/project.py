"""Project name derivation from git remote."""

import subprocess
from pathlib import Path


def get_project_name_from_git(project_root: Path) -> str:
    """Derive project name from git remote URL.

    Handles various URL formats:
    - git@github.com:user/repo.git -> repo
    - https://github.com/user/repo.git -> repo
    - https://github.com/user/repo -> repo
    - git@gitlab.com:group/subgroup/project.git -> project

    Args:
        project_root: The root directory of the project.

    Returns:
        The derived project name, or the directory name if no remote found.
    """
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return project_root.name

    url = result.stdout.strip()
    return _extract_repo_name(url)


def _extract_repo_name(url: str) -> str:
    """Extract repository name from a git URL.

    Args:
        url: Git remote URL (SSH or HTTPS format).

    Returns:
        The repository name.
    """
    # Remove .git suffix if present
    if url.endswith(".git"):
        url = url[:-4]

    # Handle SSH format: git@host:path/repo
    if url.startswith("git@"):
        # Extract path after the colon
        path = url.split(":", 1)[1] if ":" in url else url
    else:
        # Handle HTTPS format: https://host/path/repo
        # Extract path after host
        path = url.split("/", 3)[-1] if "/" in url else url

    # Get the last component (repo name)
    return path.rsplit("/", 1)[-1]
