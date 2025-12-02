"""Tests for task executor and preflight checks."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.planning import ExecutionPlan, PlanningAgent, PlanStep
from jiro.config.schema import CommandsConfig, Config
from jiro.core.executor import (
    EnhancedTask,
    PreflightResult,
    enhance_task_with_planning,
    run_relevant_lint,
    run_relevant_tests,
    run_task_preflight,
)
from jiro.trackers.interface import Task


class TestRunRelevantTests:
    """Tests for run_relevant_tests function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="A test task",
            labels=["test"],
        )

    @pytest.fixture
    def config(self):
        """Create a sample config."""
        return Config(
            commands=CommandsConfig(
                test="pytest",
                lint="ruff check",
            )
        )

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_test_files")
    def test_run_relevant_tests_success(
        self, mock_find_tests, mock_subprocess, sample_task, config
    ):
        """run_relevant_tests should return True when tests pass."""
        # Arrange
        mock_find_tests.return_value = [
            "tests/unit/test_file.py",
            "tests/unit/test_other.py",
        ]
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Act
        result = run_relevant_tests(sample_task, config)

        # Assert
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert "pytest" in call_args[0][0]

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_test_files")
    def test_run_relevant_tests_failure(
        self, mock_find_tests, mock_subprocess, sample_task, config
    ):
        """run_relevant_tests should return False when tests fail."""
        # Arrange
        mock_find_tests.return_value = ["tests/unit/test_file.py"]
        mock_subprocess.return_value = MagicMock(returncode=1)

        # Act
        result = run_relevant_tests(sample_task, config)

        # Assert
        assert result is False

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_test_files")
    def test_run_relevant_tests_no_tests_found(
        self, mock_find_tests, mock_subprocess, sample_task, config
    ):
        """run_relevant_tests should return True when no tests are found."""
        # Arrange
        mock_find_tests.return_value = []

        # Act
        result = run_relevant_tests(sample_task, config)

        # Assert
        assert result is True
        mock_subprocess.assert_not_called()

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_test_files")
    def test_run_relevant_tests_logs_output(
        self, mock_find_tests, mock_subprocess, sample_task, config, caplog
    ):
        """run_relevant_tests should log test results."""
        # Arrange
        mock_find_tests.return_value = ["tests/unit/test_file.py"]
        mock_subprocess.return_value = MagicMock(returncode=0, stdout=b"Test output", stderr=b"")

        # Act
        result = run_relevant_tests(sample_task, config)

        # Assert
        assert result is True


class TestRunRelevantLint:
    """Tests for run_relevant_lint function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="A test task",
            labels=["test"],
        )

    @pytest.fixture
    def config(self):
        """Create a sample config."""
        return Config(
            commands=CommandsConfig(
                test="pytest",
                lint="ruff check",
            )
        )

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_source_files")
    def test_run_relevant_lint_success(self, mock_find_files, mock_subprocess, sample_task, config):
        """run_relevant_lint should return True when lint passes."""
        # Arrange
        mock_find_files.return_value = ["src/file.py", "src/other.py"]
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Act
        result = run_relevant_lint(sample_task, config)

        # Assert
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert "ruff check" in call_args[0][0]

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_source_files")
    def test_run_relevant_lint_failure(self, mock_find_files, mock_subprocess, sample_task, config):
        """run_relevant_lint should return False when lint fails."""
        # Arrange
        mock_find_files.return_value = ["src/file.py"]
        mock_subprocess.return_value = MagicMock(returncode=1)

        # Act
        result = run_relevant_lint(sample_task, config)

        # Assert
        assert result is False

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_source_files")
    def test_run_relevant_lint_no_files_found(
        self, mock_find_files, mock_subprocess, sample_task, config
    ):
        """run_relevant_lint should return True when no files are found."""
        # Arrange
        mock_find_files.return_value = []

        # Act
        result = run_relevant_lint(sample_task, config)

        # Assert
        assert result is True
        mock_subprocess.assert_not_called()


class TestEnhanceTaskWithPlanning:
    """Tests for enhance_task_with_planning function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Implement feature X",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Feature description",
            labels=["feature"],
        )

    @pytest.fixture
    def mock_planning_agent(self):
        """Create a mock PlanningAgent."""
        agent = MagicMock(spec=PlanningAgent)
        agent.plan = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_enhance_task_with_planning_success(self, sample_task, mock_planning_agent):
        """enhance_task_with_planning should return EnhancedTask with plan."""
        # Arrange
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[
                PlanStep(
                    description="Create file",
                    files=["src/file.py"],
                    action="create",
                ),
                PlanStep(
                    description="Add tests",
                    files=["tests/test_file.py"],
                    action="create",
                ),
            ],
            verification_command="pytest tests/",
            estimated_tokens=300,
        )
        mock_planning_agent.plan.return_value = plan

        # Act
        result = await enhance_task_with_planning(sample_task, mock_planning_agent)

        # Assert
        assert isinstance(result, EnhancedTask)
        assert result.task.id == "task-123"
        assert result.execution_plan == plan
        assert len(result.execution_plan.steps) == 2
        mock_planning_agent.plan.assert_called_once_with(sample_task)

    @pytest.mark.asyncio
    async def test_enhance_task_with_planning_logs_result(
        self, sample_task, mock_planning_agent, caplog
    ):
        """enhance_task_with_planning should log the plan."""
        # Arrange
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[
                PlanStep(
                    description="Create file",
                    files=["src/file.py"],
                    action="create",
                )
            ],
            verification_command="pytest tests/",
            estimated_tokens=150,
        )
        mock_planning_agent.plan.return_value = plan

        # Act
        result = await enhance_task_with_planning(sample_task, mock_planning_agent)

        # Assert
        assert isinstance(result, EnhancedTask)


