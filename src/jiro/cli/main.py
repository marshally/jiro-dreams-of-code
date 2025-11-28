"""Main CLI entry point for jiro-dreams-of-code."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from jiro import __version__

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
        Optional[bool],
        typer.Option("--version", callback=version_callback, help="Show version and exit"),
    ] = None,
) -> None:
    """jiro-dreams-of-code: Build software with discipline and craft."""
    pass


@app.command()
def init(
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
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will:")
    console.print("  - Verify git repository")
    console.print("  - Create .jiro-dreams-of-code/ directory (or stealth equivalent)")
    console.print("  - Initialize beads database")
    console.print("  - Create default configuration")
    if interactive:
        console.print("  - Prompt for test and lint commands")


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
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will check:")
    console.print("  - Python version (3.12+)")
    console.print("  - Claude Agent SDK installed")
    console.print("  - Anthropic API key configured")
    console.print("  - Git available")
    console.print("  - Test and lint commands work")
    console.print("  - Beads database accessible")
    if fix:
        console.print("\n[green]With --fix:[/green] Will attempt to create missing directories and fix issues")


@app.command()
def dream(
    prompt: Annotated[str, typer.Argument(help="Natural language description of what to build")],
    model: Annotated[
        Optional[str], typer.Option("--model", help="Override the model for this operation")
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
    refinement: Annotated[
        Optional[str], typer.Argument(help="Optional refinement prompt")
    ] = None,
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


# Create tasks subcommand group
tasks_app = typer.Typer(
    name="tasks",
    help="Manage and view tasks in the issue tracker",
    no_args_is_help=True,
)
app.add_typer(tasks_app, name="tasks")


@tasks_app.command("list")
def tasks_list(
    status: Annotated[
        Optional[str],
        typer.Option("--status", "-s", help="Filter by status (open, in_progress, closed, blocked)"),
    ] = None,
    epic: Annotated[
        Optional[str], typer.Option("--epic", "-e", help="Filter by epic ID")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    List all tasks with optional filters.

    Shows tasks grouped by epic and status.

    Examples:
        jiro tasks list
        jiro tasks list --status pending --epic JIRO-42
        jiro tasks list --json
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will display all tasks")
    if status:
        console.print(f"  - Filtered by status: {status}")
    if epic:
        console.print(f"  - Filtered by epic: {epic}")
    if json_output:
        console.print("  - Output format: JSON")
    elif toon:
        console.print("  - Output format: TOON")
    else:
        console.print("  - Output format: Human-readable (default)")


@tasks_app.command("show")
def tasks_show(
    task_id: Annotated[str, typer.Argument(help="Task ID to show")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show detailed information about a specific task.

    Displays full task details including description, dependencies,
    acceptance criteria, and execution history.

    Examples:
        jiro tasks show JIRO-15
        jiro tasks show JIRO-15 --json
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nTask ID: {task_id}")
    console.print("\nThis command will display full task details")


@tasks_app.command("next")
def tasks_next(
    epic: Annotated[
        Optional[str], typer.Option("--epic", "-e", help="Filter by epic ID")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show the next task to be executed.

    Displays the next task that is ready to work on (no blockers).

    Examples:
        jiro tasks next
        jiro tasks next --epic JIRO-42
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will show the next ready task")
    if epic:
        console.print(f"  - Filtered by epic: {epic}")


@app.command()
def execute(
    epic: Annotated[
        Optional[str], typer.Option("--epic", help="Limit execution to a specific epic")
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


@app.command()
def status(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    toon: Annotated[bool, typer.Option("--toon", help="Output as TOON format")] = False,
) -> None:
    """
    Show status of all active sessions for this project.

    Displays running sessions, current task, progress, and context usage.

    Examples:
        jiro status
        jiro status --json
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will display active session status")


