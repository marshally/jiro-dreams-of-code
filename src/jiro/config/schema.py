"""Configuration schema for jiro."""

from dataclasses import dataclass, field


@dataclass
class ModelsConfig:
    """Configuration for AI models used by different agents."""

    planning: str = "claude-opus-4-20250514"
    execution: str = "claude-3-5-haiku-20241022"
    review: str = "claude-sonnet-4-20250514"


@dataclass
class CommandsConfig:
    """Configuration for shell commands."""

    test: str = "pytest"
    lint: str = "ruff check"
    lint_fix: str = "ruff check --fix"


@dataclass
class ConventionsConfig:
    """Configuration for project conventions."""

    test_file_pattern: str = "test_{name}.py"


@dataclass
class PreflightConfig:
    """Configuration for preflight checks."""

    skip_if_recent_minutes: int = 60


@dataclass
class SlackConfig:
    """Configuration for Slack notifications."""

    webhook_url: str | None = None
    channel: str | None = None
    notify_on: list[str] = field(
        default_factory=lambda: [
            "session_started",
            "task_completed",
            "session_completed",
            "session_failed",
            "intervention_required",
        ]
    )


@dataclass
class EmailConfig:
    """Configuration for Email notifications."""

    smtp_host: str | None = None
    smtp_port: int = 587
    sender_email: str | None = None
    recipients: list[str] = field(default_factory=list)
    smtp_username: str | None = None
    smtp_password: str | None = None
    notify_on: list[str] = field(
        default_factory=lambda: [
            "session_started",
            "task_completed",
            "session_completed",
            "session_failed",
            "intervention_required",
        ]
    )


@dataclass
class Config:
    """Main configuration for jiro."""

    models: ModelsConfig = field(default_factory=ModelsConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    conventions: ConventionsConfig = field(default_factory=ConventionsConfig)
    preflight: PreflightConfig = field(default_factory=PreflightConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
