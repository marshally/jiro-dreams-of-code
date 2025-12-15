"""Tests for config loader."""

from pathlib import Path
from unittest.mock import patch

import pytest

from jiro.config.loader import load_config
from jiro.config.schema import (
    CommandsConfig,
    Config,
    ConventionsConfig,
    ModelsConfig,
    PreflightConfig,
)


@pytest.mark.unit
class TestLoadConfig:
    """Test config loader functionality."""

    def test_load_config_returns_config_dataclass(self, tmp_path: Path) -> None:
        """load_config should return a Config dataclass."""
        result = load_config(tmp_path, "test-project")
        assert isinstance(result, Config)

    def test_load_config_uses_defaults_when_file_missing(self, tmp_path: Path) -> None:
        """load_config should use defaults when config file is missing."""
        result = load_config(tmp_path, "test-project")

        # Verify defaults are used
        assert isinstance(result.models, ModelsConfig)
        assert result.models.planning == "claude-opus-4-20250514"
        assert result.models.execution == "claude-3-5-haiku-20241022"
        assert result.models.review == "claude-sonnet-4-20250514"

        assert isinstance(result.commands, CommandsConfig)
        assert result.commands.test == "pytest"
        assert result.commands.lint == "ruff check"
        assert result.commands.lint_fix == "ruff check --fix"

        assert isinstance(result.conventions, ConventionsConfig)
        assert result.conventions.test_file_pattern == "test_{name}.py"

        assert isinstance(result.preflight, PreflightConfig)
        assert result.preflight.skip_if_recent_minutes == 60

    def test_load_config_loads_values_from_yaml(self, tmp_path: Path) -> None:
        """load_config should load values from YAML when file exists."""
        # Create config directory and file
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "custom-planning-model"
  execution: "custom-execution-model"
  review: "custom-review-model"
commands:
  test: "custom-test-command"
  lint: "custom-lint-command"
  lint_fix: "custom-lint-fix-command"
conventions:
  test_file_pattern: "custom_test_{name}.py"
preflight:
  skip_if_recent_minutes: 120
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify loaded values
        assert result.models.planning == "custom-planning-model"
        assert result.models.execution == "custom-execution-model"
        assert result.models.review == "custom-review-model"

        assert result.commands.test == "custom-test-command"
        assert result.commands.lint == "custom-lint-command"
        assert result.commands.lint_fix == "custom-lint-fix-command"

        assert result.conventions.test_file_pattern == "custom_test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 120

    def test_load_config_uses_defaults_for_missing_keys(self, tmp_path: Path) -> None:
        """load_config should use defaults for missing keys in YAML."""
        # Create config directory and file with partial config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "custom-planning-model"
commands:
  test: "custom-test-command"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify custom values
        assert result.models.planning == "custom-planning-model"
        assert result.commands.test == "custom-test-command"

        # Verify defaults for missing keys
        assert result.models.execution == "claude-3-5-haiku-20241022"
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.lint == "ruff check"
        assert result.commands.lint_fix == "ruff check --fix"
        assert result.conventions.test_file_pattern == "test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 60

    def test_load_config_with_empty_yaml(self, tmp_path: Path) -> None:
        """load_config should handle empty YAML file gracefully."""
        # Create config directory and empty file
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text("")

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify all defaults are used
        assert result.models.planning == "claude-opus-4-20250514"
        assert result.commands.test == "pytest"
        assert result.conventions.test_file_pattern == "test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 60

    def test_load_config_with_partial_nested_config(self, tmp_path: Path) -> None:
        """load_config should handle partial nested config sections."""
        # Create config directory and file with partial nested config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "custom-planning-model"
preflight:
  skip_if_recent_minutes: 90
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify custom values
        assert result.models.planning == "custom-planning-model"
        assert result.preflight.skip_if_recent_minutes == 90

        # Verify defaults for missing nested keys
        assert result.models.execution == "claude-3-5-haiku-20241022"
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.test == "pytest"

    def test_load_config_with_project_name(self, tmp_path: Path) -> None:
        """load_config should use provided project name in path."""
        # Create config directory with custom project name
        config_dir = tmp_path / ".jiro-dreams-of-code" / "my-custom-project"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-specific-model"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "my-custom-project")

        assert result.models.planning == "project-specific-model"
        assert result.models.execution == "claude-3-5-haiku-20241022"
