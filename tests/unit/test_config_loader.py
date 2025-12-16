"""Tests for config loader."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from jiro.config.loader import load_config, load_config_with_sources, merge_configs
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

    def test_load_config_with_local_config_file(self, tmp_path: Path) -> None:
        """load_config should load values from local .jiro-dreams-of-code.yaml in project root."""
        # Create local config file in project root
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
  execution: "local-execution-model"
commands:
  test: "local-test-command"
"""
        )

        result = load_config(tmp_path, "test-project")

        # Verify local config values are loaded
        assert result.models.planning == "local-planning-model"
        assert result.models.execution == "local-execution-model"
        assert result.commands.test == "local-test-command"

        # Verify defaults for missing keys
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.lint == "ruff check"

    def test_load_config_prefers_local_over_project_scope(self, tmp_path: Path) -> None:
        """load_config should prefer local config over project scope config."""
        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
commands:
  test: "project-test-command"
"""
        )

        # Create local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify local config takes precedence
        assert result.models.planning == "local-planning-model"
        # Project scope config value should not be used when local config exists
        assert result.commands.test == "project-test-command"

    def test_load_config_with_local_config_empty_file(self, tmp_path: Path) -> None:
        """load_config should handle empty local config file gracefully."""
        # Create empty local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text("")

        result = load_config(tmp_path, "test-project")

        # Verify all defaults are used
        assert result.models.planning == "claude-opus-4-20250514"
        assert result.commands.test == "pytest"
        assert result.conventions.test_file_pattern == "test_{name}.py"

    def test_load_config_without_local_config_uses_project_scope(self, tmp_path: Path) -> None:
        """load_config should use project scope config when local config is absent."""
        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify project scope config is used
        assert result.models.planning == "project-planning-model"

    def test_load_config_with_global_config_file(self, tmp_path: Path) -> None:
        """load_config should load values from global ~/.jiro-dreams-of-code/config.yaml."""
        # Create global config file
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)

        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
  execution: "global-execution-model"
commands:
  test: "global-test-command"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify global config values are loaded
        assert result.models.planning == "global-planning-model"
        assert result.models.execution == "global-execution-model"
        assert result.commands.test == "global-test-command"

        # Verify defaults for missing keys
        assert result.models.review == "claude-sonnet-4-20250514"
        assert result.commands.lint == "ruff check"

    def test_load_config_prefers_project_scope_over_global(self, tmp_path: Path) -> None:
        """load_config should prefer project scope config over global config."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
commands:
  test: "global-test-command"
"""
        )

        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify project scope config takes precedence over global
        assert result.models.planning == "project-planning-model"
        # Global config value should be used for keys not in project scope
        assert result.commands.test == "global-test-command"

    def test_load_config_prefers_local_over_global(self, tmp_path: Path) -> None:
        """load_config should prefer local config over global config."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
  execution: "global-execution-model"
commands:
  test: "global-test-command"
"""
        )

        # Create local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify local config takes precedence
        assert result.models.planning == "local-planning-model"
        # Global config value should be used for keys not in local config
        assert result.models.execution == "global-execution-model"
        assert result.commands.test == "global-test-command"

    def test_load_config_full_precedence_order(self, tmp_path: Path) -> None:
        """load_config should follow precedence: local > project scope > global > defaults."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
  execution: "global-execution-model"
  review: "global-review-model"
commands:
  test: "global-test-command"
  lint: "global-lint-command"
"""
        )

        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
commands:
  test: "project-test-command"
preflight:
  skip_if_recent_minutes: 75
"""
        )

        # Create local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
conventions:
  test_file_pattern: "local_test_{name}.py"
