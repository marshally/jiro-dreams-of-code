"""TDD Red step type.

This module implements the TDD Red phase: creating a failing test.

Classes:
    TddRedCommand: Spawns subagent to create failing test
    TddRedVerify: Verifies test meets TDD red requirements
    TddRedCommit: Creates git commit with 🔴 emoji
    TddRedResult: Result dataclass with test details
"""

from jiro.steps.tdd.red.tdd_red_command import TddRedCommand
from jiro.steps.tdd.red.tdd_red_commit import TddRedCommit
from jiro.steps.tdd.red.tdd_red_result import TddRedResult
from jiro.steps.tdd.red.tdd_red_verify import TddRedVerify

__all__ = [
    "TddRedCommand",
    "TddRedResult",
    "TddRedVerify",
    "TddRedCommit",
]
