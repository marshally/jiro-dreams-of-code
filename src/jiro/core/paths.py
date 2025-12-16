"""Path resolution for jiro in normal and stealth modes."""

from pathlib import Path

JIRO_DIR_NAME = ".jiro-dreams-of-code"


def get_jiro_dir(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Get the jiro directory for a project.

    Args:
        project_root: The root directory of the project.
        stealth: If True, use ~/.jiro-dreams-of-code/$PROJECT/ instead of local.
        project_name: Required in stealth mode. The project name for the directory.

    Returns:
        Path to the jiro directory.
    """
    if stealth:
        if project_name is None:
            project_name = project_root.name
        return Path.home() / JIRO_DIR_NAME / project_name
    return project_root / JIRO_DIR_NAME


def get_database_path(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Get the database path for a project.

    Args:
        project_root: The root directory of the project.
        stealth: If True, use stealth mode paths.
        project_name: Required in stealth mode.

    Returns:
        Path to the jiro.db file.
    """
    return get_jiro_dir(project_root, stealth, project_name) / "jiro.db"


def get_config_path(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Get the config file path for a project.

    Args:
        project_root: The root directory of the project.
        stealth: If True, use stealth mode paths.
        project_name: Required in stealth mode.

    Returns:
        Path to the config.yaml file.
    """
    return get_jiro_dir(project_root, stealth, project_name) / "config.yaml"


def get_specs_dir(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Get the specs directory for a project.

    Args:
        project_root: The root directory of the project.
        stealth: If True, use stealth mode paths.
        project_name: Required in stealth mode.

    Returns:
        Path to the specs directory.
    """
    return get_jiro_dir(project_root, stealth, project_name) / "specs"


def get_logs_dir(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Get the logs directory for a project.

    Args:
        project_root: The root directory of the project.
        stealth: If True, use stealth mode paths.
        project_name: Required in stealth mode.

    Returns:
        Path to the logs directory.
    """
    return get_jiro_dir(project_root, stealth, project_name) / "logs"


def get_local_config_path(project_root: Path) -> Path:
    """Get the local config file path in the project root.

    Args:
        project_root: The root directory of the project.

    Returns:
        Path to the .jiro-dreams-of-code.yaml file in project root.
    """
    return project_root / ".jiro-dreams-of-code.yaml"
