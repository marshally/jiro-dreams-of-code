"""Dream command implementation for spec generation."""

import asyncio
import io
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
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


@contextmanager
def _suppress_structlog_output() -> Generator[None, None, None]:
    """Context manager to suppress structlog JSON output to stdout."""
    # Capture stdout to suppress JSON log output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


@contextmanager
def _enhanced_keyboard_mode() -> Generator[None, None, None]:
    """Enable modifyOtherKeys mode for enhanced keyboard input.

    This allows the terminal to send distinct escape sequences for modified keys
    like Shift+Enter, without requiring manual terminal configuration.

    Uses level 1 (not level 2) to preserve Ctrl+C and Ctrl+D behavior.
    Level 1 only modifies keys that produce characters, leaving control
    sequences intact.

    Reference: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
    """
    # Enable modifyOtherKeys level 1 (character keys only, preserves Ctrl+C/D)
    # CSI > 4 ; 1 m
    sys.stderr.write("\x1b[>4;1m")
    sys.stderr.flush()
    try:
        yield
    finally:
        # Disable modifyOtherKeys
        # CSI > 4 ; 0 m
        sys.stderr.write("\x1b[>4;0m")
        sys.stderr.flush()


# Thinking indicator messages (similar to Claude Code)
THINKING_MESSAGES = [
    "Contemplating…",
    "Dreaming…",
    "Pondering…",
    "Envisioning…",
    "Imagining…",
]


def _get_thinking_message() -> str:
    """Get a random thinking message."""
    import random

    return random.choice(THINKING_MESSAGES)


def _create_multiline_session() -> PromptSession[str]:
    """Create a prompt_toolkit session with multiline support.

    When used with _enhanced_keyboard_mode() context manager:
    - Enter submits
    - Shift+Enter adds a new line

    Fallback (terminals that don't support modifyOtherKeys):
    - Enter submits
    - Meta+Enter (Alt+Enter / Option+Enter) adds a new line

    Returns:
        A configured PromptSession for multiline input.
    """
    from prompt_toolkit.keys import Keys

    bindings = KeyBindings()

    # Enter submits (override default multiline behavior)
    @bindings.add("enter")
    def _submit_on_enter(event: object) -> None:
        """Submit input when Enter is pressed."""
        from prompt_toolkit.buffer import Buffer

        if hasattr(event, "current_buffer"):
            buffer: Buffer = event.current_buffer
            buffer.validate_and_handle()

    # CSI u protocol: ESC [ 13 ; 2 u = Shift+Enter
    # This handles terminals configured to send CSI u sequences
    # The sequence arrives as: ESC [ 1 3 ; 2 u
    @bindings.add(Keys.Escape, "[", "1", "3", ";", "2", "u")
    def _insert_newline_csi_u(event: object) -> None:
        """Insert newline when Shift+Enter via CSI u is received."""
        from prompt_toolkit.buffer import Buffer

        if hasattr(event, "current_buffer"):
            buffer: Buffer = event.current_buffer
            buffer.insert_text("\n")

    # Ghostty's modifyOtherKeys format: ESC [ 27 ; 2 ; 13 ~
    @bindings.add(Keys.Escape, "[", "2", "7", ";", "2", ";", "1", "3", "~")
    def _insert_newline_modify_other_keys(event: object) -> None:
        """Insert newline when Shift+Enter via modifyOtherKeys is received."""
        from prompt_toolkit.buffer import Buffer

        if hasattr(event, "current_buffer"):
            buffer: Buffer = event.current_buffer
            buffer.insert_text("\n")

    # Meta+Enter (Escape+Enter) inserts newline (fallback for unconfigured terminals)
    @bindings.add("escape", "enter")
    def _insert_newline_meta_enter(event: object) -> None:
        """Insert newline when Meta+Enter is pressed."""
        from prompt_toolkit.buffer import Buffer

        if hasattr(event, "current_buffer"):
            buffer: Buffer = event.current_buffer
            buffer.insert_text("\n")

    return PromptSession(
        multiline=True,
        key_bindings=bindings,
    )


app = typer.Typer(
    name="dream",
    help="Generate specifications from natural language",
    no_args_is_help=False,
)

# Use stderr for Rich output so we can suppress stdout (JSON logs) independently
console = Console(stderr=True)


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


