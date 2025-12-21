"""Shell completions management for jiro."""

from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(
    name="completions",
    help="Install and manage shell completions",
    no_args_is_help=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def completions_callback(ctx: typer.Context) -> None:
    """Show completions help when no subcommand is provided."""
    if ctx.invoked_subcommand is not None:
        return

    console.print("[cyan]Shell Completions[/cyan]")
    console.print()
    console.print("Commands:")
    console.print("  jiro completions install  Install completions for your shell")
    console.print("  jiro completions show     Show the completion script")
    console.print()
    console.print("Supported shells: bash, zsh, fish, powershell, pwsh")


@app.command("install")
def install_completion(
    shell: Annotated[
        str | None,
        typer.Option(help="Shell to install completions for (bash, zsh, fish, powershell, pwsh)"),
    ] = None,
) -> None:
    """Install shell completions for jiro."""
    # Import here to avoid loading typer internals at module level
    from typer._completion_shared import install

    try:
        shell_name, path = install(shell=shell)
        console.print(f"[green]Installed {shell_name} completion to {path}[/green]")
        console.print("Restart your terminal for completions to take effect.")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e


@app.command("show")
def show_completion(
    ctx: typer.Context,
    shell: Annotated[
        str | None,
        typer.Option(help="Shell to show completions for (bash, zsh, fish, powershell, pwsh)"),
    ] = None,
) -> None:
    """Show the completion script for a shell."""
    # Import here to avoid loading typer internals at module level
    from typer._completion_shared import get_completion_script

    try:
        prog_name = ctx.find_root().info_name or "jiro"
        complete_var = f"_{prog_name.replace('-', '_').upper()}_COMPLETE"

        script = get_completion_script(
            prog_name=prog_name,
            complete_var=complete_var,
            shell=shell,
        )
        # Print raw script without Rich formatting
        print(script)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e
