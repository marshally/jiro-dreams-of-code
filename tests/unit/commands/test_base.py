"""Tests for Command ABC."""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import pytest

from jiro.commands.base import Command
from jiro.results.base import Result
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task


class TestCommandABC:
    """Tests for Command abstract base class."""

    def test_command_is_abc(self):
        """Command should be an abstract base class."""
        assert issubclass(Command, ABC)

    def test_command_cannot_be_instantiated_directly(self):
        """Command should not be instantiable directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Command()  # type: ignore[abstract]

    def test_command_has_tools_class_attribute(self):
        """Command should define tools as a class variable annotation."""
        assert "tools" in Command.__annotations__

    def test_command_has_output_schema_class_attribute(self):
        """Command should define output_schema as a class variable annotation."""
        assert "output_schema" in Command.__annotations__

    def test_command_has_execute_abstract_method(self):
        """Command should have abstract execute method."""
        assert hasattr(Command, "execute")
        assert getattr(Command.execute, "__isabstractmethod__", False)


class TestCommandSubclass:
    """Tests for Command subclass implementation."""

    def test_subclass_must_implement_execute(self):
        """Subclass must implement execute method."""

        class IncompleteCommand(Command):
            tools: ClassVar[list[type]] = []
            output_schema: ClassVar[type] = Result

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCommand()  # type: ignore[abstract]

    def test_subclass_can_implement_command(self):
        """Subclass can properly implement Command."""

        @dataclass
        class TestResult(Result):
            test_name: str

        class TestCommand(Command):
            tools: ClassVar[list[type]] = [str, int]  # Placeholder types for testing
            output_schema: ClassVar[type] = TestResult

            def execute(self, *, step: PlanStep, task: Task) -> TestResult:
                return TestResult(
                    changed_files=[Path("test.py")],
                    test_name="test_example",
                )

        cmd = TestCommand()
        assert cmd.tools == [str, int]
        assert cmd.output_schema == TestResult

    def test_execute_receives_step_and_task(self):
        """execute() should receive step and task parameters."""

        @dataclass
        class TestResult(Result):
            received_step_type: str
            received_task_id: str

        class TestCommand(Command):
            tools: ClassVar[list[type]] = []
            output_schema: ClassVar[type] = TestResult

            def execute(self, *, step: PlanStep, task: Task) -> TestResult:
                return TestResult(
                    changed_files=[],
                    received_step_type=str(step.step_type),
                    received_task_id=task.id,
                )

        cmd = TestCommand()
        step = PlanStep(step_type=StepType.TDD_RED, planning_context="Write test")
        task = Task(
            id="task-123",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )

        result = cmd.execute(step=step, task=task)
        assert result.received_step_type == "tdd_red"
        assert result.received_task_id == "task-123"

    def test_execute_returns_result(self):
        """execute() should return a Result instance."""

        class TestCommand(Command):
            tools: ClassVar[list[type]] = []
            output_schema: ClassVar[type] = Result

            def execute(self, *, step: PlanStep, task: Task) -> Result:
                return Result(changed_files=[Path("src/foo.py")])

        cmd = TestCommand()
        step = PlanStep(step_type=StepType.TDD_GREEN, planning_context="Implement")
        task = Task(
            id="task-456",
            title="Another task",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
        )

        result = cmd.execute(step=step, task=task)
        assert isinstance(result, Result)
        assert result.changed_files == [Path("src/foo.py")]
