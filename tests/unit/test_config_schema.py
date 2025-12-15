"""Tests for configuration schema."""

import pytest

from jiro.config.schema import (
    CommandsConfig,
    Config,
    ConventionsConfig,
    ModelsConfig,
    PreflightConfig,
)


class TestModelsConfig:
    """Tests for ModelsConfig dataclass."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        """Models should have sensible defaults."""
        config = ModelsConfig()
        assert config.planning == "claude-opus-4-20250514"
        assert config.execution == "claude-3-5-haiku-20241022"
        assert config.review == "claude-sonnet-4-20250514"

    @pytest.mark.unit
    def test_custom_values(self) -> None:
        """Custom model values should be used."""
        config = ModelsConfig(
            planning="custom-planning",
            execution="custom-execution",
            review="custom-review",
        )
        assert config.planning == "custom-planning"
        assert config.execution == "custom-execution"
        assert config.review == "custom-review"


class TestCommandsConfig:
    """Tests for CommandsConfig dataclass."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        """Commands should have sensible defaults."""
        config = CommandsConfig()
        assert config.test == "pytest"
        assert config.lint == "ruff check"
        assert config.lint_fix == "ruff check --fix"

    @pytest.mark.unit
    def test_custom_values(self) -> None:
        """Custom command values should be used."""
        config = CommandsConfig(
            test="uv run pytest",
            lint="uv run ruff check",
            lint_fix="uv run ruff check --fix",
        )
        assert config.test == "uv run pytest"
        assert config.lint == "uv run ruff check"
        assert config.lint_fix == "uv run ruff check --fix"


class TestConventionsConfig:
    """Tests for ConventionsConfig dataclass."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        """Conventions should have sensible defaults."""
        config = ConventionsConfig()
        assert config.test_file_pattern == "test_{name}.py"

    @pytest.mark.unit
    def test_custom_values(self) -> None:
        """Custom convention values should be used."""
        config = ConventionsConfig(test_file_pattern="{name}_test.py")
        assert config.test_file_pattern == "{name}_test.py"


class TestPreflightConfig:
    """Tests for PreflightConfig dataclass."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        """Preflight should have sensible defaults."""
        config = PreflightConfig()
        assert config.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_custom_values(self) -> None:
        """Custom preflight values should be used."""
        config = PreflightConfig(skip_if_recent_minutes=30)
        assert config.skip_if_recent_minutes == 30


class TestConfig:
    """Tests for main Config dataclass."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        """Config should have sensible defaults for all nested configs."""
        config = Config()
        # Check nested configs have defaults
        assert isinstance(config.models, ModelsConfig)
        assert isinstance(config.commands, CommandsConfig)
        assert isinstance(config.conventions, ConventionsConfig)
        assert isinstance(config.preflight, PreflightConfig)
        # Verify default values propagate
        assert config.models.planning == "claude-opus-4-20250514"
        assert config.commands.test == "pytest"
        assert config.conventions.test_file_pattern == "test_{name}.py"
        assert config.preflight.skip_if_recent_minutes == 60

    @pytest.mark.unit
    def test_custom_nested_configs(self) -> None:
        """Custom nested configs should be used."""
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
    def test_all_fields_have_type_hints(self) -> None:
        """All fields should have type hints."""
        from typing import get_type_hints

        # Check Config
        hints = get_type_hints(Config)
        assert "models" in hints
        assert "commands" in hints
        assert "conventions" in hints
        assert "preflight" in hints

        # Check nested configs
        models_hints = get_type_hints(ModelsConfig)
        assert "planning" in models_hints
        assert "execution" in models_hints
        assert "review" in models_hints

        commands_hints = get_type_hints(CommandsConfig)
        assert "test" in commands_hints
        assert "lint" in commands_hints
        assert "lint_fix" in commands_hints

        conventions_hints = get_type_hints(ConventionsConfig)
        assert "test_file_pattern" in conventions_hints

        preflight_hints = get_type_hints(PreflightConfig)
        assert "skip_if_recent_minutes" in preflight_hints
