"""Configuration loader for jiro projects."""

from pathlib import Path

import yaml

from jiro.config.schema import (
    CommandsConfig,
    Config,
    ConventionsConfig,
    ModelsConfig,
    PreflightConfig,
)
from jiro.core.paths import get_config_path


def _flatten_config_for_save(config: Config) -> dict:
    """Convert Config object to flat dictionary for YAML serialization.

    Args:
        config: Config object to flatten.

    Returns:
        Dictionary with nested structure for YAML output.
    """
    return {
        "models": {
            "planning": config.models.planning,
            "execution": config.models.execution,
            "review": config.models.review,
        },
        "commands": {
            "test": config.commands.test,
            "lint": config.commands.lint,
            "lint_fix": config.commands.lint_fix,
        },
        "conventions": {
            "test_file_pattern": config.conventions.test_file_pattern,
        },
        "preflight": {
            "skip_if_recent_minutes": config.preflight.skip_if_recent_minutes,
        },
    }


def save_config(config: Config, project_root: Path, project_name: str) -> None:
    """Save configuration to project scope directory.

    Saves config to ~/.jiro-dreams-of-code/$PROJECT/config.yaml.

    Args:
        config: Config object to save.
        project_root: The root directory of the project.
        project_name: The project name for scoped config directory.
    """
    config_path = get_config_path(project_root, stealth=True, project_name=project_name)

    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten config and write to YAML
    config_dict = _flatten_config_for_save(config)
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)


def load_config(project_root: Path, project_name: str) -> Config:
    """Load configuration from project scope directory.

    Loads config from ~/.jiro-dreams-of-code/$PROJECT/config.yaml.
    Returns Config dataclass with YAML values and defaults for missing values.

    Args:
        project_root: The root directory of the project.
        project_name: The project name for scoped config directory.

    Returns:
        Config dataclass with loaded values and defaults.
    """
    # Get config file path using stealth mode
    config_path = get_config_path(project_root, stealth=True, project_name=project_name)

    # Load YAML if file exists
    config_data = {}
    if config_path.exists():
        with open(config_path) as f:
            loaded_data = yaml.safe_load(f)
            if loaded_data:
                config_data = loaded_data

    # Build nested configs with defaults
    models_data = config_data.get("models", {})
    models = ModelsConfig(
        planning=models_data.get("planning", "claude-opus-4-20250514"),
        execution=models_data.get("execution", "claude-3-5-haiku-20241022"),
        review=models_data.get("review", "claude-sonnet-4-20250514"),
    )

    commands_data = config_data.get("commands", {})
    commands = CommandsConfig(
        test=commands_data.get("test", "pytest"),
        lint=commands_data.get("lint", "ruff check"),
        lint_fix=commands_data.get("lint_fix", "ruff check --fix"),
    )

    conventions_data = config_data.get("conventions", {})
    conventions = ConventionsConfig(
        test_file_pattern=conventions_data.get("test_file_pattern", "test_{name}.py"),
    )

    preflight_data = config_data.get("preflight", {})
    preflight = PreflightConfig(
        skip_if_recent_minutes=preflight_data.get("skip_if_recent_minutes", 60),
    )

    return Config(
        models=models,
        commands=commands,
        conventions=conventions,
        preflight=preflight,
    )