"""
        )

        # Mock home directory to use tmp_path
        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            result = load_config(tmp_path, "test-project")

        # Verify precedence order:
        # - local > project scope > global > defaults
        assert result.models.planning == "local-planning-model"  # from local
        assert result.models.execution == "global-execution-model"  # from global (not in local)
        assert (
            result.models.review == "global-review-model"
        )  # from global (not in local or project)
        assert result.commands.test == "project-test-command"  # from project (not in local)
        assert (
            result.commands.lint == "global-lint-command"
        )  # from global (not in local or project)
        assert result.conventions.test_file_pattern == "local_test_{name}.py"  # from local
        assert result.preflight.skip_if_recent_minutes == 75  # from project scope (not in local)


@pytest.mark.unit
class TestMergeConfigs:
    """Test config merge functionality."""

    def test_merge_configs_simple_values(self) -> None:
        """merge_configs should merge simple key-value pairs."""
        base = {"key1": "value1", "key2": "value2"}
        override = {"key3": "value3"}
        merge_configs(base, override)

        assert base == {"key1": "value1", "key2": "value2", "key3": "value3"}

    def test_merge_configs_override_takes_precedence(self) -> None:
        """merge_configs should give override values precedence."""
        base = {"key1": "base_value"}
        override = {"key1": "override_value"}
        merge_configs(base, override)

        assert base == {"key1": "override_value"}

    def test_merge_configs_nested_dicts(self) -> None:
        """merge_configs should deep-merge nested dictionaries."""
        base = {"models": {"planning": "gpt-4", "execution": "gpt-3.5"}}
        override = {"models": {"execution": "claude-3"}}
        merge_configs(base, override)

        assert base == {"models": {"planning": "gpt-4", "execution": "claude-3"}}

    def test_merge_configs_nested_adds_new_keys(self) -> None:
        """merge_configs should add new keys in nested dicts."""
        base = {"models": {"planning": "gpt-4"}}
        override = {"models": {"execution": "gpt-3.5"}}
        merge_configs(base, override)

        assert base == {"models": {"planning": "gpt-4", "execution": "gpt-3.5"}}

    def test_merge_configs_deep_nesting(self) -> None:
        """merge_configs should handle deeply nested dictionaries."""
        base = {"level1": {"level2": {"level3": {"key": "base_value"}}}}
        override = {"level1": {"level2": {"level3": {"key": "override_value"}}}}
        merge_configs(base, override)

        assert base == {"level1": {"level2": {"level3": {"key": "override_value"}}}}

    def test_merge_configs_mixed_types(self) -> None:
        """merge_configs should handle mixed data types."""
        base = {
            "models": {"planning": "gpt-4"},
            "timeout": 30,
            "enabled": True,
            "list_value": [1, 2, 3],
        }
        override = {"models": {"execution": "gpt-3.5"}, "timeout": 60}
        merge_configs(base, override)

        assert base == {
            "models": {"planning": "gpt-4", "execution": "gpt-3.5"},
            "timeout": 60,
            "enabled": True,
            "list_value": [1, 2, 3],
        }

    def test_merge_configs_empty_override(self) -> None:
        """merge_configs should handle empty override dict."""
        base = {"key": "value"}
        override = {}
        merge_configs(base, override)

        assert base == {"key": "value"}

    def test_merge_configs_empty_base(self) -> None:
        """merge_configs should populate empty base dict."""
        base = {}
        override = {"key": "value"}
        merge_configs(base, override)

        assert base == {"key": "value"}

    def test_merge_configs_modifies_in_place(self) -> None:
        """merge_configs should modify base dict in-place."""
        base = {"key1": "value1"}
        original_base = base
        override = {"key2": "value2"}
        merge_configs(base, override)

        assert base is original_base
        assert base == {"key1": "value1", "key2": "value2"}

    def test_merge_configs_preserves_override_nested_structure(self) -> None:
        """merge_configs should preserve nested structure from override."""
        base = {"config": {"setting1": "value1"}}
        override = {
            "config": {"setting2": {"nested": "value"}},
            "other": {"nested": {"deep": "value"}},
        }
        merge_configs(base, override)

        assert base == {
            "config": {
                "setting1": "value1",
                "setting2": {"nested": "value"},
            },
            "other": {"nested": {"deep": "value"}},
        }


@pytest.mark.unit
class TestInvalidYamlHandling:
    """Test config loader's handling of invalid YAML."""

    def test_load_config_with_invalid_local_yaml(self, tmp_path: Path) -> None:
        """load_config should handle invalid YAML in local config gracefully."""
        # Create invalid YAML in local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
invalid: [unclosed
  list syntax
"""
        )

        # Should raise an error when trying to parse invalid YAML
        with pytest.raises(yaml.YAMLError):
            load_config(tmp_path, "test-project")

    def test_load_config_with_invalid_global_yaml(self, tmp_path: Path) -> None:
        """load_config should handle invalid YAML in global config gracefully."""
        # Create invalid YAML in global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
bad: yaml: file:
  - unclosed
"""
        )

        # Should raise an error when trying to parse invalid YAML
        with (
            pytest.raises(yaml.YAMLError),
            patch("jiro.config.loader.Path.home", return_value=tmp_path),
        ):
            load_config(tmp_path, "test-project")

    def test_load_config_with_invalid_project_yaml(self, tmp_path: Path) -> None:
        """load_config should handle invalid YAML in project config gracefully."""
        # Create invalid YAML in project config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: unquoted: string: with: colons
