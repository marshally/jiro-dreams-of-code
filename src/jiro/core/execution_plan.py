"""Execution plan schema for planning agent output.

This module defines the structured schema for execution plans that the planning
agent outputs. These plans provide specific file paths, line numbers, and
step-by-step instructions for the execution agent.
"""

import json
from dataclasses import dataclass, field
from typing import Literal

# Valid step types matching commit types
StepType = Literal[
    "docs",
    "tdd_red",
    "tdd_green",
    "tdd_refactor",
    "lint_fix",
    "bug_fix",
    "config",
    "test_only",
    "performance",
]

# Valid file actions
FileActionType = Literal["create", "modify", "delete"]


@dataclass
class FileAction:
    """Describes an action to take on a file.

    Provides specific guidance for the execution agent about what file
    to modify and where within the file to make changes.
    """

    path: str
    action: FileActionType
    content_hints: str | None = None
    location: str | None = None  # e.g., "line 27" or "function main()"

    def to_dict(self) -> dict:
        """Serialize to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "path": self.path,
            "action": self.action,
            "content_hints": self.content_hints,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileAction":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            FileAction instance.
        """
        return cls(
            path=data["path"],
            action=data["action"],
            content_hints=data.get("content_hints"),
            location=data.get("location"),
        )


@dataclass
class ExecutionStep:
    """A single step in an execution plan.

    Each step represents an atomic unit of work that should result in
    a single commit. Steps are ordered and should be executed sequentially.
    """

    description: str
    step_type: StepType
    files: list[FileAction] = field(default_factory=list)
    verification_command: str | None = None

    def to_dict(self) -> dict:
        """Serialize to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "description": self.description,
            "step_type": self.step_type,
            "files": [f.to_dict() for f in self.files],
            "verification_command": self.verification_command,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionStep":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            ExecutionStep instance.
        """
        return cls(
            description=data["description"],
            step_type=data["step_type"],
            files=[FileAction.from_dict(f) for f in data.get("files", [])],
            verification_command=data.get("verification_command"),
        )


@dataclass
class ExecutionPlanSchema:
    """The complete execution plan for a task.

    This schema is used by the planning agent to output structured plans
    that the execution agent can follow. Plans contain ordered steps,
    each with specific file actions and verification commands.

    Note: This is the in-memory schema representation. For database storage,
    see jiro.db.models.ExecutionPlan which stores the serialized JSON.
    """

    task_id: str
    steps: list[ExecutionStep] = field(default_factory=list)
    estimated_tokens: int | None = None

    def to_dict(self) -> dict:
        """Serialize to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "task_id": self.task_id,
            "steps": [s.to_dict() for s in self.steps],
            "estimated_tokens": self.estimated_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionPlanSchema":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            ExecutionPlanSchema instance.
        """
        return cls(
            task_id=data["task_id"],
            steps=[ExecutionStep.from_dict(s) for s in data.get("steps", [])],
            estimated_tokens=data.get("estimated_tokens"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlanSchema":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            ExecutionPlanSchema instance.
        """
        return cls.from_dict(json.loads(json_str))
