"""Tests for ConfigResult dataclass."""

from pathlib import Path

from jiro.results.base import Result
from jiro.steps.config.config_result import ConfigResult


class TestConfigResultIsResult:
    """Test that ConfigResult is a proper Result subclass."""

    def test_is_result_subclass(self):
        """ConfigResult should inherit from Result."""
        assert issubclass(ConfigResult, Result)

    def test_can_instantiate(self):
        """Should be able to instantiate ConfigResult."""
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.5,
        )
        assert isinstance(result, ConfigResult)
        assert result.config_files_changed == 1


class TestConfigResultAttributes:
    """Test ConfigResult attributes."""

    def test_has_changed_files(self):
        """Should have changed_files attribute."""
        result = ConfigResult(
            changed_files=[Path("config.yaml"), Path("settings.json")],
            config_files_changed=2,
            config_types=["yaml", "json"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert len(result.changed_files) == 2
        assert Path("config.yaml") in result.changed_files

    def test_config_files_count(self):
        """Should track config file count."""
        result = ConfigResult(
            changed_files=[
                Path("config.yaml"),
                Path("settings.toml"),
                Path(".env"),
            ],
            config_files_changed=3,
            config_types=["yaml", "toml", "env"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.config_files_changed == 3
        assert len(result.config_types) == 3

    def test_config_types(self):
        """Should track config file types."""
        result = ConfigResult(
            changed_files=[Path("config.yaml"), Path("config.json")],
            config_files_changed=2,
            config_types=["yaml", "json"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert "yaml" in result.config_types
        assert "json" in result.config_types
        assert len(result.config_types) == 2

    def test_subagent_metrics(self):
        """Should track subagent metrics."""
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=2.5,
        )
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 2.5


class TestConfigResultSerialization:
    """Test serialization methods inherited from Result."""

    def test_as_dict(self):
        """Should convert to dictionary."""
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        d = result.as_dict()
        assert isinstance(d, dict)
        assert d["config_files_changed"] == 1
        assert d["changed_files"] == ["config.yaml"]

    def test_as_json(self):
        """Should convert to JSON."""
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        json_str = result.as_json()
        assert isinstance(json_str, str)
        assert "config_files_changed" in json_str
        assert "1" in json_str
