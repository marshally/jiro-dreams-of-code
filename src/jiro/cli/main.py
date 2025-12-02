"""Main CLI entry point for jiro-dreams-of-code."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro import __version__
from jiro.cli.assets import app as assets_app
from jiro.cli.config import app as config_app
from jiro.cli.doctor import fix_missing_config, fix_missing_directories, run_doctor
from jiro.cli.init import app as init_app
from jiro.cli.logs import app as logs_app
from jiro.cli.mode import app as mode_app
from jiro.cli.status import app as status_app
from jiro.cli.tasks import app as tasks_app
from jiro.core.logging import configure_logging

app = typer.Typer(
    name="jiro",
    help="A disciplined AI agent orchestration system using the shokunin philosophy",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"jiro-dreams-of-code version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, help="Show version and exit"),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            count=True,
            help="Increase verbosity level (-v for DEBUG, -vv for TRACE)",
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output (CRITICAL level only)"),
    ] = False,
) -> None:
    """jiro-dreams-of-code: Build software with discipline and craft."""
    # Determine log level based on flags
    if quiet:
        log_level = logging.CRITICAL
    elif verbose == 1:
        log_level = logging.DEBUG
    elif verbose >= 2:
        log_level = logging.DEBUG  # Both -v and -vv map to DEBUG for now
    else:
        log_level = logging.INFO

    # Initialize logging
    configure_logging(verbosity=log_level)


@app.command()
def doctor(
    fix: Annotated[
        bool, typer.Option("--fix", help="Attempt auto-remediation of fixable issues")
    ] = False,
) -> None:
    """
    Verify installation and configuration health.

    Checks Python version, dependencies, API keys, git, test/lint commands,
    database accessibility, and more.

    Examples:
        jiro doctor
        jiro doctor --fix
    """
    project_root = Path.cwd()

    # Run all health checks
    doctor_result = run_doctor(project_root)

    # Display results in a table
    table = Table(title="Health Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="yellow")

    for check_name, check_result in doctor_result.checks.items():
        status = "[green]PASS[/green]" if check_result.passed else "[red]FAIL[/red]"
        details = "" if check_result.passed else check_result.error
        table.add_row(check_name, status, details)

    console.print(table)

    # Apply fixes if requested
    if fix:
        console.print("\n[cyan]Attempting to fix issues...[/cyan]")

        # Fix missing directories
        created_dirs = fix_missing_directories(project_root)
        if created_dirs:
            console.print(f"[green]Created {len(created_dirs)} directory/directories:[/green]")
            for dir_path in created_dirs:
                console.print(f"  - {dir_path}")

        # Fix missing config
        config_created = fix_missing_config(project_root, project_root.name)
        if config_created:
            config_path = project_root / ".jiro-dreams-of-code" / "config.yaml"
            console.print(f"[green]Created config file:[/green] {config_path}")

        if not created_dirs and not config_created:
            console.print("[yellow]No fixable issues found[/yellow]")

    # Exit with error code if checks failed
    if not doctor_result.passed:
        console.print(
            "\n[red]Some checks failed. Run with --fix to attempt auto-remediation.[/red]"
        )
        raise typer.Exit(code=1)


@app.command()
def dream(
    prompt: Annotated[str, typer.Argument(help="Natural language description of what to build")],
    model: Annotated[
        str | None, typer.Option("--model", help="Override the model for this operation")
    ] = None,
) -> None:
    """
    Generate a specification from natural language.

    Opens interactive chat refinement mode. Saves spec to
    .jiro-dreams-of-code/specs/ (or stealth equivalent).

    Examples:
        jiro dream "build a user authentication system with OAuth"
        jiro dream "add GraphQL API support" --model claude-opus-4
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nPrompt: {prompt}")
    if model:
        console.print(f"Model: {model}")
    console.print("\nThis command will:")
    console.print("  - Generate initial spec from prompt")
    console.print("  - Enter interactive refinement chat")
    console.print("  - Save final spec to specs/")


@app.command()
def plan(
    spec: Annotated[str, typer.Option("--spec", help="Path to specification file")],
    refinement: Annotated[str | None, typer.Argument(help="Optional refinement prompt")] = None,
) -> None:
    """
    Parse spec and generate epics + tasks.

    Analyzes dependencies between tasks and prompts for confirmation
    before creating tasks in the issue tracker.

    Examples:
        jiro plan --spec specs/auth-system.md
        jiro plan --spec specs/auth-system.md "focus on security"
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nSpec: {spec}")
    if refinement:
        console.print(f"Refinement: {refinement}")
    console.print("\nThis command will:")
    console.print("  - Parse specification")
    console.print("  - Generate epics and tasks")
    console.print("  - Analyze dependencies")
    console.print("  - Prompt: Proceed? [yes/chat/edit/quit]")


# Wire tasks subcommand from tasks module
app.add_typer(tasks_app, name="tasks")

# Wire status subcommand from status module
app.add_typer(status_app, name="status")

# Wire config subcommand from config module
app.add_typer(config_app, name="config")

# Wire init subcommand from init module
app.add_typer(init_app, name="init")


@app.command()
def execute(
    epic: Annotated[
        str | None, typer.Option("--epic", help="Limit execution to a specific epic")
    ] = None,
) -> None:
    """
    Execute tasks with preflight and postflight checks.

    Runs session preflight, iteratively executes tasks, and runs
    session postflight. Agents work with strict TDD discipline.

    Examples:
        jiro execute
        jiro execute --epic JIRO-42
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will:")
    console.print("  - Run session preflight checks")
    console.print("  - Execute tasks iteratively")
    console.print("  - Validate commits")
    console.print("  - Run session postflight checks")
    if epic:
        console.print(f"  - Limited to epic: {epic}")


# Wire mode subcommand from mode module
app.add_typer(mode_app, name="mode")


# Wire logs subcommand from logs module
app.add_typer(logs_app, name="logs")


@app.command()
def web(
    daemon: Annotated[bool, typer.Option("--daemon", help="Run web UI in background")] = False,
    port: Annotated[int, typer.Option("--port", help="Port to run on")] = 8888,
) -> None:
    """
    Start web UI.

    Launches FastAPI server with HTMX frontend for spec refinement,
    task monitoring, and execution status.

    Examples:
        jiro web              # Run in foreground
        jiro web --daemon     # Run in background
        jiro web --port 9000  # Use custom port
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nWeb UI would start on http://localhost:{port}")
    if daemon:
        console.print("  - Running in background")
    else:
        console.print("  - Running in foreground")


# Wire assets subcommand from assets module
app.add_typer(assets_app, name="assets")


if __name__ == "__main__":
    app()
