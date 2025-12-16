"""Integration tests for the complete TDD workflow.

This module tests the full TDD red -> green -> refactor cycle,
verifying that the ExecutionStep orchestrator correctly handles
each phase with proper verification and commit creation.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from jiro.commits.base import CommitResult
from jiro.steps.execution_step import ExecutionStep
from jiro.steps.tdd.green.tdd_green_result import TddGreenResult
from jiro.steps.tdd.red.tdd_red_result import TddRedResult
from jiro.steps.tdd.refactor.tdd_refactor_result import TddRefactorResult
from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import VerificationResult


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock session object."""
    session = MagicMock()
    session.session_id = "test-session-123"
    session.status = "in_progress"
    return session


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database object."""
    return MagicMock()


@pytest.fixture
def mock_task() -> MagicMock:
    """Create a mock task object."""
    task = MagicMock()
    task.id = "task-123"
    task.title = "Implement login validation"
    task.description = "Add email validation to login function"
    return task


@pytest.fixture
def mock_plan_step() -> MagicMock:
    """Create a mock plan step object."""
    step = MagicMock()
    step.step_type = StepType.TDD_RED
    step.context = {
        "feature": "User authentication",
        "requirement": "Email validation on login",
    }
    return step


@pytest.fixture
def mock_tdd_red_result() -> TddRedResult:
    """Create a realistic TDD red result."""
    return TddRedResult(
        changed_files=[Path("tests/test_auth.py")],
        test_file=Path("tests/test_auth.py"),
        test_name="test_login_validates_email",
        test_specifier="tests/test_auth.py::test_login_validates_email",
        test_output="FAILED - test requires implementation",
        subagent_type="claude-opus-4.5",
        subagent_prompt="Create a failing test for email validation",
        tokens_in=500,
        tokens_out=1200,
        subagent_time=2.5,
    )


@pytest.fixture
def mock_tdd_green_result() -> TddGreenResult:
    """Create a realistic TDD green result."""
    return TddGreenResult(
        changed_files=[Path("src/auth.py")],
        test_specifier="tests/test_auth.py::test_login_validates_email",
        test_output="PASSED - test now passes",
        implementation_files=[Path("src/auth.py")],
        subagent_type="claude-opus-4.5",
        subagent_prompt="Implement email validation in login function",
        tokens_in=800,
        tokens_out=1500,
        subagent_time=3.2,
    )


@pytest.fixture
def mock_tdd_refactor_result() -> TddRefactorResult:
    """Create a realistic TDD refactor result."""
    return TddRefactorResult(
        changed_files=[Path("src/auth.py")],
        test_specifier="tests/test_auth.py::test_login_validates_email",
        test_output="PASSED - all tests pass after refactoring",
        refactoring_type="extract_method",
        checksum="abc123def456",
        subagent_type="claude-opus-4.5",
        subagent_prompt="Refactor email validation to improve maintainability",
        tokens_in=700,
        tokens_out=1300,
        subagent_time=2.8,
    )


class TestTddWorkflowIntegration:
    """Integration tests for the complete TDD workflow."""

    @pytest.mark.integration
    def test_execution_step_for_type_creates_tdd_red(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test ExecutionStep.for_type creates correct step for TDD_RED.

        Verifies:
        - for_type() factory method works
        - step_type is set correctly
        - step properties are initialized
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        assert step is not None
        assert isinstance(step, ExecutionStep)
        assert step.step_type == StepType.TDD_RED
        assert step.session == mock_session
        assert step.db == mock_db

    @pytest.mark.integration
    def test_execution_step_discovers_command_verify_commit(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test ExecutionStep discovers correct Command/Verification/Commit.

        Verifies:
        - command property discovers correct class
        - verify property discovers correct class
        - commit property discovers correct class
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        # These should not raise and should return instances
        command = step.command
        verify = step.verify
        commit = step.commit

        assert command is not None
        assert verify is not None
        assert commit is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_red_step_creates_test_file_and_commits(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
    ) -> None:
        """Test TDD red step execution flow.

        Verifies:
        - Command executes and returns result
        - Verification passes
        - Commit creates with 🔴 emoji
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest -xvs",
            verification_output="test fails as expected",
            verification_time=1.5,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="abc123def456",
            message="🔴 Add failing test for test_login_validates_email",
        )

        # Patch the properties using PropertyMock
        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Execute the full workflow
            result = await step.execute(mock_plan_step, mock_task)

            # Verify result structure
            assert result is not None
            assert isinstance(result, CommitResult)
            assert result.sha == "abc123def456"
            assert "🔴" in result.message
            assert result.message.startswith("🔴")

            # Verify commit was called
            mock_commit_obj.create.assert_called_once()
            call_kwargs = mock_commit_obj.create.call_args.kwargs
            assert call_kwargs["result"] == mock_tdd_red_result
            assert call_kwargs["verification"].success is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_green_step_implements_and_commits(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_green_result: TddGreenResult,
    ) -> None:
        """Test TDD green step execution flow.

        Verifies:
        - Command executes and returns result
        - Verification passes (test now passes)
        - Commit creates with 🟢 emoji
        - Only implementation files are staged
        """
        mock_plan_step.step_type = StepType.TDD_GREEN

        step = ExecutionStep.for_type(
            StepType.TDD_GREEN,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_green_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest -xvs",
            verification_output="test now passes",
            verification_time=2.0,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="def456ghi789",
            message="🟢 Make tests/test_auth.py::test_login_validates_email pass",
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Execute the full workflow
            result = await step.execute(mock_plan_step, mock_task)

            # Verify result structure
            assert result is not None
            assert isinstance(result, CommitResult)
            assert result.sha == "def456ghi789"
            assert "🟢" in result.message
            assert result.message.startswith("🟢")

            # Verify commit was called with implementation files
            mock_commit_obj.create.assert_called_once()
            call_kwargs = mock_commit_obj.create.call_args.kwargs
            assert call_kwargs["result"] == mock_tdd_green_result
            assert call_kwargs["result"].changed_files == [Path("src/auth.py")]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_refactor_step_refactors_and_commits(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_refactor_result: TddRefactorResult,
    ) -> None:
        """Test TDD refactor step execution flow.

        Verifies:
        - Command executes and returns result
        - Verification passes (all tests still pass)
        - Commit creates with ♻️ emoji
        - Checksum is validated
        """
        mock_plan_step.step_type = StepType.TDD_REFACTOR

        step = ExecutionStep.for_type(
            StepType.TDD_REFACTOR,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_refactor_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest -xvs",
            verification_output="all tests pass after refactoring",
            verification_time=1.8,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="ghi789jkl012",
            message="♻️ Refactor: extract_method",
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Execute the full workflow
            result = await step.execute(mock_plan_step, mock_task)

            # Verify result structure
            assert result is not None
            assert isinstance(result, CommitResult)
            assert result.sha == "ghi789jkl012"
            assert "♻️" in result.message
            assert result.message.startswith("♻️")

            # Verify commit was called
            mock_commit_obj.create.assert_called_once()
            call_kwargs = mock_commit_obj.create.call_args.kwargs
            assert call_kwargs["result"] == mock_tdd_refactor_result
            assert call_kwargs["result"].checksum == "abc123def456"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_tdd_cycle_red_green_refactor(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
        mock_tdd_green_result: TddGreenResult,
        mock_tdd_refactor_result: TddRefactorResult,
    ) -> None:
        """Test complete TDD cycle: red -> green -> refactor.

        Verifies:
        - Each step executes in sequence
        - Results flow correctly between steps
        - Commits are created with correct emojis
        """
        commits = []

        # Step 1: RED
        red_step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="test fails",
            verification_time=1.0,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="red123",
            message="🔴 Add failing test",
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            red_result = await red_step.execute(mock_plan_step, mock_task)
            commits.append(red_result)

        # Step 2: GREEN
        mock_plan_step.step_type = StepType.TDD_GREEN
        green_step = ExecutionStep.for_type(
            StepType.TDD_GREEN,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_green_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="test passes",
            verification_time=1.5,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="green456",
            message="🟢 Make test pass",
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            green_result = await green_step.execute(mock_plan_step, mock_task)
            commits.append(green_result)

        # Step 3: REFACTOR
        mock_plan_step.step_type = StepType.TDD_REFACTOR
        refactor_step = ExecutionStep.for_type(
            StepType.TDD_REFACTOR,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_refactor_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="all tests pass",
            verification_time=1.2,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="refactor789",
            message="♻️ Refactor code",
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            refactor_result = await refactor_step.execute(mock_plan_step, mock_task)
            commits.append(refactor_result)

        # Verify all steps executed
        assert len(commits) == 3
        assert commits[0].message.startswith("🔴")
        assert commits[1].message.startswith("🟢")
        assert commits[2].message.startswith("♻️")
        assert commits[0].sha == "red123"
        assert commits[1].sha == "green456"
        assert commits[2].sha == "refactor789"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_red_verification_failure_raises_error(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
    ) -> None:
        """Test that verification failure halts execution.

        Verifies:
        - VerificationError is raised on failure
        - Execution stops before commit
        - Error contains failure details
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.side_effect = VerificationError(
            step_type=StepType.TDD_RED,
            rule_violated="Test does not fail",
            expected="Test to fail (exit code non-zero)",
            actual="Test passed (exit code 0)",
            details="A red test must fail to be correct",
        )
        mock_commit_obj = MagicMock()

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Verification should raise
            with pytest.raises(VerificationError) as exc_info:
                await step.execute(mock_plan_step, mock_task)

            # Commit should not be called
            mock_commit_obj.create.assert_not_called()

            # Error should contain details
            error = exc_info.value
            assert error.rule_violated == "Test does not fail"
            assert "failed" in str(error).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_green_verification_failure_raises_error(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_green_result: TddGreenResult,
    ) -> None:
        """Test TDD green verification failure halts execution.

        Verifies:
        - VerificationError raised when test doesn't pass
        - Commit is not created on verification failure
        """
        mock_plan_step.step_type = StepType.TDD_GREEN

        step = ExecutionStep.for_type(
            StepType.TDD_GREEN,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_green_result)
        mock_verify = MagicMock()
        mock_verify.verify.side_effect = VerificationError(
            step_type=StepType.TDD_GREEN,
            rule_violated="Test does not pass",
            expected="Test to pass (exit code 0)",
            actual="Test failed (exit code 1)",
            details="Implementation is incomplete",
        )
        mock_commit_obj = MagicMock()

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Verification should raise
            with pytest.raises(VerificationError) as exc_info:
                await step.execute(mock_plan_step, mock_task)

            # Commit should not be called
            mock_commit_obj.create.assert_not_called()

            # Error details
            error = exc_info.value
            assert error.step_type == StepType.TDD_GREEN
            assert "does not pass" in error.rule_violated

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tdd_refactor_verification_failure_raises_error(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_refactor_result: TddRefactorResult,
    ) -> None:
        """Test TDD refactor verification failure halts execution.

        Verifies:
        - VerificationError raised when tests break during refactoring
        - Commit is not created
        """
        mock_plan_step.step_type = StepType.TDD_REFACTOR

        step = ExecutionStep.for_type(
            StepType.TDD_REFACTOR,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_refactor_result)
        mock_verify = MagicMock()
        mock_verify.verify.side_effect = VerificationError(
            step_type=StepType.TDD_REFACTOR,
            rule_violated="Tests do not pass",
            expected="All tests to pass (exit code 0)",
            actual="Tests failed (exit code 1)",
            details="Refactoring broke some tests",
        )
        mock_commit_obj = MagicMock()

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            # Verification should raise
            with pytest.raises(VerificationError) as exc_info:
                await step.execute(mock_plan_step, mock_task)

            # Commit should not be called
            mock_commit_obj.create.assert_not_called()

            # Error details
            error = exc_info.value
            assert error.step_type == StepType.TDD_REFACTOR

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_commits_have_correct_emojis(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
        mock_tdd_green_result: TddGreenResult,
        mock_tdd_refactor_result: TddRefactorResult,
    ) -> None:
        """Test that commits use correct emoji prefixes.

        Verifies:
        - Red step uses 🔴 emoji
        - Green step uses 🟢 emoji
        - Refactor step uses ♻️ emoji
        """
        # Test RED emoji
        red_step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        red_emoji = "🔴"
        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="",
            verification_time=1.0,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(sha="red", message=f"{red_emoji} test")

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            result = await red_step.execute(mock_plan_step, mock_task)
            assert red_emoji in result.message

        # Test GREEN emoji
        mock_plan_step.step_type = StepType.TDD_GREEN
        green_step = ExecutionStep.for_type(
            StepType.TDD_GREEN,
            session=mock_session,
            db=mock_db,
        )

        green_emoji = "🟢"
        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_green_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="",
            verification_time=1.0,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="green", message=f"{green_emoji} test"
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            result = await green_step.execute(mock_plan_step, mock_task)
            assert green_emoji in result.message

        # Test REFACTOR emoji
        mock_plan_step.step_type = StepType.TDD_REFACTOR
        refactor_step = ExecutionStep.for_type(
            StepType.TDD_REFACTOR,
            session=mock_session,
            db=mock_db,
        )

        refactor_emoji = "♻️"
        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_refactor_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="",
            verification_time=1.0,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(
            sha="refactor", message=f"{refactor_emoji} test"
        )

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            result = await refactor_step.execute(mock_plan_step, mock_task)
            assert refactor_emoji in result.message

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execution_time_tracking(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
    ) -> None:
        """Test that execution time is tracked correctly.

        Verifies:
        - e2e_time is calculated and passed to commit
        - Verification time is captured
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="test output",
            verification_time=1.5,
        )
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(sha="abc", message="test")

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            await step.execute(mock_plan_step, mock_task)

            # Verify e2e_time was passed to commit
            mock_commit_obj.create.assert_called_once()
            call_kwargs = mock_commit_obj.create.call_args.kwargs
            assert "e2e_time" in call_kwargs
            assert isinstance(call_kwargs["e2e_time"], float)
            assert call_kwargs["e2e_time"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_verification_result_passed_to_commit(
        self,
        mock_session: MagicMock,
        mock_db: MagicMock,
        mock_task: MagicMock,
        mock_plan_step: MagicMock,
        mock_tdd_red_result: TddRedResult,
    ) -> None:
        """Test that verification result is passed to commit.

        Verifies:
        - VerificationResult is passed with correct fields
        - Commit receives verification details
        """
        step = ExecutionStep.for_type(
            StepType.TDD_RED,
            session=mock_session,
            db=mock_db,
        )

        verification_result = VerificationResult(
            success=True,
            verification_command="pytest -xvs tests/test_auth.py::test_login",
            verification_output="test output details",
            verification_time=2.3,
        )

        mock_command = MagicMock()
        mock_command.execute = AsyncMock(return_value=mock_tdd_red_result)
        mock_verify = MagicMock()
        mock_verify.verify.return_value = verification_result
        mock_commit_obj = MagicMock()
        mock_commit_obj.create.return_value = CommitResult(sha="abc", message="test")

        with (
            patch.object(
                ExecutionStep, "command", new_callable=PropertyMock, return_value=mock_command
            ),
            patch.object(
                ExecutionStep, "verify", new_callable=PropertyMock, return_value=mock_verify
            ),
            patch.object(
                ExecutionStep, "commit", new_callable=PropertyMock, return_value=mock_commit_obj
            ),
        ):
            await step.execute(mock_plan_step, mock_task)

            # Verify verification result was passed to commit
            mock_commit_obj.create.assert_called_once()
            call_kwargs = mock_commit_obj.create.call_args.kwargs
            assert call_kwargs["verification"] == verification_result
            assert call_kwargs["verification"].success is True
            assert call_kwargs["verification"].verification_time == 2.3