"""
        )

        # Should raise an error when trying to parse invalid YAML
        with (
            pytest.raises(yaml.YAMLError),
            patch("jiro.config.loader.Path.home", return_value=tmp_path),
        ):
            load_config(tmp_path, "test-project")

    def test_load_config_recovers_with_valid_global_after_invalid_local(
        self, tmp_path: Path
    ) -> None:
        """load_config should use lower-level configs even if higher-level has invalid YAML.

        This tests the principle that invalid YAML in one level should
        ideally not prevent loading from other levels. However, since
        yaml.safe_load throws exceptions, this documents current behavior.
        """
        # Create valid global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
commands:
  test: "global-test-command"
"""
        )

        # Create invalid local config
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
invalid: [unclosed list
"""
        )

        # Currently, invalid YAML raises an error immediately
        with pytest.raises(yaml.YAMLError):
            load_config(tmp_path, "test-project")


@pytest.mark.unit
class TestLoadConfigWithSources:
    """Test config source tracking functionality."""

    def test_load_config_with_sources_returns_tuple(self, tmp_path: Path) -> None:
        """load_config_with_sources should return a tuple of Config and sources dict."""
        result = load_config_with_sources(tmp_path, "test-project")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], Config)
        assert isinstance(result[1], dict)

    def test_load_config_with_sources_tracks_defaults(self, tmp_path: Path) -> None:
        """load_config_with_sources should track default values as 'default' source."""
        config, sources = load_config_with_sources(tmp_path, "test-project")

        # When no config files exist, all values should come from defaults
        assert sources.get("models.planning") == "default"
        assert sources.get("models.execution") == "default"
        assert sources.get("models.review") == "default"
        assert sources.get("commands.test") == "default"
        assert sources.get("commands.lint") == "default"
        assert sources.get("commands.lint_fix") == "default"
        assert sources.get("conventions.test_file_pattern") == "default"
        assert sources.get("preflight.skip_if_recent_minutes") == "default"

    def test_load_config_with_sources_tracks_global_source(self, tmp_path: Path) -> None:
        """load_config_with_sources should track values from global config."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
  execution: "global-execution-model"
commands:
  test: "global-test-command"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify global config sources
        assert sources.get("models.planning") == "global"
        assert sources.get("models.execution") == "global"
        assert sources.get("commands.test") == "global"
        # Unspecified keys should still be default
        assert sources.get("models.review") == "default"
        assert sources.get("commands.lint") == "default"

    def test_load_config_with_sources_tracks_project_source(self, tmp_path: Path) -> None:
        """load_config_with_sources should track values from project config."""
        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
commands:
  lint: "project-lint-command"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify project config sources
        assert sources.get("models.planning") == "project"
        assert sources.get("commands.lint") == "project"
        # Unspecified keys should still be default
        assert sources.get("models.execution") == "default"
        assert sources.get("commands.test") == "default"

    def test_load_config_with_sources_tracks_local_source(self, tmp_path: Path) -> None:
        """load_config_with_sources should track values from local config."""
        # Create local config file
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
conventions:
  test_file_pattern: "local_test_{name}.py"
"""
        )

        config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify local config sources
        assert sources.get("models.planning") == "local"
        assert sources.get("conventions.test_file_pattern") == "local"
        # Unspecified keys should still be default
        assert sources.get("models.execution") == "default"
        assert sources.get("commands.test") == "default"

    def test_load_config_with_sources_precedence_local_over_project(self, tmp_path: Path) -> None:
        """load_config_with_sources should track local as source when it overrides project."""
        # Create project scope config
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
  execution: "project-execution-model"
"""
        )

        # Create local config file that overrides one value
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify precedence: local source for overridden value, project for others
        assert sources.get("models.planning") == "local"
        assert sources.get("models.execution") == "project"

    def test_load_config_with_sources_full_precedence_chain(self, tmp_path: Path) -> None:
        """load_config_with_sources should track sources across all precedence levels."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
  execution: "global-execution-model"
  review: "global-review-model"
commands:
  test: "global-test-command"
  lint: "global-lint-command"
"""
        )

        # Create project scope config that overrides some values
        config_dir = tmp_path / ".jiro-dreams-of-code" / "test-project"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
models:
  planning: "project-planning-model"
commands:
  lint: "project-lint-command"
preflight:
  skip_if_recent_minutes: 45
"""
        )

        # Create local config that overrides more values
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
commands:
  test: "local-test-command"
conventions:
  test_file_pattern: "local_test_{name}.py"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify full precedence chain
        assert sources.get("models.planning") == "local"  # overridden by local
        assert sources.get("models.execution") == "global"  # from global only
        assert sources.get("models.review") == "global"  # from global only
        assert sources.get("commands.test") == "local"  # overridden by local
        assert sources.get("commands.lint") == "project"  # from project (not in local)
        assert sources.get("conventions.test_file_pattern") == "local"  # from local
        assert sources.get("preflight.skip_if_recent_minutes") == "project"  # from project

    def test_load_config_with_sources_values_correct(self, tmp_path: Path) -> None:
        """load_config_with_sources should return correct config values with source tracking."""
        # Create global config
        global_config_dir = tmp_path / ".jiro-dreams-of-code"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_file = global_config_dir / "config.yaml"
        global_config_file.write_text(
            """
models:
  planning: "global-planning-model"
commands:
  test: "global-test-command"
"""
        )

        # Create local config
        local_config_file = tmp_path / ".jiro-dreams-of-code.yaml"
        local_config_file.write_text(
            """
models:
  planning: "local-planning-model"
"""
        )

        with patch("jiro.config.loader.Path.home", return_value=tmp_path):
            config, sources = load_config_with_sources(tmp_path, "test-project")

        # Verify both config values and sources are correct
        assert config.models.planning == "local-planning-model"
        assert sources.get("models.planning") == "local"

        assert config.commands.test == "global-test-command"
        assert sources.get("commands.test") == "global"

        assert config.models.execution == "claude-3-5-haiku-20241022"
        assert sources.get("models.execution") == "default"
