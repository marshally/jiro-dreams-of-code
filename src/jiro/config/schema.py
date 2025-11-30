"""Configuration schema for jiro."""

from dataclasses import dataclass, field


@dataclass
class ModelsConfig:
    """Configuration for AI models used by different agents."""

    planning: str = "claude-opus-4-5-20250514"
    execution: str = "claude-haiku-4-5-20250514"
    review: str = "claude-sonnet-4-5-20250514"


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
class Config:
    """Main configuration for jiro."""

    models: ModelsConfig = field(default_factory=ModelsConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    conventions: ConventionsConfig = field(default_factory=ConventionsConfig)
    preflight: PreflightConfig = field(default_factory=PreflightConfig)
