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
from jiro.cli.doctor import fix_missing_config, run_doctor
from jiro.cli.dream import app as dream_app
from jiro.cli.execute import app as execute_app
from jiro.cli.init import app as init_app
from jiro.cli.logs import app as logs_app
from jiro.cli.mode import app as mode_app
from jiro.cli.plan import app as plan_app
from jiro.cli.status import app as status_app
from jiro.cli.tasks import app as tasks_app
from jiro.cli.web import app as web_app
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

        # Fix missing config
        config_created = fix_missing_config(project_root, project_root.name)
        if config_created:
            config_path = project_root / ".jiro-dreams-of-code" / "config.yaml"
            console.print(f"[green]Created config file:[/green] {config_path}")

        if not config_created:
            console.print("[yellow]No fixable issues found[/yellow]")

    # Exit with error code if checks failed
    if not doctor_result.passed:
        console.print(
            "\n[red]Some checks failed. Run with --fix to attempt auto-remediation.[/red]"
        )
        raise typer.Exit(code=1)


# Wire dream subcommand from dream module
app.add_typer(dream_app, name="dream")

# Wire plan subcommand from plan module
app.add_typer(plan_app, name="plan")

# Wire tasks subcommand from tasks module
app.add_typer(tasks_app, name="tasks")

# Wire status subcommand from status module
app.add_typer(status_app, name="status")

# Wire config subcommand from config module
app.add_typer(config_app, name="config")

# Wire init subcommand from init module
app.add_typer(init_app, name="init")

# Wire execute subcommand from execute module
app.add_typer(execute_app, name="execute")

# Wire mode subcommand from mode module
app.add_typer(mode_app, name="mode")


# Wire logs subcommand from logs module
app.add_typer(logs_app, name="logs")

# Wire web subcommand from web module
app.add_typer(web_app, name="web")

# Wire assets subcommand from assets module
app.add_typer(assets_app, name="assets")


if __name__ == "__main__":
    app()
