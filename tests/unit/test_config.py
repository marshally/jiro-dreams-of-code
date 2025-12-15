"""Comprehensive unit tests for config module (schema and loader)."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from jiro.config.loader import load_config, save_config
from jiro.config.schema import (
    CommandsConfig,
    Config,
    ConventionsConfig,
    ModelsConfig,
    PreflightConfig,
)


# ============================================================================
# ConfigSchema Tests
# ============================================================================
class TestModelsConfigDefaults:
    """Test ModelsConfig schema defaults."""

    @pytest.mark.unit
    def test_models_config_has_expected_defaults(self) -> None:
        """ModelsConfig should have all expected default values."""
        config = ModelsConfig()
        assert config.planning == "claude-opus-4-20250514"
        assert config.execution == "claude-3-5-haiku-20241022"
        assert config.review == "claude-sonnet-4-20250514"

    @pytest.mark.unit
    def test_models_config_custom_values(self) -> None:
        """ModelsConfig should accept and store custom values."""
        config = ModelsConfig(
            planning="custom-planning",
            execution="custom-execution",
            review="custom-review",
        )
        assert config.planning == "custom-planning"
        assert config.execution == "custom-execution"
        assert config.review == "custom-review"

    @pytest.mark.unit
    def test_models_config_partial_override(self) -> None:
        """ModelsConfig should allow partial overrides with defaults."""
        config = ModelsConfig(planning="custom-planning")
        assert config.planning == "custom-planning"
        assert config.execution == "claude-3-5-haiku-20241022"
        assert config.review == "claude-sonnet-4-20250514"


class TestCommandsConfigDefaults:
    """Test CommandsConfig schema defaults."""

    @pytest.mark.unit
    def test_commands_config_has_expected_defaults(self) -> None:
        """CommandsConfig should have all expected default values."""
        config = CommandsConfig()
        assert config.test == "pytest"
        assert config.lint == "ruff check"
        assert config.lint_fix == "ruff check --fix"

    @pytest.mark.unit
    def test_commands_config_custom_values(self) -> None:
        """CommandsConfig should accept and store custom values."""
        config = CommandsConfig(
            test="uv run pytest",
            lint="uv run ruff check",
            lint_fix="uv run ruff check --fix",
        )
        assert config.test == "uv run pytest"
        assert config.lint == "uv run ruff check"
        assert config.lint_fix == "uv run ruff check --fix"

    @pytest.mark.unit
    def test_commands_config_partial_override(self) -> None:
        """CommandsConfig should allow partial overrides with defaults."""
        config = CommandsConfig(test="custom-test")
        assert config.test == "custom-test"
        assert config.lint == "ruff check"
        assert config.lint_fix == "ruff check --fix"


class TestConventionsConfigDefaults:
    """Test ConventionsConfig schema defaults."""

    @pytest.mark.unit
    def test_conventions_config_has_expected_defaults(self) -> None:
        """ConventionsConfig should have all expected default values."""
        config = ConventionsConfig()
        assert config.test_file_pattern == "test_{name}.py"

    @pytest.mark.unit
    def test_conventions_config_custom_values(self) -> None:
        """ConventionsConfig should accept and store custom values."""
        config = ConventionsConfig(test_file_pattern="{name}_test.py")
        assert config.test_file_pattern == "{name}_test.py"


class TestPreflightConfigDefaults:
    """Test PreflightConfig schema defaults."""

    @pytest.mark.unit
    def test_preflight_config_has_expected_defaults(self) -> None:
        """PreflightConfig should have all expected default values."""
        config = PreflightConfig()
        assert config.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_preflight_config_custom_values(self) -> None:
        """PreflightConfig should accept and store custom values."""
        config = PreflightConfig(skip_if_recent_minutes=30)
        assert config.skip_if_recent_minutes == 30


class TestConfigDefaults:
    """Test main Config schema defaults."""

    @pytest.mark.unit
    def test_config_has_all_nested_config_types(self) -> None:
        """Config should have all nested config types."""
        config = Config()
        assert isinstance(config.models, ModelsConfig)
        assert isinstance(config.commands, CommandsConfig)
        assert isinstance(config.conventions, ConventionsConfig)
        assert isinstance(config.preflight, PreflightConfig)

    @pytest.mark.unit
    def test_config_all_nested_defaults_propagate(self) -> None:
        """Config should have all expected defaults in nested configs."""
        config = Config()
        # Models defaults
        assert config.models.planning == "claude-opus-4-20250514"
        assert config.models.execution == "claude-3-5-haiku-20241022"
        assert config.models.review == "claude-sonnet-4-20250514"
        # Commands defaults
        assert config.commands.test == "pytest"
        assert config.commands.lint == "ruff check"
        assert config.commands.lint_fix == "ruff check --fix"
        # Conventions defaults
        assert config.conventions.test_file_pattern == "test_{name}.py"
        # Preflight defaults
        assert config.preflight.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_config_custom_nested_configs(self) -> None:
        """Config should accept custom nested configs."""
        config = Config(
            models=ModelsConfig(planning="custom-model"),
            commands=CommandsConfig(test="custom-test"),
        )
        assert config.models.planning == "custom-model"
        assert config.commands.test == "custom-test"
        # Other nested configs should still have defaults
        assert config.conventions.test_file_pattern == "test_{name}.py"
        assert config.preflight.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_config_all_fields_have_type_hints(self) -> None:
        """All Config fields should have proper type hints."""
        from typing import get_type_hints

        hints = get_type_hints(Config)
        assert "models" in hints
        assert "commands" in hints
        assert "conventions" in hints
        assert "preflight" in hints


# ============================================================================
# Config Loader Tests
# ============================================================================
class TestLoadConfigMissingFile:
    """Test load_config when configuration file is missing."""

    @pytest.mark.unit
    def test_load_config_returns_defaults_with_missing_file(self, tmp_path: Path) -> None:
        """load_config should return defaults when config file is missing."""
        result = load_config(tmp_path, "test-project")
        assert isinstance(result, Config)

        # Verify all defaults
        assert result.models.planning == "claude-opus-4-20250514"
        assert result.models.execution == "claude-3-5-haiku-20241022"
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.test == "pytest"
        assert result.commands.lint == "ruff check"
        assert result.commands.lint_fix == "ruff check --fix"
        assert result.conventions.test_file_pattern == "test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_load_config_handles_empty_yaml_file(self, tmp_path: Path) -> None:
        """load_config should handle empty YAML files gracefully."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("")

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify all defaults are used
        assert result.models.planning == "claude-opus-4-20250514"
        assert result.commands.test == "pytest"
        assert result.conventions.test_file_pattern == "test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 60


