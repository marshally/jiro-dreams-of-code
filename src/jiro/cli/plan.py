"""Plan command implementation for spec planning and task creation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jiro.agents.base import AgentConfig
from jiro.agents.client import AgentClient
from jiro.config.loader import load_config
from jiro.core.infrastructure import BootstrapTaskGenerator, ProjectInspector
from jiro.core.paths import get_database_path, get_specs_dir
from jiro.core.planner import PlanResult, SpecPlanner, create_tasks, parse_spec
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import PromptRepository
from jiro.trackers.beads import BeadsTracker

app = typer.Typer(
    name="plan",
    help="Parse spec and generate epics + tasks",
    no_args_is_help=False,
)

console = Console()


def _find_most_recent_spec(specs_dir: Path) -> Path | None:
    """Find the most recently modified spec file in the specs directory.

    Args:
        specs_dir: Directory containing spec files.

    Returns:
        Path to the most recent spec file, or None if no specs exist.
    """
    if not specs_dir.exists():
        return None

    spec_files = list(specs_dir.glob("*.md"))
    if not spec_files:
        return None

    # Sort by modification time, most recent first
    spec_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return spec_files[0]


def _display_plan_summary(plan_result: PlanResult) -> None:
    """Display plan summary using Rich formatting.

    Args:
        plan_result: The PlanResult object containing epics, tasks, and dependencies.
    """
    # Create epics table
    epics_table = Table(title="Epics")
    epics_table.add_column("ID", style="cyan")
    epics_table.add_column("Name", style="green")
    epics_table.add_column("Description", style="yellow")
    epics_table.add_column("Task Count", style="magenta")

    for epic in plan_result.epics:
        epics_table.add_row(epic.id, epic.name, epic.description, str(len(epic.tasks)))

    console.print(epics_table)

    # Create tasks table
    tasks_table = Table(title="Tasks")
    tasks_table.add_column("ID", style="cyan")
    tasks_table.add_column("Title", style="green")
    tasks_table.add_column("Epic", style="blue")
    tasks_table.add_column("Dependencies", style="yellow")

    for task in plan_result.tasks:
        deps_str = ", ".join(task.dependencies) if task.dependencies else "None"
        tasks_table.add_row(task.id, task.title, task.epic_id, deps_str)

    console.print(tasks_table)

    # Display dependencies summary
    if plan_result.dependencies:
        deps_table = Table(title="Dependencies")
        deps_table.add_column("From", style="cyan")
        deps_table.add_column("To", style="green")

        for dep in plan_result.dependencies:
            deps_table.add_row(dep.get("from", ""), dep.get("to", ""))

        console.print(deps_table)

    # Summary panel
    summary_text = f"""
