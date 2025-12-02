"""Init command implementation for jiro."""

import subprocess
from pathlib import Path

import yaml
from rich.console import Console

from jiro.config.schema import Config
from jiro.core.paths import get_config_path, get_jiro_dir, get_logs_dir, get_specs_dir

console = Console()


class InitError(Exception):
    """Error during initialization."""

    pass


def verify_git_repository(project_root: Path) -> bool:
    """Verify we are inside a git repository.

    Args:
        project_root: The directory to check.

    Returns:
        True if inside a git repository.

    Raises:
        InitError: If not in a git repository.
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        raise InitError("Not a git repository. Please run 'git init' first.") from e


def get_project_name(project_root: Path) -> str:
    """Get the project name from the directory or git remote.

    Args:
        project_root: The project root directory.

    Returns:
        The project name.
    """
    # Try to get from git remote first
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
        # Extract project name from URL (e.g., git@github.com:user/project.git -> project)
        if url:
            name = url.split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
    except subprocess.CalledProcessError:
        pass

    # Fall back to directory name
    return project_root.name


def create_directory_structure(
    project_root: Path,
    stealth: bool = False,
    project_name: str | None = None,
) -> Path:
    """Create the jiro directory structure.

    Args:
        project_root: The project root directory.
        stealth: If True, create directories in home.
        project_name: The project name (required for stealth mode).

    Returns:
        Path to the jiro directory.
    """
    jiro_dir = get_jiro_dir(project_root, stealth=stealth, project_name=project_name)
    specs_dir = get_specs_dir(project_root, stealth=stealth, project_name=project_name)
    logs_dir = get_logs_dir(project_root, stealth=stealth, project_name=project_name)

    # Create directories
    jiro_dir.mkdir(parents=True, exist_ok=True)
    specs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return jiro_dir


def create_default_config(
    project_root: Path,
    project_name: str,
    stealth: bool = False,
) -> Path:
    """Create the default configuration file.

    Args:
        project_root: The project root directory.
        project_name: The project name.
        stealth: If True, use stealth mode paths.

    Returns:
        Path to the config file.
    """
    config_path = get_config_path(project_root, stealth=stealth, project_name=project_name)

    # Create default config
    config = Config()
    config_dict = {
        "project": {"name": project_name},
        "models": {
            "planning": config.models.planning,
            "execution": config.models.execution,
            "review": config.models.review,
        },
        "commands": {
            "test": config.commands.test,
            "lint": config.commands.lint,
            "lint_fix": config.commands.lint_fix,
        },
        "conventions": {
            "test_file_pattern": config.conventions.test_file_pattern,
        },
        "preflight": {
            "skip_if_recent_minutes": config.preflight.skip_if_recent_minutes,
        },
    }

    # Write config file
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    return config_path


def initialize_beads(
    project_root: Path,
    project_name: str,
    stealth: bool = False,
) -> bool:
    """Initialize the beads database.

    Args:
        project_root: The project root directory.
        project_name: The project name (used as prefix).
        stealth: If True, use stealth mode paths.

    Returns:
        True if successful, False otherwise.
    """
    jiro_dir = get_jiro_dir(project_root, stealth=stealth, project_name=project_name)

    try:
        # bd init uses the current directory, so change to jiro_dir
        subprocess.run(
            ["bd", "init", "--prefix", project_name],
            cwd=jiro_dir,
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        # bd might not be available or might already be initialized
        console.print("[yellow]Warning: Could not initialize beads database.[/yellow]")
        console.print("[dim]This is OK if 'bd' is not installed or already initialized.[/dim]")
        return False
    except FileNotFoundError:
        console.print("[yellow]Warning: 'bd' command not found.[/yellow]")
        return False


def run_init(
    project_root: Path,
    stealth: bool = False,
    interactive: bool = False,
) -> bool:
    """Run the init command.

    Args:
        project_root: The project root directory.
        stealth: If True, use stealth mode.
        interactive: If True, prompt for configuration.

    Returns:
        True if successful.

    Raises:
        InitError: If initialization fails.
    """
    # Verify git repository
    verify_git_repository(project_root)

    # Get project name
    project_name = get_project_name(project_root)
    console.print(f"[cyan]Initializing jiro for project:[/cyan] {project_name}")

    # Create directory structure
    jiro_dir = create_directory_structure(project_root, stealth=stealth, project_name=project_name)
    console.print(f"[green]✓[/green] Created directory: {jiro_dir}")

    # Create config file
    config_path = create_default_config(project_root, project_name, stealth=stealth)
    console.print(f"[green]✓[/green] Created config: {config_path}")

    # Initialize beads
    if initialize_beads(project_root, project_name, stealth=stealth):
        console.print("[green]✓[/green] Initialized beads database")
    else:
        console.print("[yellow]![/yellow] Beads database not initialized (manual setup required)")

    # Interactive mode (for future implementation)
    if interactive:
        console.print("\n[yellow]Interactive mode is not yet implemented.[/yellow]")
        console.print("[dim]In the future, this will prompt for test and lint commands.[/dim]")

    console.print("\n[green]Initialization complete![/green]")
    return True
