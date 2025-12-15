"""Bug Red step type.

This module implements the Bug Red phase: reproducing the bug with a failing test.

Classes:
    BugRedCommand: Spawns subagent to create failing bug reproduction test
    BugRedVerify: Verifies test meets bug red requirements
    BugRedCommit: Creates git commit with 🐛 emoji
    BugRedResult: Result dataclass with test details
"""

from jiro.steps.bug.red.bug_red_command import BugRedCommand
from jiro.steps.bug.red.bug_red_commit import BugRedCommit
from jiro.steps.bug.red.bug_red_result import BugRedResult
from jiro.steps.bug.red.bug_red_verify import BugRedVerify

__all__ = [
    "BugRedCommand",
    "BugRedResult",
    "BugRedVerify",
    "BugRedCommit",
]
