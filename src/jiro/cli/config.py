"""Configuration subcommand module for viewing and managing configuration."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.config.loader import load_config, load_config_with_sources, save_config
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


def _get_config_with_sources() -> tuple[Config, dict[str, str]]:
    """Get the effective configuration and source information for each value."""
    project_root = Path.cwd()
    project_name = project_root.name
    try:
        return load_config_with_sources(project_root, project_name)
    except Exception:
        # Fallback for when load_config_with_sources is not available or mocked
        config = load_config(project_root, project_name)
        return config, {}


def _flatten_config(config: Config, sources: dict[str, str] | None = None) -> dict:
    """Flatten the nested config structure into a key-value format.

    Returns a dictionary with keys like "models.planning" and values
    containing the actual value and its source.

    Args:
        config: The Config object to flatten.
        sources: Optional dict mapping dotted keys to their source. If not provided,
                 all sources default to "default".
    """
    if sources is None:
        sources = {}

    flattened = {}

    # Process models section
    for key in ["planning", "execution", "review"]:
        value = getattr(config.models, key)
        full_key = f"models.{key}"
        flattened[full_key] = {
            "value": value,
            "source": sources.get(full_key, "default"),
            "section": "models",
        }

    # Process commands section
    for key in ["test", "lint", "lint_fix"]:
        value = getattr(config.commands, key)
        full_key = f"commands.{key}"
        flattened[full_key] = {
            "value": value,
            "source": sources.get(full_key, "default"),
            "section": "commands",
        }

    # Process conventions section
    for key in ["test_file_pattern"]:
        value = getattr(config.conventions, key)
        full_key = f"conventions.{key}"
        flattened[full_key] = {
            "value": value,
            "source": sources.get(full_key, "default"),
            "section": "conventions",
        }

    # Process preflight section
    for key in ["skip_if_recent_minutes"]:
        value = getattr(config.preflight, key)
        full_key = f"preflight.{key}"
        flattened[full_key] = {
            "value": value,
            "source": sources.get(full_key, "default"),
            "section": "preflight",
        }

    return flattened


def _build_json_output(config: Config, sources: dict[str, str] | None = None) -> dict:
    """Build a JSON-serializable representation of the config with sources.

    Args:
        config: The Config object to serialize.
        sources: Optional dict mapping dotted keys to their source. If not provided,
                 all sources default to "default".
    """
    if sources is None:
        sources = {}

    return {
        "models": {
            "planning": {
                "value": config.models.planning,
                "source": sources.get("models.planning", "default"),
            },
            "execution": {
                "value": config.models.execution,
                "source": sources.get("models.execution", "default"),
            },
            "review": {
                "value": config.models.review,
                "source": sources.get("models.review", "default"),
            },
        },
        "commands": {
            "test": {
                "value": config.commands.test,
                "source": sources.get("commands.test", "default"),
            },
            "lint": {
                "value": config.commands.lint,
                "source": sources.get("commands.lint", "default"),
            },
            "lint_fix": {
                "value": config.commands.lint_fix,
                "source": sources.get("commands.lint_fix", "default"),
            },
        },
        "conventions": {
            "test_file_pattern": {
                "value": config.conventions.test_file_pattern,
                "source": sources.get("conventions.test_file_pattern", "default"),
            },
        },
        "preflight": {
            "skip_if_recent_minutes": {
                "value": config.preflight.skip_if_recent_minutes,
                "source": sources.get("preflight.skip_if_recent_minutes", "default"),
            },
        },
    }


def _display_config_table(config: Config, sources: dict[str, str] | None = None) -> None:
    """Display configuration values in a Rich table.

    Args:
        config: The Config object to display.
        sources: Optional dict mapping dotted keys to their source. If not provided,
                 all sources default to "default".
    """
    if sources is None:
        sources = {}

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="yellow")

    # Models section
    table.add_row(
        "models.planning", config.models.planning, sources.get("models.planning", "default")
    )
    table.add_row(
        "models.execution",
        config.models.execution,
        sources.get("models.execution", "default"),
    )
    table.add_row("models.review", config.models.review, sources.get("models.review", "default"))

    # Commands section
    table.add_row("commands.test", config.commands.test, sources.get("commands.test", "default"))
    table.add_row("commands.lint", config.commands.lint, sources.get("commands.lint", "default"))
    table.add_row(
        "commands.lint_fix",
        config.commands.lint_fix,
        sources.get("commands.lint_fix", "default"),
    )

    # Conventions section
    table.add_row(
        "conventions.test_file_pattern",
        config.conventions.test_file_pattern,
        sources.get("conventions.test_file_pattern", "default"),
    )

    # Preflight section
    table.add_row(
        "preflight.skip_if_recent_minutes",
        str(config.preflight.skip_if_recent_minutes),
        sources.get("preflight.skip_if_recent_minutes", "default"),
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
    config, sources = _get_config_with_sources()

    if json_output:
        output = _build_json_output(config, sources)
        console.print(json.dumps(output))
    else:
        _display_config_table(config, sources)


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
    config, sources = _get_config_with_sources()
    flattened = _flatten_config(config, sources)

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