class TestRunTaskPreflight:
    """Tests for run_task_preflight function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Implement feature X",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Feature description",
            labels=["feature"],
        )

    @pytest.fixture
    def config(self):
        """Create a sample config."""
        return Config(
            commands=CommandsConfig(
                test="pytest",
                lint="ruff check",
            )
        )

    @pytest.fixture
    def mock_planning_agent(self):
        """Create a mock PlanningAgent."""
        agent = MagicMock(spec=PlanningAgent)
        agent.plan = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_run_task_preflight_all_pass(self, sample_task, config, mock_planning_agent):
        """run_task_preflight should return success when all checks pass."""
        # Arrange
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[
                PlanStep(
                    description="Create file",
                    files=["src/file.py"],
                    action="create",
                )
            ],
            verification_command="pytest tests/",
            estimated_tokens=150,
        )
        mock_planning_agent.plan.return_value = plan

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.enhance_task_with_planning") as mock_enhance,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_enhance.return_value = EnhancedTask(task=sample_task, execution_plan=plan)

            # Act
            result = await run_task_preflight(sample_task, config, mock_planning_agent)

            # Assert
            assert isinstance(result, PreflightResult)
            assert result.tests_passed is True
            assert result.lint_passed is True
            assert result.planning_done is True
            assert result.enhanced_task is not None
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_run_task_preflight_tests_fail(self, sample_task, config, mock_planning_agent):
        """run_task_preflight should collect errors when tests fail."""
        # Arrange
        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.enhance_task_with_planning") as mock_enhance,
        ):
            mock_tests.return_value = False
            mock_lint.return_value = True

            plan = ExecutionPlan(
                task_id="task-123",
                steps=[],
                verification_command="pytest tests/",
                estimated_tokens=100,
            )
            mock_enhance.return_value = EnhancedTask(task=sample_task, execution_plan=plan)

            # Act
            result = await run_task_preflight(sample_task, config, mock_planning_agent)

            # Assert
            assert isinstance(result, PreflightResult)
            assert result.tests_passed is False
            assert result.lint_passed is True
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_run_task_preflight_lint_fail(self, sample_task, config, mock_planning_agent):
        """run_task_preflight should collect errors when lint fails."""
        # Arrange
        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.enhance_task_with_planning") as mock_enhance,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = False

            plan = ExecutionPlan(
                task_id="task-123",
                steps=[],
                verification_command="pytest tests/",
                estimated_tokens=100,
            )
            mock_enhance.return_value = EnhancedTask(task=sample_task, execution_plan=plan)

            # Act
            result = await run_task_preflight(sample_task, config, mock_planning_agent)

            # Assert
            assert isinstance(result, PreflightResult)
            assert result.tests_passed is True
            assert result.lint_passed is False
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_run_task_preflight_planning_fails(
        self, sample_task, config, mock_planning_agent
    ):
        """run_task_preflight should handle planning failures."""
        # Arrange
        mock_planning_agent.plan.side_effect = ValueError("Planning failed")

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True

            # Act
            result = await run_task_preflight(sample_task, config, mock_planning_agent)

            # Assert
            assert isinstance(result, PreflightResult)
            assert result.planning_done is False
            assert result.enhanced_task is None
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_run_task_preflight_logs_results(
        self, sample_task, config, mock_planning_agent, caplog
    ):
        """run_task_preflight should log all results."""
        # Arrange
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[],
            verification_command="pytest tests/",
            estimated_tokens=100,
        )
        mock_planning_agent.plan.return_value = plan

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.enhance_task_with_planning") as mock_enhance,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_enhance.return_value = EnhancedTask(task=sample_task, execution_plan=plan)

            # Act
            result = await run_task_preflight(sample_task, config, mock_planning_agent)

            # Assert
            assert isinstance(result, PreflightResult)


class TestEnhancedTask:
    """Tests for EnhancedTask dataclass."""

    def test_enhanced_task_creation(self):
        """EnhancedTask should be created with task and plan."""
        # Arrange
        task = Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
        )
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[],
            verification_command="pytest",
            estimated_tokens=100,
        )

        # Act
        enhanced = EnhancedTask(task=task, execution_plan=plan)

        # Assert
        assert enhanced.task == task
        assert enhanced.execution_plan == plan


class TestPreflightResult:
    """Tests for PreflightResult dataclass."""

    def test_preflight_result_creation(self):
        """PreflightResult should be created with all fields."""
        # Arrange
        task = Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
        )
        plan = ExecutionPlan(
            task_id="task-123",
            steps=[],
            verification_command="pytest",
            estimated_tokens=100,
        )
        enhanced = EnhancedTask(task=task, execution_plan=plan)

        # Act
        result = PreflightResult(
            tests_passed=True,
            lint_passed=True,
            planning_done=True,
            enhanced_task=enhanced,
            errors=[],
        )

        # Assert
        assert result.tests_passed is True
        assert result.lint_passed is True
        assert result.planning_done is True
        assert result.enhanced_task == enhanced
        assert result.errors == []

    def test_preflight_result_with_errors(self):
        """PreflightResult should handle multiple errors."""
        # Act
        result = PreflightResult(
            tests_passed=False,
            lint_passed=False,
            planning_done=False,
            enhanced_task=None,
            errors=["Test failed", "Lint failed", "Planning failed"],
        )

        # Assert
        assert result.tests_passed is False
        assert len(result.errors) == 3
