"""Assets subcommand module for managing customizable assets (prompts and templates)."""

from collections import defaultdict

import typer
from rich.console import Console
from rich.table import Table

from jiro.assets.loader import AssetInfo, get_asset_path, list_assets

app = typer.Typer(
    name="assets",
    help="Manage customizable assets (prompts and templates)",
    no_args_is_help=True,
)

console = Console()


def _display_assets_table(assets: list[AssetInfo]) -> None:
    """Display assets in a Rich table format, grouped by type.

    Args:
        assets: List of AssetInfo objects to display.
    """
    if not assets:
        console.print("[yellow]No assets found[/yellow]")
        return

    # Group assets by type
    assets_by_type = defaultdict(list)
    for asset in assets:
        assets_by_type[asset.asset_type].append(asset)

    # Display counts
    console.print()
    total_assets = len(assets)
    console.print(f"[bold]Total Assets: {total_assets}[/bold]")

    for asset_type in sorted(assets_by_type.keys()):
        type_assets = assets_by_type[asset_type]
        count = len(type_assets)
        console.print(f"  [cyan]{asset_type.title()}s:[/cyan] {count}")

    console.print()

    # Create a table
    table = Table(title="Assets")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Path", style="yellow")

    # Sort by type then by name for consistent display
    sorted_assets = sorted(assets, key=lambda a: (a.asset_type, a.name))

    for asset in sorted_assets:
        # Convert path to string first to avoid any issues with pathlib
        path_str = str(asset.path)
        table.add_row(
            asset.name,
            asset.asset_type,
            path_str,
        )

    console.print(table)


@app.command(name="list")
def list_all_assets() -> None:
    """
    List all bundled assets and their locations.

    Shows which assets are available as prompts and templates.
    Displays asset type (prompt, template), name, and file path.

    Examples:
        jiro assets list
    """
    try:
        # Get all available assets
        assets_list_loader = list_assets()

        # Display assets in table format
        _display_assets_table(assets_list_loader)

    except Exception as e:  # noqa: B904
        console.print(f"[red]Error listing assets: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@app.command(name="which")
def which_asset_location(name: str) -> None:
    """
    Show the package location for an asset.

    Display the full path to where an asset will be loaded from.
    For the steel thread, this shows the package location.

    Args:
        name: Name of the asset (e.g., "planning_agent.md" or "commit/docs.txt.j2")

    Examples:
        jiro assets which planning_agent.md
        jiro assets which commit/docs.txt.j2
    """
    try:
        # Get the path to the asset
        asset_path = get_asset_path(name)
        # Display the path
        console.print(str(asset_path))

    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error retrieving asset location: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@app.command(name="customize")
def customize_asset(name: str) -> None:
    """
    Customize an asset (deferred to future release).

    Shows the current package default for an asset.
    Customization support will be added in a future release,
    allowing you to override assets in ~/.config/jiro/assets/.

    Args:
        name: Name of the asset (e.g., "planning_agent.md" or "commit/docs.txt.j2")

    Examples:
        jiro assets customize planning_agent.md
        jiro assets customize commit/docs.txt.j2
    """
    try:
        # Get the path to the asset
        asset_path = get_asset_path(name)

        # Display deferred message with warning
        console.print(
            "\n[yellow]⚠️  Asset customization is deferred to a future release.[/yellow]\n"
        )

        # Read and display the package default content
        content = asset_path.read_text()
        console.print(f"[bold]Current package default for '{name}':[/bold]")
        console.print("-" * 60)
        console.print(content)
        console.print("-" * 60)

        # Show where overrides will go in the future
        console.print(
            "\n[cyan]To customize this asset in the future, override files will be placed in:[/cyan]"
        )
        console.print("[bold]~/.config/jiro/assets/[/bold]\n")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:  # noqa: B904
        console.print(f"[red]Error customizing asset: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
