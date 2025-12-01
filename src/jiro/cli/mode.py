"""Mode command for switching between stealth and local modes."""

import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from jiro.core.paths import JIRO_DIR_NAME

app = typer.Typer(
    name="mode",
    help="View or switch between stealth and local modes",
    no_args_is_help=False,
)

console = Console()


def _get_current_mode(project_root: Path, project_name: str | None = None) -> str | None:
    """Determine current mode by checking which directory exists.

    Args:
        project_root: The root directory of the project.
        project_name: The project name (defaults to directory name).

    Returns:
        "local", "stealth", or None if no mode is active.
    """
    if project_name is None:
        project_name = project_root.name

    # Check if local directory exists
    local_dir = project_root / JIRO_DIR_NAME
    if local_dir.exists():
        return "local"

    # Check if stealth directory exists
    stealth_dir = Path.home() / JIRO_DIR_NAME / project_name
    if stealth_dir.exists():
        return "stealth"

    return None


def _migrate_data(source: Path, destination: Path) -> None:
    """Migrate data from source directory to destination.

    Args:
        source: Source directory path.
        destination: Destination directory path.
    """
    # Create parent directories if they don't exist
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Copy all files from source to destination
    shutil.copytree(source, destination, dirs_exist_ok=True)

    # Remove the source directory after successful copy
    shutil.rmtree(source)


@app.callback(invoke_without_command=True)
def mode_callback(ctx: typer.Context) -> None:
    """Callback to handle mode command without subcommands."""
    # If no command was invoked, show current mode
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()
    project_name = project_root.name

    current_mode = _get_current_mode(project_root, project_name)
    if current_mode:
        console.print(f"[cyan]Current mode: {current_mode}[/cyan]")
    else:
        console.print("[yellow]No mode is currently active[/yellow]")


@app.command("stealth")
def switch_to_stealth(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt and perform migration"),
    ] = False,
) -> None:
    """
    Switch to stealth mode.

    Stealth mode stores all data in ~/.jiro-dreams-of-code/$PROJECT_NAME/

    Examples:
        jiro mode stealth
        jiro mode stealth --yes
    """
    project_root = Path.cwd()
    project_name = project_root.name

    # Get current mode
    current_mode = _get_current_mode(project_root, project_name)

    # Check if already in target mode
    if current_mode == "stealth":
        console.print("[yellow]Already in stealth mode[/yellow]")
        return

    # Determine source and destination directories
    local_dir = project_root / JIRO_DIR_NAME
    stealth_dir = Path.home() / JIRO_DIR_NAME / project_name

    source = local_dir
    destination = stealth_dir

    # Check if source exists
    if not source.exists():
        console.print("[yellow]No data to migrate (source not found)[/yellow]")
        return

    # Get confirmation if not using --yes flag
    if not yes:
        console.print("[cyan]Migration Details:[/cyan]")
        console.print(f"  From: {source}")
        console.print(f"  To: {destination}")
        console.print("[yellow]This will migrate all data from local to stealth mode.[/yellow]")

        # Prompt for confirmation
        try:
            confirm = typer.confirm("Continue with migration?")
        except typer.Abort:
            console.print("[yellow]Migration cancelled[/yellow]")
            return

        if not confirm:
            console.print("[yellow]Migration cancelled[/yellow]")
            return

    # Perform migration
    try:
        _migrate_data(source, destination)
        console.print("[green]Successfully migrated to stealth mode[/green]")
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error during migration: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@app.command("local")
def switch_to_local(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt and perform migration"),
    ] = False,
) -> None:
    """
    Switch to local mode.

    Local mode stores data in .jiro-dreams-of-code/ in project root

    Examples:
        jiro mode local
        jiro mode local --yes
    """
    project_root = Path.cwd()
    project_name = project_root.name

    # Get current mode
    current_mode = _get_current_mode(project_root, project_name)

    # Check if already in target mode
    if current_mode == "local":
        console.print("[yellow]Already in local mode[/yellow]")
        return

    # Determine source and destination directories
    local_dir = project_root / JIRO_DIR_NAME
    stealth_dir = Path.home() / JIRO_DIR_NAME / project_name

    source = stealth_dir
    destination = local_dir

    # Check if source exists
    if not source.exists():
        console.print("[yellow]No data to migrate (source not found)[/yellow]")
        return

    # Get confirmation if not using --yes flag
    if not yes:
        console.print("[cyan]Migration Details:[/cyan]")
        console.print(f"  From: {source}")
        console.print(f"  To: {destination}")
        console.print("[yellow]This will migrate all data from stealth to local mode.[/yellow]")

        # Prompt for confirmation
        try:
            confirm = typer.confirm("Continue with migration?")
        except typer.Abort:
            console.print("[yellow]Migration cancelled[/yellow]")
            return

        if not confirm:
            console.print("[yellow]Migration cancelled[/yellow]")
            return

    # Perform migration
    try:
        _migrate_data(source, destination)
        console.print("[green]Successfully migrated to local mode[/green]")
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error during migration: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
