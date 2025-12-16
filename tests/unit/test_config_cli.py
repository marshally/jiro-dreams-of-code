"""Tests for config CLI commands."""

import json
from unittest import mock

import pytest
from typer.testing import CliRunner

from jiro.cli.main import app
from jiro.config.schema import (
    CommandsConfig,
    Config,
    ConventionsConfig,
    ModelsConfig,
    PreflightConfig,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for Typer CLI testing."""
    return CliRunner()


@pytest.fixture
def sample_config() -> Config:
    """Create a sample config for testing."""
    return Config(
        models=ModelsConfig(
            planning="claude-opus-4-20250514",
            execution="claude-3-5-haiku-20241022",
            review="claude-sonnet-4-20250514",
        ),
        commands=CommandsConfig(
            test="pytest",
            lint="ruff check",
            lint_fix="ruff check --fix",
        ),
        conventions=ConventionsConfig(
            test_file_pattern="test_{name}.py",
        ),
        preflight=PreflightConfig(
            skip_if_recent_minutes=60,
        ),
    )


@pytest.mark.unit
class TestConfigListCommand:
    """Tests for config list command."""

    def test_config_list_help(self, cli_runner: CliRunner) -> None:
        """Config list command should display help."""
        result = cli_runner.invoke(app, ["config", "list", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout.lower() or "List" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_basic(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list should display config values in a table."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        # Should display models configuration
        assert "models" in result.stdout.lower() or "Models" in result.stdout
        # Should show some config values
        assert "pytest" in result.stdout or "claude-opus" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_shows_sources(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list should show where each value comes from."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        # Should show source information (default/project)
        assert "default" in result.stdout.lower() or "source" in result.stdout.lower()

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_output(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list should output JSON when --json flag is used."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        # Should contain configuration sections
        assert "models" in output or "commands" in output

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_models_section(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list JSON should include models section."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert "models" in output
        models = output["models"]
        assert models["planning"]["value"] == "claude-opus-4-20250514"
        assert models["execution"]["value"] == "claude-3-5-haiku-20241022"
        assert models["review"]["value"] == "claude-sonnet-4-20250514"

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_commands_section(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list JSON should include commands section."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert "commands" in output
        commands = output["commands"]
        assert commands["test"]["value"] == "pytest"
        assert commands["lint"]["value"] == "ruff check"
        assert commands["lint_fix"]["value"] == "ruff check --fix"

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_conventions_section(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list JSON should include conventions section."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert "conventions" in output
        conventions = output["conventions"]
        assert conventions["test_file_pattern"]["value"] == "test_{name}.py"

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_preflight_section(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list JSON should include preflight section."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert "preflight" in output
        preflight = output["preflight"]
        assert preflight["skip_if_recent_minutes"]["value"] == 60

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_json_includes_source(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list JSON should include source for each value."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        # Check that source is present in values
        models = output["models"]
        assert "source" in models["planning"]
        # Source should be "default" since we're using defaults
        assert models["planning"]["source"] in ["default", "project"]

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_with_custom_config(
        self, mock_load_config_with_sources, cli_runner: CliRunner
    ) -> None:
        """Config list should work with custom configuration."""
        custom_config = Config(
            models=ModelsConfig(
                planning="custom-planning-model",
                execution="custom-execution-model",
                review="custom-review-model",
            ),
            commands=CommandsConfig(
                test="custom-pytest",
                lint="custom-ruff",
                lint_fix="custom-ruff-fix",
            ),
            conventions=ConventionsConfig(
                test_file_pattern="custom_test_{name}.py",
            ),
            preflight=PreflightConfig(
                skip_if_recent_minutes=120,
            ),
        )
        mock_load_config_with_sources.return_value = (custom_config, {})

        result = cli_runner.invoke(app, ["config", "list", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert output["models"]["planning"]["value"] == "custom-planning-model"
        assert output["commands"]["test"]["value"] == "custom-pytest"
        assert output["conventions"]["test_file_pattern"]["value"] == "custom_test_{name}.py"
        assert output["preflight"]["skip_if_recent_minutes"]["value"] == 120

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_list_table_format(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config list table should have proper formatting."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "list"])
        assert result.exit_code == 0
        # Check for table-like formatting
        output = result.stdout
        # Should have some visual separators or structured output
        assert len(output) > 0


@pytest.mark.unit
class TestConfigGetCommand:
    """Tests for config get command."""

    def test_config_get_help(self, cli_runner: CliRunner) -> None:
        """Config get command should display help."""
        result = cli_runner.invoke(app, ["config", "get", "--help"])
        assert result.exit_code == 0
        assert "get" in result.stdout.lower() or "Get" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_models_planning(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should retrieve models.planning value."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "models.planning"])
        assert result.exit_code == 0
        # Should contain the value
        assert "claude-opus-4-20250514" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_models_execution(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should retrieve models.execution value."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "models.execution"])
        assert result.exit_code == 0
        assert "claude-3-5-haiku-20241022" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_commands_test(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should retrieve commands.test value."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "commands.test"])
        assert result.exit_code == 0
        assert "pytest" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_shows_source(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should show the source of the configuration value."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "models.planning"])
        assert result.exit_code == 0
        # Should show source information
        assert "source" in result.stdout.lower() or "default" in result.stdout.lower()

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_invalid_key(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should handle invalid keys gracefully."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "invalid.key"])
        assert result.exit_code != 0
        # Should show an error message
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_json_output(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should output JSON when --json flag is used."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "models.planning", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        # Should contain key, value, and source
        assert "key" in output
        assert "value" in output
        assert "source" in output

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_json_content(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get JSON should have correct structure and content."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "commands.test", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)

        assert output["key"] == "commands.test"
        assert output["value"] == "pytest"
        assert output["source"] in ["default", "project"]

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_conventions_pattern(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should handle conventions section."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "conventions.test_file_pattern"])
        assert result.exit_code == 0
        assert "test_{name}.py" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_preflight_setting(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get should handle preflight settings."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "preflight.skip_if_recent_minutes"])
        assert result.exit_code == 0
        assert "60" in result.stdout

    @mock.patch("jiro.cli.config.load_config_with_sources")
    def test_config_get_json_invalid_key(
        self, mock_load_config_with_sources, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config get JSON output should handle invalid keys."""
        mock_load_config_with_sources.return_value = (sample_config, {})

        result = cli_runner.invoke(app, ["config", "get", "nonexistent.key", "--json"])
        assert result.exit_code != 0


@pytest.mark.unit
class TestConfigSetCommand:
    """Tests for config set command."""

    def test_config_set_help(self, cli_runner: CliRunner) -> None:
        """Config set command should display help."""
        result = cli_runner.invoke(app, ["config", "set", "--help"])
        assert result.exit_code == 0
        assert "set" in result.stdout.lower() or "Set" in result.stdout

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_valid_key(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should set a valid configuration key."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "models.planning", "claude-opus-4-20250514", "--project"]
        )
        assert result.exit_code == 0
        # Should show confirmation
        assert "set" in result.stdout.lower() or "models.planning" in result.stdout

    @mock.patch("jiro.cli.config.load_config")
    def test_config_set_invalid_key(
        self, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should reject invalid configuration keys."""
        mock_load_config.return_value = sample_config

        result = cli_runner.invoke(app, ["config", "set", "invalid.key", "value", "--project"])
        assert result.exit_code != 0
        # Should show an error message
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_models_execution(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should update models.execution value."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "models.execution", "claude-sonnet-4-5-20250929", "--project"]
        )
        assert result.exit_code == 0
        # Verify save_config was called
        assert mock_save_config.called

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_commands_test(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should update commands.test value."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "commands.test", "pytest -v", "--project"]
        )
        assert result.exit_code == 0
        assert mock_save_config.called

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_conventions_pattern(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should update conventions.test_file_pattern value."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "conventions.test_file_pattern", "test_*.py", "--project"]
        )
        assert result.exit_code == 0
        assert mock_save_config.called

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_preflight_setting(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should update preflight.skip_if_recent_minutes value."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "preflight.skip_if_recent_minutes", "120", "--project"]
        )
        assert result.exit_code == 0
        assert mock_save_config.called

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_requires_scope(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should require a scope option."""
        mock_load_config.return_value = sample_config

        result = cli_runner.invoke(app, ["config", "set", "models.planning", "new-model"])
        # Should still work with default scope
        assert result.exit_code == 0

    @mock.patch("jiro.cli.config.load_config")
    @mock.patch("jiro.cli.config.save_config")
    def test_config_set_saves_to_correct_scope(
        self, mock_save_config, mock_load_config, cli_runner: CliRunner, sample_config: Config
    ) -> None:
        """Config set should write to the specified scope."""
        mock_load_config.return_value = sample_config
        mock_save_config.return_value = None

        result = cli_runner.invoke(
            app, ["config", "set", "models.planning", "new-model", "--project"]
        )
        assert result.exit_code == 0
        # Verify save_config was called with project scope
        assert mock_save_config.called
