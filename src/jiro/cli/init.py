"""Init command implementation for jiro."""

import subprocess
from pathlib import Path
from typing import Annotated, cast

import typer
import yaml
from rich.console import Console

from jiro.config.schema import Config
from jiro.core.paths import get_config_path, get_jiro_dir, get_logs_dir, get_specs_dir

app = typer.Typer(
    name="init",
    help="Initialize jiro in a project",
    no_args_is_help=False,
)

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


def prompt_for_test_command(default: str = "pytest") -> str:
    """Prompt user for test command.

    Args:
        default: The default test command.

    Returns:
        The test command provided by the user.
    """
    return cast(str, typer.prompt("Test command", default=default))


def prompt_for_lint_command(default: str = "ruff check") -> str:
    """Prompt user for lint command.

    Args:
        default: The default lint command.

    Returns:
        The lint command provided by the user.
    """
    return cast(str, typer.prompt("Lint command", default=default))


def validate_command(command: str) -> bool:
    """Validate that a command can be executed.

    Args:
        command: The command to validate.

    Returns:
        True if the command can be executed.
    """
    try:
        # Try to run the command with --help or --version first
        cmd_parts = command.split()
        help_cmd = cmd_parts + ["--help"]
        subprocess.run(
            help_cmd,
            capture_output=True,
            timeout=5,
            check=False,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def create_default_config(
    project_root: Path,
    project_name: str,
    stealth: bool = False,
    test_command: str | None = None,
    lint_command: str | None = None,
) -> Path:
    """Create the default configuration file.

    Args:
        project_root: The project root directory.
        project_name: The project name.
        stealth: If True, use stealth mode paths.
        test_command: Custom test command (from interactive mode).
        lint_command: Custom lint command (from interactive mode).

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
            "test": test_command or config.commands.test,
            "lint": lint_command or config.commands.lint,
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


def update_gitignore(project_root: Path) -> bool:
    """Add jiro-specific entries to .gitignore.

    Args:
        project_root: The project root directory.

    Returns:
        True if gitignore was updated, False if entries already exist.
    """
    gitignore_path = project_root / ".gitignore"
    entries_to_add = [
        "# jiro-dreams-of-code",
        ".jiro-dreams-of-code/.beads/",
        ".jiro-dreams-of-code/jiro.db",
        ".jiro-dreams-of-code/logs/",
    ]

    # Read existing content
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()

    # Check if already configured (either specific entries or entire directory)
    if ".jiro-dreams-of-code/.beads/" in existing_content:
        return False
    if ".jiro-dreams-of-code/" in existing_content:
        return False  # Entire directory is already ignored

    # Append entries
    with open(gitignore_path, "a") as f:
        if existing_content and not existing_content.endswith("\n"):
            f.write("\n")
        f.write("\n".join(entries_to_add) + "\n")

    return True


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

    # Interactive mode: prompt for test and lint commands
    test_command = None
    lint_command = None

    if interactive:
        console.print("\n[cyan]Interactive Configuration[/cyan]")
        test_command = prompt_for_test_command()
        console.print(f"[dim]Test command: {test_command}[/dim]")

        lint_command = prompt_for_lint_command()
        console.print(f"[dim]Lint command: {lint_command}[/dim]")

    # Create config file with prompted commands (if any)
    config_path = create_default_config(
        project_root,
        project_name,
        stealth=stealth,
        test_command=test_command,
        lint_command=lint_command,
    )
    console.print(f"[green]✓[/green] Created config: {config_path}")

    # Initialize beads
    if initialize_beads(project_root, project_name, stealth=stealth):
        console.print("[green]✓[/green] Initialized beads database")
    else:
        console.print("[yellow]![/yellow] Beads database not initialized (manual setup required)")

    # Update .gitignore (only in normal mode - stealth mode doesn't need it)
    if not stealth:
        if update_gitignore(project_root):
            console.print("[green]✓[/green] Updated .gitignore")
        else:
            console.print("[dim]·[/dim] .gitignore already configured")

    console.print("\n[green]Initialization complete![/green]")
    return True


@app.callback(invoke_without_command=True)
def init_callback(
    ctx: typer.Context,
    stealth: Annotated[
        bool,
        typer.Option(
            "--stealth",
            help="Store all files in ~/.jiro-dreams-of-code/$PROJECT_NAME/ instead of project root",
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", help="Prompt for test command, lint command, etc."),
    ] = False,
) -> None:
    """
    Initialize jiro in the current project.

    Creates project configuration and beads database.
    Must be run inside a git repository.

    Examples:
        jiro init
        jiro init --stealth
        jiro init --interactive
    """
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()

    try:
        run_init(project_root, stealth=stealth, interactive=interactive)
    except InitError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