class TestLoadConfigPartialConfig:
    """Test load_config with partial configuration."""

    @pytest.mark.unit
    def test_load_config_merges_partial_config_with_defaults(self, tmp_path: Path) -> None:
        """load_config should merge partial config with defaults."""
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

    @pytest.mark.unit
    def test_load_config_handles_partial_nested_sections(self, tmp_path: Path) -> None:
        """load_config should handle partial nested config sections."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "custom-planning-model"
  execution: "custom-execution-model"
preflight:
  skip_if_recent_minutes: 90
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify custom values
        assert result.models.planning == "custom-planning-model"
        assert result.models.execution == "custom-execution-model"
        assert result.preflight.skip_if_recent_minutes == 90
        # Verify defaults for missing nested keys
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.test == "pytest"

    @pytest.mark.unit
    def test_load_config_partial_command_config(self, tmp_path: Path) -> None:
        """load_config should handle partial commands config."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
commands:
  test: "custom-test"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        assert result.commands.test == "custom-test"
        assert result.commands.lint == "ruff check"
        assert result.commands.lint_fix == "ruff check --fix"


class TestLoadConfigFullConfig:
    """Test load_config with complete configuration."""

    @pytest.mark.unit
    def test_load_config_with_full_config(self, tmp_path: Path) -> None:
        """load_config should load complete configuration from YAML."""
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

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify all custom values
        assert result.models.planning == "custom-planning-model"
        assert result.models.execution == "custom-execution-model"
        assert result.models.review == "custom-review-model"
        assert result.commands.test == "custom-test-command"
        assert result.commands.lint == "custom-lint-command"
        assert result.commands.lint_fix == "custom-lint-fix-command"
        assert result.conventions.test_file_pattern == "custom_test_{name}.py"
        assert result.preflight.skip_if_recent_minutes == 120

    @pytest.mark.unit
    def test_load_config_with_various_values(self, tmp_path: Path) -> None:
        """load_config should handle various configuration values."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "gpt-4"
  execution: "gpt-3.5"
  review: "claude-2"
commands:
  test: "pytest -v"
  lint: "pylint"
  lint_fix: "black --line-length=100"
conventions:
  test_file_pattern: "{name}_spec.py"
preflight:
  skip_if_recent_minutes: 5
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        assert result.models.planning == "gpt-4"
        assert result.models.execution == "gpt-3.5"
        assert result.models.review == "claude-2"
        assert result.commands.test == "pytest -v"
        assert result.commands.lint == "pylint"
        assert result.commands.lint_fix == "black --line-length=100"
        assert result.conventions.test_file_pattern == "{name}_spec.py"
        assert result.preflight.skip_if_recent_minutes == 5


class TestLoadConfigProjectScoping:
    """Test load_config with different project names and paths."""

    @pytest.mark.unit
    def test_load_config_with_custom_project_name(self, tmp_path: Path) -> None:
        """load_config should use provided project name in path."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "my-custom-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-specific-model"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "my-custom-project")

        assert result.models.planning == "project-specific-model"
        # Other models should have defaults
        assert result.models.execution == "claude-3-5-haiku-20241022"

    @pytest.mark.unit
    def test_load_config_with_different_project_names_isolated(self, tmp_path: Path) -> None:
        """load_config should isolate configs for different projects."""
        # Create config for project 1
        config_dir1 = tmp_path / ".jiro-dreams-of-code" / "project-1"
        config_dir1.mkdir(parents=True, exist_ok=True)
        config_file1 = config_dir1 / "config.yaml"
        config_file1.write_text(
            """
models:
  planning: "project-1-model"
"""
        )

        # Create config for project 2
        config_dir2 = tmp_path / ".jiro-dreams-of-code" / "project-2"
        config_dir2.mkdir(parents=True, exist_ok=True)
        config_file2 = config_dir2 / "config.yaml"
        config_file2.write_text(
            """
models:
  planning: "project-2-model"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result1 = load_config(tmp_path, "project-1")
            result2 = load_config(tmp_path, "project-2")

        assert result1.models.planning == "project-1-model"
        assert result2.models.planning == "project-2-model"


class TestLoadConfigErrorHandling:
    """Test load_config error handling."""

    @pytest.mark.unit
    def test_load_config_handles_invalid_yaml(self, tmp_path: Path) -> None:
        """load_config should handle invalid YAML gracefully."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        # Write invalid YAML
        config_file.write_text("invalid: yaml: content: here:")

        with (
            patch("jiro.config.loader.Path.home", return_value=tmp_path),
            pytest.raises(yaml.YAMLError),
        ):
            load_config(tmp_path, "test-project")

    @pytest.mark.unit
    def test_load_config_handles_none_yaml_data(self, tmp_path: Path) -> None:
        """load_config should handle YAML file that parses to None."""
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        # Write YAML that parses to None
        config_file.write_text("# Just a comment\n")

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Should use defaults
        assert result.models.planning == "claude-opus-4-20250514"


class TestLoadConfigReturnType:
    """Test load_config return type and structure."""

    @pytest.mark.unit
    def test_load_config_returns_config_dataclass_instance(self, tmp_path: Path) -> None:
        """load_config should always return a Config dataclass instance."""
        result = load_config(tmp_path, "test-project")
        assert isinstance(result, Config)

    @pytest.mark.unit
    def test_load_config_result_has_all_nested_configs(self, tmp_path: Path) -> None:
        """load_config result should have all nested config types."""
        result = load_config(tmp_path, "test-project")
        assert isinstance(result.models, ModelsConfig)
        assert isinstance(result.commands, CommandsConfig)
        assert isinstance(result.conventions, ConventionsConfig)
        assert isinstance(result.preflight, PreflightConfig)


class TestSaveConfig:
    """Test save_config functionality."""

    @pytest.mark.unit
    def test_save_config_creates_config_file(self, tmp_path: Path) -> None:
        """save_config should create config file with correct content."""
        config = Config(
            models=ModelsConfig(planning="test-model"),
            commands=CommandsConfig(test="test-cmd"),
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            save_config(config, tmp_path, "test-project")

        config_file = tmp_path / ".jiro-dreams-of-code" / "test-project" / "config.yaml"
        assert config_file.exists()

        # Load and verify
        with open(config_file) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["models"]["planning"] == "test-model"
        assert saved_data["commands"]["test"] == "test-cmd"

    @pytest.mark.unit
    def test_save_config_creates_parent_directories(self, tmp_path: Path) -> None:
        """save_config should create parent directories if needed."""
        config = Config()

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            save_config(config, tmp_path, "new-project")

        config_dir = tmp_path / ".jiro-dreams-of-code" / "new-project"
        assert config_dir.exists()
        assert (config_dir / "config.yaml").exists()

    @pytest.mark.unit
    def test_save_and_load_config_roundtrip(self, tmp_path: Path) -> None:
        """save_config and load_config should roundtrip successfully."""
        original = Config(
            models=ModelsConfig(
                planning="custom-planning",
                execution="custom-execution",
                review="custom-review",
            ),
            commands=CommandsConfig(
                test="custom-test",
                lint="custom-lint",
                lint_fix="custom-lint-fix",
            ),
            conventions=ConventionsConfig(test_file_pattern="custom_{name}_test.py"),
            preflight=PreflightConfig(skip_if_recent_minutes=45),
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            save_config(original, tmp_path, "test-project")
            loaded = load_config(tmp_path, "test-project")

        assert loaded.models.planning == original.models.planning
        assert loaded.models.execution == original.models.execution
        assert loaded.models.review == original.models.review
        assert loaded.commands.test == original.commands.test
        assert loaded.commands.lint == original.commands.lint
        assert loaded.commands.lint_fix == original.commands.lint_fix
        assert loaded.conventions.test_file_pattern == original.conventions.test_file_pattern
        assert loaded.preflight.skip_if_recent_minutes == original.preflight.skip_if_recent_minutes


# ============================================================================
# Integration Tests
# ============================================================================
class TestConfigIntegration:
    """Integration tests for config schema and loader."""

    @pytest.mark.unit
    def test_config_schema_with_loader_integration(self, tmp_path: Path) -> None:
        """Config schema and loader should work together seamlessly."""
        # Create a config using schema
        config = Config(
            models=ModelsConfig(planning="integration-test-model"),
        )

        # Save it
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            save_config(config, tmp_path, "integration-test")

        # Load it back
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            loaded = load_config(tmp_path, "integration-test")

        # Verify
        assert loaded.models.planning == "integration-test-model"
        # Defaults should be present for unset values
        assert loaded.models.execution == "claude-3-5-haiku-20241022"
        assert isinstance(loaded.commands, CommandsConfig)
