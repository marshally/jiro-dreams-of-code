"""Tests for Email configuration."""

from jiro.config.schema import Config, EmailConfig


class TestEmailConfig:
    """Tests for EmailConfig dataclass."""

    def test_email_config_default_creation(self):
        """EmailConfig should be creatable with default values."""
        config = EmailConfig()
        assert config.smtp_host is None
        assert config.smtp_port == 587
        assert config.sender_email is None
        assert config.recipients == []
        assert config.smtp_username is None
        assert config.smtp_password is None
        assert len(config.notify_on) == 5

    def test_email_config_with_smtp_host(self):
        """EmailConfig should accept smtp_host."""
        config = EmailConfig(smtp_host="smtp.example.com")
        assert config.smtp_host == "smtp.example.com"

    def test_email_config_with_smtp_port(self):
        """EmailConfig should accept custom SMTP port."""
        config = EmailConfig(smtp_port=465)
        assert config.smtp_port == 465

    def test_email_config_with_sender_email(self):
        """EmailConfig should accept sender_email."""
        config = EmailConfig(sender_email="bot@example.com")
        assert config.sender_email == "bot@example.com"

    def test_email_config_with_recipients(self):
        """EmailConfig should accept recipients list."""
        recipients = ["user1@example.com", "user2@example.com"]
        config = EmailConfig(recipients=recipients)
        assert config.recipients == recipients

    def test_email_config_with_credentials(self):
        """EmailConfig should accept SMTP credentials."""
        config = EmailConfig(
            smtp_username="user",
            smtp_password="pass",
        )
        assert config.smtp_username == "user"
        assert config.smtp_password == "pass"

    def test_email_config_with_notify_on(self):
        """EmailConfig should accept custom notify_on list."""
        events = ["session_completed", "session_failed"]
        config = EmailConfig(notify_on=events)
        assert config.notify_on == events

    def test_email_config_default_notify_on_events(self):
        """EmailConfig should have default notify_on events."""
        config = EmailConfig()
        expected_events = [
            "session_started",
            "task_completed",
            "session_completed",
            "session_failed",
            "intervention_required",
        ]
        assert config.notify_on == expected_events

    def test_email_config_full_configuration(self):
        """EmailConfig should accept all parameters."""
        recipients = ["alert@example.com"]
        config = EmailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=recipients,
            smtp_username="bot@example.com",
            smtp_password="app-password",
            notify_on=["session_completed", "session_failed"],
        )
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.sender_email == "bot@example.com"
        assert config.recipients == recipients
        assert config.smtp_username == "bot@example.com"
        assert config.smtp_password == "app-password"
        assert config.notify_on == ["session_completed", "session_failed"]


class TestConfigIncludesEmail:
    """Tests for Config integration with Email."""

    def test_config_includes_email_config(self):
        """Config should include email configuration."""
        config = Config()
        assert hasattr(config, "email")
        assert isinstance(config.email, EmailConfig)

    def test_config_email_defaults(self):
        """Config email should have default EmailConfig."""
        config = Config()
        assert config.email.smtp_host is None
        assert config.email.smtp_port == 587
        assert config.email.sender_email is None
        assert config.email.recipients == []
