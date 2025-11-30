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
