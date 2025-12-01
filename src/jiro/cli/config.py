"""Configuration subcommand module for viewing and managing configuration."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.config.loader import load_config, save_config
from jiro.config.schema import Config

app = typer.Typer(
    name="config",
    help="Get/set configuration values",
    no_args_is_help=True,
)

console = Console()


def _get_config() -> Config:
    """Get the effective configuration for the current project."""
    project_root = Path.cwd()
    project_name = project_root.name
    return load_config(project_root, project_name)


def _flatten_config(config: Config) -> dict:
    """Flatten the nested config structure into a key-value format.

    Returns a dictionary with keys like "models.planning" and values
    containing the actual value and its source.
    """
    flattened = {}

    # Process models section
    for key in ["planning", "execution", "review"]:
        value = getattr(config.models, key)
        flattened[f"models.{key}"] = {
            "value": value,
            "source": "default",  # For now, assume all are defaults
            "section": "models",
        }

    # Process commands section
    for key in ["test", "lint", "lint_fix"]:
        value = getattr(config.commands, key)
        flattened[f"commands.{key}"] = {
            "value": value,
            "source": "default",
            "section": "commands",
        }

    # Process conventions section
    for key in ["test_file_pattern"]:
        value = getattr(config.conventions, key)
        flattened[f"conventions.{key}"] = {
            "value": value,
            "source": "default",
            "section": "conventions",
        }

    # Process preflight section
    for key in ["skip_if_recent_minutes"]:
        value = getattr(config.preflight, key)
        flattened[f"preflight.{key}"] = {
            "value": value,
            "source": "default",
            "section": "preflight",
        }

    return flattened


def _build_json_output(config: Config) -> dict:
    """Build a JSON-serializable representation of the config with sources."""
    return {
        "models": {
            "planning": {
                "value": config.models.planning,
                "source": "default",
            },
            "execution": {
                "value": config.models.execution,
                "source": "default",
            },
            "review": {
                "value": config.models.review,
                "source": "default",
            },
        },
        "commands": {
            "test": {
                "value": config.commands.test,
                "source": "default",
            },
            "lint": {
                "value": config.commands.lint,
                "source": "default",
            },
            "lint_fix": {
                "value": config.commands.lint_fix,
                "source": "default",
            },
        },
        "conventions": {
            "test_file_pattern": {
                "value": config.conventions.test_file_pattern,
                "source": "default",
            },
        },
        "preflight": {
            "skip_if_recent_minutes": {
                "value": config.preflight.skip_if_recent_minutes,
                "source": "default",
            },
        },
    }


def _display_config_table(config: Config) -> None:
    """Display configuration values in a Rich table."""
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="yellow")

    # Models section
    table.add_row("models.planning", config.models.planning, "default")
    table.add_row("models.execution", config.models.execution, "default")
    table.add_row("models.review", config.models.review, "default")

    # Commands section
    table.add_row("commands.test", config.commands.test, "default")
    table.add_row("commands.lint", config.commands.lint, "default")
    table.add_row("commands.lint_fix", config.commands.lint_fix, "default")

    # Conventions section
    table.add_row("conventions.test_file_pattern", config.conventions.test_file_pattern, "default")

    # Preflight section
    table.add_row(
        "preflight.skip_if_recent_minutes", str(config.preflight.skip_if_recent_minutes), "default"
    )

    console.print(table)


@app.command("list")
def config_list(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    global_config: Annotated[bool, typer.Option("--global", help="Show global config")] = False,
    project: Annotated[bool, typer.Option("--project", help="Show project config")] = False,
    local: Annotated[bool, typer.Option("--local", help="Show local config")] = False,
) -> None:
    """
    List all configuration values.

    Shows effective configuration with source scope.

    Examples:
        jiro config list
        jiro config list --json
        jiro config list --global
        jiro config list --project
    """
    config = _get_config()

    if json_output:
        output = _build_json_output(config)
        console.print(json.dumps(output))
    else:
        _display_config_table(config)


@app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Configuration key (e.g., commands.test)")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """
    Get a configuration value.

    Shows the effective value and which scope it comes from.

    Examples:
        jiro config get commands.test
        jiro config get models.execution
        jiro config get models.planning --json
    """
    config = _get_config()
    flattened = _flatten_config(config)

    if key not in flattened:
        console.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        raise typer.Exit(code=1)

    config_item = flattened[key]

    if json_output:
        output = {
            "key": key,
            "value": config_item["value"],
            "source": config_item["source"],
        }
        console.print(json.dumps(output))
    else:
        # Display in human-readable format
        console.print(f"[cyan]Key:[/cyan] {key}")
        console.print(f"[cyan]Value:[/cyan] {config_item['value']}")
        console.print(f"[cyan]Source:[/cyan] {config_item['source']}")


def _set_config_value(config: Config, key: str, value: str) -> None:
    """Set a configuration value by dotted key notation.

    Args:
        config: The Config object to modify.
        key: Dotted notation key (e.g., "models.planning").
        value: The new value to set.

    Raises:
        ValueError: If the key is not valid.
    """
    parts = key.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid key format: {key}. Use format 'section.key'")

    section, field = parts

    if section == "models":
        if field == "planning":
            config.models.planning = value
        elif field == "execution":
            config.models.execution = value
        elif field == "review":
            config.models.review = value
        else:
            raise ValueError(f"Unknown models field: {field}")
    elif section == "commands":
        if field == "test":
            config.commands.test = value
        elif field == "lint":
            config.commands.lint = value
        elif field == "lint_fix":
            config.commands.lint_fix = value
        else:
            raise ValueError(f"Unknown commands field: {field}")
    elif section == "conventions":
        if field == "test_file_pattern":
            config.conventions.test_file_pattern = value
        else:
            raise ValueError(f"Unknown conventions field: {field}")
    elif section == "preflight":
        if field == "skip_if_recent_minutes":
            try:
                config.preflight.skip_if_recent_minutes = int(value)
            except ValueError as err:
                raise ValueError(f"Invalid integer value for {key}: {value}") from err
        else:
            raise ValueError(f"Unknown preflight field: {field}")
    else:
        raise ValueError(f"Unknown configuration section: {section}")


@app.command("set")
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
    # Get the current configuration
    config = _get_config()

    # Validate the key exists
    try:
        _set_config_value(config, key, value)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from e

    # Save the configuration
    project_root = Path.cwd()
    project_name = project_root.name
    save_config(config, project_root, project_name)

    # Show confirmation
    console.print(f"[green]Successfully set {key} = {value}[/green]")