Plan Summary:
- Epics: {len(plan_result.epics)}
- Tasks: {len(plan_result.tasks)}
- Dependencies: {len(plan_result.dependencies)}
"""
    panel = Panel(summary_text.strip(), title="Plan Overview", border_style="blue")
    console.print(panel)


def _detect_and_suggest_bootstrap_tasks(
    project_root: Path,
    tracker: BeadsTracker,
) -> bool:
    """Detect missing infrastructure and offer to create bootstrap tasks.

    Args:
        project_root: The project root directory.
        tracker: The issue tracker.

    Returns:
        True if user wants to continue with planning, False to cancel.
    """
    inspector = ProjectInspector(project_root)
    analysis = inspector.analyze()

    if not analysis.missing_components:
        console.print("[green]✓ Project infrastructure is complete[/green]")
        return True

    # Display detected infrastructure
    console.print("\n[bold blue]Infrastructure Detection[/bold blue]\n")

    if analysis.languages:
        console.print("[cyan]Detected Languages:[/cyan]")
        for lang in analysis.languages:
            pm = f" ({lang.package_manager})" if lang.package_manager else ""
            console.print(f"  - {lang.name}{pm}")

    if analysis.frameworks:
        console.print("[cyan]Detected Frameworks:[/cyan]")
        for fw in analysis.frameworks:
            console.print(f"  - {fw.name}")

    if analysis.tools:
        console.print("[cyan]Detected Tools:[/cyan]")
        for tool in analysis.tools:
            console.print(f"  - {tool.name} ({tool.category})")

    # Display missing components
    console.print("\n[yellow]Missing Infrastructure Components:[/yellow]")
    for component in analysis.missing_components:
        console.print(f"  - {component}")

    # Offer to create bootstrap tasks
    console.print("\n[yellow]jiro can create bootstrap tasks to set up missing infrastructure.[/yellow]")
    create_bootstrap: bool = typer.confirm(
        "Would you like to create bootstrap tasks for missing infrastructure?",
        default=True,
    )

    if create_bootstrap:
        generator = BootstrapTaskGenerator(analysis)
        bootstrap_tasks = generator.generate_tasks()

        if bootstrap_tasks:
            # Create an infrastructure epic if not exists
            bootstrap_epic = tracker.create_task(
                title="Project Infrastructure",
                description="Bootstrap tasks for setting up project infrastructure",
                task_type="epic",
            )

            # Create bootstrap tasks
            created_count = 0
            for task_data in bootstrap_tasks:
                try:
                    _ = tracker.create_task(
                        title=task_data["title"],
                        description=task_data["description"],
                        task_type="task",
                        epic_id=bootstrap_epic.id,
                        design=task_data.get("design"),
                        acceptance=task_data.get("acceptance"),
                    )
                    created_count += 1
                except Exception as e:
                    console.print(f"[red]Error creating bootstrap task: {e}[/red]")

            console.print(f"\n[green]Created {created_count} bootstrap tasks[/green]")

            # Ask if user wants to proceed with feature planning
            console.print("\n[yellow]Bootstrap tasks have been created.[/yellow]")
            proceed: bool = typer.confirm(
                "Do you want to proceed with planning the feature specification?",
                default=True,
            )
            return proceed

    return True


async def _run_plan(
    spec_file: str,
    model: str | None = None,
    project_root: Path | None = None,
) -> None:
    """Run the plan command asynchronously.

    Args:
        spec_file: Path to the specification file.
        model: Optional model override.
        project_root: The project root directory.
    """
    if project_root is None:
        project_root = Path.cwd()

    spec_path = Path(spec_file)
    if not spec_path.is_absolute():
        spec_path = project_root / spec_path

    # Get project name
    project_name = project_root.name

    # Load configuration
    config = load_config(project_root, project_name)

    # Get database
    db_path = get_database_path(project_root, stealth=False, project_name=project_name)
    db = get_database(db_path)
    ensure_schema(db)

    # Create repository
    repository = PromptRepository(db)

    # Create tracker for infrastructure detection
    tracker = BeadsTracker(project_root, stealth=False, project_name=project_name)

    # Check if beads is initialized
    if not tracker.beads_dir.exists():
        console.print("[red]Error: jiro has not been initialized in this project.[/red]")
        console.print("[dim]Run 'jiro init' first to set up the project.[/dim]")
        return

    # Detect infrastructure and offer bootstrap tasks
    console.print("[cyan]Analyzing project infrastructure...[/cyan]\n")
    if not _detect_and_suggest_bootstrap_tasks(project_root, tracker):
        console.print("[yellow]Plan cancelled.[/yellow]")
        return

    # Create agent config
    model_to_use = model or config.models.planning
    agent_config = AgentConfig(
        model=model_to_use,
        system_prompt="You are an expert software architect. Decompose specifications into epics, tasks, and dependencies.",
    )

    # Create client and planner
    client = AgentClient(agent_config, repository)
    planner = SpecPlanner(client)

    # Parse spec file
    console.print("[cyan]Parsing specification...[/cyan]")
    spec = parse_spec(spec_path)

    # Run planning
    console.print("[cyan]Running planning agent...[/cyan]")
    plan_result = await planner.plan(spec)

    # Display plan summary
    console.print("\n[bold blue]Plan Result[/bold blue]\n")
    _display_plan_summary(plan_result)

    # Confirmation prompt
    console.print("\n[yellow]Review the plan above.[/yellow]")
    proceed = typer.confirm("Proceed with creating tasks?", default=False)

    if not proceed:
        console.print("[yellow]Plan cancelled.[/yellow]")
        return

    # Create tasks in tracker
    console.print("[cyan]Creating tasks in tracker...[/cyan]")
    created_tasks = create_tasks(plan_result, tracker)

    console.print(f"\n[green]Created {len(created_tasks)} tasks:[/green]")
    for task in created_tasks:
        console.print(f"  - {task.id}: {task.title}")


@app.callback(invoke_without_command=True)
def plan_callback(
    ctx: typer.Context,
    spec: Annotated[str | None, typer.Option("--spec", help="Path to specification file")] = None,
    model: Annotated[
        str | None, typer.Option("--model", help="Override the model for this operation")
    ] = None,
) -> None:
    """
    Parse spec and generate epics + tasks.

    Analyzes dependencies between tasks and prompts for confirmation
    before creating tasks in the issue tracker.

    If --spec is not provided, uses the most recently modified spec file.

    Examples:
        jiro plan                                        # Use most recent spec
        jiro plan --spec specs/auth-system.md
        jiro plan --spec specs/auth-system.md --model claude-opus-4
    """
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()
    project_name = project_root.name

    # If no spec provided, find the most recent one
    spec_file = spec
    if spec_file is None:
        specs_dir = get_specs_dir(project_root, stealth=False, project_name=project_name)
        recent_spec = _find_most_recent_spec(specs_dir)
        if recent_spec is None:
            console.print("[red]Error: No spec files found.[/red]")
            console.print("[dim]Run 'jiro dream' to create a specification first.[/dim]")
            raise typer.Exit(code=1)
        spec_file = str(recent_spec)
        console.print(f"[cyan]Using most recent spec:[/cyan] {recent_spec.name}")

    try:
        # Run the async plan function
        asyncio.run(_run_plan(spec_file, model, project_root))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
