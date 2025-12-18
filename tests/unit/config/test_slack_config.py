"""Tests for Slack configuration."""

from jiro.config.schema import Config, SlackConfig


class TestSlackConfig:
    """Tests for SlackConfig dataclass."""

    def test_slack_config_default_creation(self):
        """SlackConfig should be creatable with default values."""
        config = SlackConfig()
        assert config.webhook_url is None
        assert config.channel is None
        assert len(config.notify_on) == 5

    def test_slack_config_with_webhook_url(self):
        """SlackConfig should accept webhook_url."""
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        config = SlackConfig(webhook_url=webhook_url)
        assert config.webhook_url == webhook_url

    def test_slack_config_with_channel(self):
        """SlackConfig should accept channel override."""
        config = SlackConfig(channel="#alerts")
        assert config.channel == "#alerts"

    def test_slack_config_with_notify_on(self):
        """SlackConfig should accept custom notify_on list."""
        events = ["session_started", "task_completed"]
        config = SlackConfig(notify_on=events)
        assert config.notify_on == events

    def test_slack_config_default_notify_on_events(self):
        """SlackConfig should have default notify_on events."""
        config = SlackConfig()
        expected_events = [
            "session_started",
            "task_completed",
            "session_completed",
            "session_failed",
            "intervention_required",
        ]
        assert config.notify_on == expected_events


class TestConfigIncludesSlack:
    """Tests for Config integration with Slack."""

    def test_config_includes_slack_config(self):
        """Config should include slack configuration."""
        config = Config()
        assert hasattr(config, "slack")
        assert isinstance(config.slack, SlackConfig)

    def test_config_slack_defaults(self):
        """Config slack should have default SlackConfig."""
        config = Config()
        assert config.slack.webhook_url is None
        assert config.slack.channel is None
