"""Authentication commands for managing API keys securely."""

from typing import Annotated

import typer
from rich.console import Console

from jiro.auth.manager import (
    get_api_key,
    is_key_stored,
    remove_api_key,
    store_api_key,
)

app = typer.Typer(
    name="auth",
    help="Manage API keys securely",
    no_args_is_help=True,
)

console = Console()


@app.command()
def login(
    api_key: Annotated[
        str | None,
        typer.Option(
            "--key",
            "-k",
            prompt=False,
            hide_input=True,
            help="API key (prompted if not provided)",
        ),
    ] = None,
) -> None:
    """Store API key in system keyring.

    Prompts for the API key if not provided via --key option.
    The key is securely stored in the system keyring (Keychain on macOS,
    Credential Manager on Windows, Secret Service on Linux).

    Examples:
        jiro auth login
        jiro auth login --key sk-proj-...
    """
    try:
        # Prompt for key if not provided
        if api_key is None:
            api_key = typer.prompt("Enter your Anthropic API key", hide_input=True)

        if not api_key or not api_key.strip():
            console.print("[red]Error: API key cannot be empty[/red]")
            raise typer.Exit(code=1)

        # Try to store the key
        success = store_api_key(api_key)

        if success:
            console.print("[green]API key stored securely in system keyring[/green]")
        else:
            console.print(
                "[yellow]Warning: Could not store key in system keyring. "
                "Falling back to environment variable ANTHROPIC_API_KEY[/yellow]"
            )
            console.print(
                "[yellow]For production use, please configure your system keyring[/yellow]"
            )

    except typer.Abort:
        console.print("[red]Cancelled by user[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error storing API key: {str(e)}[/red]")
        raise typer.Exit(code=1)


@app.command()
def logout() -> None:
    """Remove API key from system keyring.

    Removes the stored API key from the system keyring. If you still have
    the ANTHROPIC_API_KEY environment variable set, it will be used as
    a fallback, but we recommend unsetting it as well.

    Examples:
        jiro auth logout
    """
    try:
        if not is_key_stored():
            console.print("[yellow]No API key stored in system keyring[/yellow]")
            return

        # Confirm removal
        confirm = typer.confirm("Are you sure you want to remove the stored API key?")
        if not confirm:
            console.print("[yellow]Cancelled by user[/yellow]")
            return

        # Remove the key
        success = remove_api_key()

        if success:
            console.print("[green]API key removed from system keyring[/green]")
            console.print(
                "[cyan]Tip: If you have ANTHROPIC_API_KEY set as an environment "
                "variable, consider unsetting it:[/cyan]"
            )
            console.print("  unset ANTHROPIC_API_KEY")
        else:
            console.print("[red]Failed to remove API key from keyring[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error removing API key: {str(e)}[/red]")
        raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """Show authentication status.

    Shows whether an API key is stored in the system keyring and/or
    the ANTHROPIC_API_KEY environment variable (without revealing the key).

    Examples:
        jiro auth status
    """
    try:
        key_in_keyring = is_key_stored()
        api_key_in_env = bool(get_api_key())

        console.print("[cyan]Authentication Status[/cyan]")
        console.print("-" * 40)

        if key_in_keyring:
            console.print("[green]✓[/green] API key stored in system keyring")
        else:
            console.print("[yellow]✗[/yellow] No API key in system keyring")

        if api_key_in_env:
            console.print("[green]✓[/green] API key available (from keyring or environment)")
        else:
            console.print("[red]✗[/red] No API key found")

        if not api_key_in_env:
            console.print("\n[yellow]Warning: No API key configured[/yellow]")
            console.print("Run 'jiro auth login' to store your API key")

    except Exception as e:
        console.print(f"[red]Error checking authentication status: {str(e)}[/red]")
        raise typer.Exit(code=1)
