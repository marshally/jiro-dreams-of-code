"""Tests for ExecutionStep orchestrator."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from jiro.commands.base import Command
from jiro.commits.base import Commit, CommitResult
from jiro.db.models import Session
from jiro.results.base import Result
from jiro.steps.execution_step import ExecutionStep
from jiro.steps.types import PlanStep, StepType
from jiro.trackers.interface import Task
from jiro.verifications.base import Verification, VerificationResult


@dataclass
class MockResult(Result):
    """Mock result for testing."""

    test_value: str = "test"


class MockCommand(Command):
    """Mock command for testing."""

    tools: ClassVar[list[type]] = []
    output_schema: ClassVar[type] = MockResult

    async def execute(self, *, step: PlanStep, task: Task) -> MockResult:
        return MockResult(changed_files=[Path("test.py")], test_value="executed")


class MockVerification(Verification):
    """Mock verification for testing."""

    def verify(self, *, result: Result) -> VerificationResult:
        return VerificationResult(
            success=True,
            verification_command="mock verify",
            verification_output="passed",
            verification_time=0.1,
        )


class MockCommit(Commit):
    """Mock commit for testing."""

    def create(
        self,
        *,
        result: Result,
        verification: VerificationResult,
        e2e_time: float,
    ) -> CommitResult:
        return CommitResult(sha="abc123", message=f"test commit (e2e: {e2e_time:.2f}s)")


class TestExecutionStepInit:
    """Tests for ExecutionStep initialization."""

    def test_init_stores_step_type(self):
        """ExecutionStep should store step_type."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()

        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        assert step.step_type == StepType.TDD_RED

    def test_init_stores_session(self):
        """ExecutionStep should store session."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()

        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        assert step.session == session

    def test_init_stores_db(self):
        """ExecutionStep should store db."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()

        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        assert step.db == db


class TestExecutionStepFactory:
    """Tests for ExecutionStep.for_type factory method."""

    def test_for_type_creates_execution_step(self):
        """for_type should create an ExecutionStep instance."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()

        step = ExecutionStep.for_type(
            step_type=StepType.TDD_GREEN,
            session=session,
            db=db,
        )

        assert isinstance(step, ExecutionStep)
        assert step.step_type == StepType.TDD_GREEN

    def test_for_type_accepts_kwargs(self):
        """for_type should accept keyword arguments."""
        session = Session(
            id="session-2",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()

        step = ExecutionStep.for_type(
            step_type=StepType.DOCUMENTATION,
            session=session,
            db=db,
        )

        assert step.session.id == "session-2"


class TestExecutionStepProperties:
    """Tests for ExecutionStep command/verify/commit properties."""

    def test_command_property_uses_discovery(self):
        """command property should use discover_command."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        with patch("jiro.steps.execution_step.discover_command") as mock_discover:
            mock_discover.return_value = MockCommand()
            cmd = step.command
            mock_discover.assert_called_once_with(StepType.TDD_RED)
            assert isinstance(cmd, Command)

    def test_verify_property_uses_discovery(self):
        """verify property should use discover_verification."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.TDD_GREEN,
            session=session,
            db=db,
        )

        with patch("jiro.steps.execution_step.discover_verification") as mock_discover:
            mock_discover.return_value = MockVerification()
            verifier = step.verify
            mock_discover.assert_called_once_with(StepType.TDD_GREEN)
            assert isinstance(verifier, Verification)

    def test_commit_property_uses_discovery(self):
        """commit property should use discover_commit."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.LINT_FIX,
            session=session,
            db=db,
        )

        with patch("jiro.steps.execution_step.discover_commit") as mock_discover:
            mock_discover.return_value = MockCommit()
            committer = step.commit
            mock_discover.assert_called_once_with(StepType.LINT_FIX)
            assert isinstance(committer, Commit)


class TestExecutionStepExecute:
    """Tests for ExecutionStep.execute method."""

    @pytest.mark.asyncio
    async def test_execute_calls_command_verify_commit_in_order(self):
        """execute should call command → verify → commit in order."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        plan_step = PlanStep(step_type=StepType.TDD_RED, planning_context="Write test")
        task = Task(
            id="task-1",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )

        call_order = []

        async def mock_execute(*, step, task):
            call_order.append("command")
            return MockResult(changed_files=[Path("test.py")])

        def mock_verify(*, result):
            call_order.append("verify")
            return VerificationResult(
                success=True,
                verification_command="test",
                verification_output="ok",
                verification_time=0.1,
            )

        def mock_create(*, result, verification, e2e_time):
            call_order.append("commit")
            return CommitResult(sha="abc", message="test")

        with (
            patch("jiro.steps.execution_step.discover_command") as mock_cmd,
            patch("jiro.steps.execution_step.discover_verification") as mock_ver,
            patch("jiro.steps.execution_step.discover_commit") as mock_com,
        ):
            mock_cmd.return_value.execute = mock_execute
            mock_ver.return_value.verify = mock_verify
            mock_com.return_value.create = mock_create

            await step.execute(plan_step=plan_step, task=task)

        assert call_order == ["command", "verify", "commit"]

    @pytest.mark.asyncio
    async def test_execute_returns_commit_result(self):
        """execute should return CommitResult."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        plan_step = PlanStep(step_type=StepType.TDD_RED, planning_context="Write test")
        task = Task(
            id="task-1",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )

        with (
            patch("jiro.steps.execution_step.discover_command") as mock_cmd,
            patch("jiro.steps.execution_step.discover_verification") as mock_ver,
            patch("jiro.steps.execution_step.discover_commit") as mock_com,
        ):
            mock_cmd.return_value = MockCommand()
            mock_ver.return_value = MockVerification()
            mock_com.return_value = MockCommit()

            result = await step.execute(plan_step=plan_step, task=task)

        assert isinstance(result, CommitResult)
        assert result.sha == "abc123"

    @pytest.mark.asyncio
    async def test_execute_passes_e2e_time_to_commit(self):
        """execute should measure and pass e2e_time to commit."""
        session = Session(
            id="session-1",
            branch_name="feature/test",
            status="running",
            started_at=datetime.now(),
        )
        db = MagicMock()
        step = ExecutionStep(
            step_type=StepType.TDD_RED,
            session=session,
            db=db,
        )

        plan_step = PlanStep(step_type=StepType.TDD_RED, planning_context="Write test")
        task = Task(
            id="task-1",
            title="Test task",
            task_type="task",
            status="in_progress",
            created_at=datetime.now(),
        )

        captured_e2e_time = None

        def mock_create(*, result, verification, e2e_time):
            nonlocal captured_e2e_time
            captured_e2e_time = e2e_time
            return CommitResult(sha="abc", message="test")

        with (
            patch("jiro.steps.execution_step.discover_command") as mock_cmd,
            patch("jiro.steps.execution_step.discover_verification") as mock_ver,
            patch("jiro.steps.execution_step.discover_commit") as mock_com,
        ):
            mock_cmd.return_value = MockCommand()
            mock_ver.return_value = MockVerification()
            mock_com.return_value.create = mock_create

            await step.execute(plan_step=plan_step, task=task)

        assert captured_e2e_time is not None
        assert captured_e2e_time >= 0
