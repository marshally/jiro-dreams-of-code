"""Dream command implementation for spec generation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from jiro.agents.client import AgentClient
from jiro.agents.dreaming import DreamingAgent
from jiro.config.loader import load_config
from jiro.core.paths import get_database_path, get_specs_dir
from jiro.core.planner import Spec
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import PromptRepository

app = typer.Typer(
    name="dream",
    help="Generate specifications from natural language",
    no_args_is_help=False,
)

console = Console()


def _save_spec_to_file(spec: Spec, specs_dir: Path) -> Path:
    """Save a specification to a markdown file.

    Args:
        spec: The Spec object to save.
        specs_dir: Directory to save the spec in.

    Returns:
        Path to the saved file.
    """
    # Create directory if it doesn't exist
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from title (lowercase, replace spaces with hyphens)
    filename = spec.title.lower().replace(" ", "-").replace("/", "-")
    filename = "".join(c for c in filename if c.isalnum() or c in "-")
    spec_path = specs_dir / f"{filename}.md"

    # Format spec as markdown
    spec_content = f"""# Feature: {spec.title}

## Overview

{spec.overview}

## Requirements

"""
    for req in spec.requirements:
        spec_content += f"- {req}\n"

    spec_content += "\n## Acceptance Criteria\n\n"
    for criteria in spec.acceptance_criteria:
        spec_content += f"- {criteria}\n"

    spec_content += "\n## Out of Scope\n\n"
    for item in spec.out_of_scope:
        spec_content += f"- {item}\n"

    if spec.technical_notes:
        spec_content += f"\n## Technical Notes\n\n{spec.technical_notes}\n"

    # Write to file
    with open(spec_path, "w") as f:
        f.write(spec_content)

    return spec_path


def _display_spec(spec: Spec) -> None:
    """Display a specification using Rich formatting.

    Args:
        spec: The Spec object to display.
    """
    # Create markdown representation
    spec_md = f"""# {spec.title}

## Overview

{spec.overview}

## Requirements

"""
    for req in spec.requirements:
        spec_md += f"- {req}\n"

    spec_md += "\n## Acceptance Criteria\n\n"
    for criteria in spec.acceptance_criteria:
        spec_md += f"- {criteria}\n"

    spec_md += "\n## Out of Scope\n\n"
    for item in spec.out_of_scope:
        spec_md += f"- {item}\n"

    if spec.technical_notes:
        spec_md += f"\n## Technical Notes\n\n{spec.technical_notes}\n"

    # Display with Rich
    panel = Panel(
        Markdown(spec_md),
        title="Generated Specification",
        border_style="blue",
    )
    console.print(panel)


async def _run_dream(
    prompt: str,
    model: str | None = None,
    project_root: Path | None = None,
) -> None:
    """Run the dream command asynchronously.

    Args:
        prompt: The feature request prompt.
        model: Optional model override.
        project_root: The project root directory.
    """
    if project_root is None:
        project_root = Path.cwd()

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

    # Create agent config
    from jiro.agents.base import AgentConfig

    model_to_use = model or config.models.planning
    agent_config = AgentConfig(
        model=model_to_use,
        system_prompt="You are an expert software architect. Generate clear, detailed feature specifications.",
    )

    # Create client and agent
    client = AgentClient(agent_config, repository)
    agent = DreamingAgent(client)

    # Generate initial spec
    console.print("[cyan]Generating initial specification...[/cyan]")
    spec = await agent.dream(prompt)

    # Display the spec
    _display_spec(spec)

    # Get specs directory
    specs_dir = get_specs_dir(project_root, stealth=False, project_name=project_name)

    # Chat refinement loop
    console.print(
        "\n[cyan]Enter refinement chat. Commands: 'done' / 'exit' / '/quit' / Ctrl+D to save and exit[/cyan]\n"
    )

    try:
        while True:
            try:
                feedback = input("[yellow]Refinement:[/yellow] ").strip()
            except EOFError:
                # Ctrl+D was pressed
                console.print("\n[green]Exiting...[/green]")
                break

            # Check for exit commands
            if feedback.lower() in ["done", "exit", "/quit", ""]:
                if feedback:
                    console.print("[green]Exiting refinement mode[/green]")
                break

            # Refine the spec based on feedback
            console.print("[cyan]Refining specification...[/cyan]")
            spec = await agent.refine(spec, feedback)

            # Display updated spec
            _display_spec(spec)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")

    # Save the final spec
    spec_path = _save_spec_to_file(spec, specs_dir)
    console.print(f"\n[green]Specification saved to:[/green] {spec_path}")


@app.callback(invoke_without_command=True)
def dream_callback(
    ctx: typer.Context,
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
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()

    try:
        # Run the async dream function
        asyncio.run(_run_dream(prompt, model, project_root))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