async def _run_interactive_dream(
    model: str | None = None,
    project_root: Path | None = None,
    debug: bool = False,
) -> None:
    """Run interactive dream mode with question-by-question interview.

    Args:
        model: Optional model override.
        project_root: The project root directory.
        debug: If True, show JSON log output.
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
        system_prompt="You are an expert software architect conducting an interview to understand requirements.",
    )

    # Create client and agent
    client = AgentClient(agent_config, repository)
    agent = DreamingAgent(client)

    # Welcome message
    console.print("[cyan]Interactive Spec Generation[/cyan]")
    console.print("I'll ask questions to understand what you want to build.\n")
    console.print("[dim]Enter to submit. Shift+Enter for a newline.[/dim]")
    console.print("[dim]Type 'quit', 'exit', or '/quit' to cancel[/dim]\n")

    # Create multiline input session
    session = _create_multiline_session()

    async def get_input() -> str:
        result: str = await session.prompt_async("> ")
        return result.strip()

    def display_message(message: str) -> None:
        console.print("\n[blue]Agent:[/blue]")
        console.print(Markdown(message))
        console.print()

    # Simple text-based thinking indicator (avoids terminal state issues with Status)
    def on_thinking_start() -> None:
        console.print(f"[dim]✽ {_get_thinking_message()}[/dim]", end="\r")

    def on_thinking_end() -> None:
        # Clear the thinking line
        console.print(" " * 40, end="\r")

    # Run interview (suppress JSON logs unless debug mode)
    if debug:
        result = await agent.interview(
            get_input, display_message, on_thinking_start, on_thinking_end
        )
    else:
        with _suppress_structlog_output():
            result = await agent.interview(
                get_input, display_message, on_thinking_start, on_thinking_end
            )

    # Display generated spec
    console.print("\n")
    _display_spec(result.spec)

    # Get specs directory
    specs_dir = get_specs_dir(project_root, stealth=False, project_name=project_name)

    # Enter refinement loop (same as _run_dream)
    console.print("\n[cyan]Enter refinement chat.[/cyan]")
    console.print("[dim]Enter to submit. Shift+Enter for a newline.[/dim]")
    console.print("[dim]Commands: 'done' / 'exit' / '/quit' / Ctrl+D to save and exit[/dim]\n")

    # Create new session for refinement
    refinement_session = _create_multiline_session()

    spec = result.spec
    try:
        while True:
            try:
                feedback = (await refinement_session.prompt_async("Refinement> ")).strip()
            except EOFError:
                console.print("\n[green]Exiting...[/green]")
                break

            if feedback.lower() in ["done", "exit", "/quit", ""]:
                if feedback:
                    console.print("[green]Exiting refinement mode[/green]")
                break

            with console.status(f"[cyan]✽ {_get_thinking_message()}[/cyan]", spinner="dots"):
                if debug:
                    spec = await agent.refine(spec, feedback)
                else:
                    with _suppress_structlog_output():
                        spec = await agent.refine(spec, feedback)
            _display_spec(spec)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")

    # Save the final spec
    spec_path = _save_spec_to_file(spec, specs_dir)
    console.print(f"\n[green]Specification saved to:[/green] {spec_path}")


async def _run_dream(
    prompt: str,
    model: str | None = None,
    project_root: Path | None = None,
    debug: bool = False,
) -> None:
    """Run the dream command asynchronously.

    Args:
        prompt: The feature request prompt.
        model: Optional model override.
        project_root: The project root directory.
        debug: If True, show JSON log output.
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

    # Generate initial spec (suppress JSON logs unless debug mode)
    with console.status(f"[cyan]✽ {_get_thinking_message()}[/cyan]", spinner="dots"):
        if debug:
            spec = await agent.dream(prompt)
        else:
            with _suppress_structlog_output():
                spec = await agent.dream(prompt)

    # Display the spec
    _display_spec(spec)

    # Get specs directory
    specs_dir = get_specs_dir(project_root, stealth=False, project_name=project_name)

    # Chat refinement loop
    console.print("\n[cyan]Enter refinement chat.[/cyan]")
    console.print("[dim]Enter to submit. Shift+Enter for a newline.[/dim]")
    console.print("[dim]Commands: 'done' / 'exit' / '/quit' / Ctrl+D to save and exit[/dim]\n")

    # Create multiline session for refinement
    refinement_session = _create_multiline_session()

    try:
        while True:
            try:
                feedback = (await refinement_session.prompt_async("Refinement> ")).strip()
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
            with console.status(f"[cyan]✽ {_get_thinking_message()}[/cyan]", spinner="dots"):
                if debug:
                    spec = await agent.refine(spec, feedback)
                else:
                    with _suppress_structlog_output():
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
    prompt: Annotated[
        str | None, typer.Argument(help="Natural language description of what to build")
    ] = None,
    model: Annotated[
        str | None, typer.Option("--model", help="Override the model for this operation")
    ] = None,
    debug: Annotated[bool, typer.Option("--debug", help="Show detailed JSON logs")] = False,
) -> None:
    """
    Generate a specification from natural language.

    Run without arguments for interactive mode where the agent asks questions
    to understand requirements. Run with a prompt for direct spec generation.

    Opens interactive chat refinement mode. Saves spec to
    .jiro-dreams-of-code/specs/ (or stealth equivalent).

    Examples:
        jiro dream                                          # Interactive mode
        jiro dream "build a user authentication system"     # Direct mode
        jiro dream "add GraphQL API support" --model claude-opus-4
        jiro dream --debug                                  # Show JSON logs
    """
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()

    try:
        with _enhanced_keyboard_mode():
            if prompt is None:
                # Interactive mode - agent asks questions
                asyncio.run(_run_interactive_dream(model, project_root, debug))
            else:
                # Direct mode - generate spec from prompt
                asyncio.run(_run_dream(prompt, model, project_root, debug))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