# Create config subcommand group
config_app = typer.Typer(
    name="config",
    help="Get/set configuration values",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@config_app.command("list")
def config_list(
    global_config: Annotated[bool, typer.Option("--global", help="Show global config")] = False,
    project: Annotated[bool, typer.Option("--project", help="Show project config")] = False,
    local: Annotated[bool, typer.Option("--local", help="Show local config")] = False,
) -> None:
    """
    List all configuration values.

    Shows effective configuration with source scope.

    Examples:
        jiro config list
        jiro config list --global
        jiro config list --project
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will list configuration values")


@config_app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Configuration key (e.g., commands.test)")],
) -> None:
    """
    Get a configuration value.

    Shows the effective value and which scope it comes from.

    Examples:
        jiro config get commands.test
        jiro config get models.execution
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nKey: {key}")
    console.print("\nThis command will show the effective configuration value")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
    global_config: Annotated[bool, typer.Option("--global", help="Set in global config")] = False,
    project: Annotated[bool, typer.Option("--project", help="Set in project config")] = False,
    local: Annotated[bool, typer.Option("--local", help="Set in local config")] = False,
) -> None:
    """
    Set a configuration value.

    Examples:
        jiro config set commands.test "pytest" --local
        jiro config set models.execution "claude-sonnet-4-5-20250929" --global
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nKey: {key}")
    console.print(f"Value: {value}")
    if global_config:
        console.print("Scope: global")
    elif project:
        console.print("Scope: project")
    elif local:
        console.print("Scope: local")
    else:
        console.print("Scope: (will determine automatically)")


@app.command()
def mode(
    target_mode: Annotated[
        Optional[str], typer.Argument(help="Mode to switch to: stealth or local")
    ] = None,
) -> None:
    """
    View or switch between stealth and local modes.

    Stealth mode stores all data in ~/.jiro-dreams-of-code/$PROJECT_NAME/
    Local mode stores data in .jiro-dreams-of-code/ in project root

    Examples:
        jiro mode              # Show current mode
        jiro mode stealth      # Switch to stealth mode
        jiro mode local        # Switch to local mode
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    if target_mode:
        console.print(f"\nSwitching to {target_mode} mode")
        console.print("This will migrate all data")
    else:
        console.print("\nCurrent mode: (not yet implemented)")


@app.command()
def logs(
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow log output")] = False,
    tail: Annotated[
        Optional[int], typer.Option("--tail", "-n", help="Show last N lines")
    ] = None,
) -> None:
    """
    View logs with filtering options.

    Examples:
        jiro logs
        jiro logs --follow
        jiro logs --tail 100
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will display logs")
    if follow:
        console.print("  - Following output")
    if tail:
        console.print(f"  - Showing last {tail} lines")


@app.command()
def web(
    daemon: Annotated[
        bool, typer.Option("--daemon", help="Run web UI in background")
    ] = False,
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


# Create assets subcommand group
assets_app = typer.Typer(
    name="assets",
    help="Manage customizable assets (prompts and templates)",
    no_args_is_help=True,
)
app.add_typer(assets_app, name="assets")


@assets_app.command("list")
def assets_list() -> None:
    """
    List all assets and their source locations.

    Shows which assets are loaded from package defaults vs. user overrides.

    Examples:
        jiro assets list
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print("\nThis command will list all available assets and their sources")


@assets_app.command("which")
def assets_which(
    asset_path: Annotated[
        str, typer.Argument(help="Asset path (e.g., prompts/execution_agent.md)")
    ],
) -> None:
    """
    Show where a specific asset is loaded from.

    Examples:
        jiro assets which prompts/execution_agent.md
        jiro assets which templates/commit/default.txt
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nAsset: {asset_path}")
    console.print("\nThis command will show the source location for this asset")


@assets_app.command("customize")
def assets_customize(
    asset_path: Annotated[str, typer.Argument(help="Asset path to customize")],
    global_config: Annotated[
        bool, typer.Option("--global", help="Copy to global assets")
    ] = False,
    project: Annotated[
        bool, typer.Option("--project", help="Copy to project assets")
    ] = False,
    local: Annotated[bool, typer.Option("--local", help="Copy to local assets")] = True,
) -> None:
    """
    Copy package default asset to specified location for customization.

    Examples:
        jiro assets customize prompts/execution_agent.md --local
        jiro assets customize templates/commit/default.txt --global
    """
    console.print("[yellow]Not implemented yet[/yellow]")
    console.print(f"\nAsset: {asset_path}")
    if global_config:
        console.print("Copying to: global assets")
    elif project:
        console.print("Copying to: project assets")
    else:
        console.print("Copying to: local assets")


if __name__ == "__main__":
    app()
