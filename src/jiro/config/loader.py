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
        planning=models_data.get("planning", "claude-opus-4-5-20250514"),
        execution=models_data.get("execution", "claude-haiku-4-5-20250514"),
        review=models_data.get("review", "claude-sonnet-4-5-20250514"),
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
