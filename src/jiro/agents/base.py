"""Base agent configuration and types."""

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for an agent.

    Defines the model, prompts, and permissions for running an agent
    via the Claude Agent SDK.
    """

    model: str
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=list)
    permission_mode: str = "acceptEdits"
    max_turns: int = 10


@dataclass
class AgentResult:
    """Result from running an agent.

    Captures success/failure, output, and token usage for tracking.
    """

    success: bool
    output: str
    tokens_before: int
    tokens_after: int
    error: str | None = None
