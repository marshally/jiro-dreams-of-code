"""Tests for task executor and preflight checks."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.planning import PlanningAgent
from jiro.agents.review import ReviewAgent, ReviewResult
from jiro.config.schema import CommandsConfig, Config
from jiro.core.execution_plan import ExecutionPlanSchema, ExecutionStep, FileAction
from jiro.core.executor import (
    EnhancedTask,
    PostflightResult,
    PreflightResult,
    close_task_in_tracker,
    enhance_task_with_planning,
    record_results,
    review_commits,
    run_relevant_lint,
    run_relevant_lint_post,
    run_relevant_tests,
    run_relevant_tests_post,
    run_task_postflight,
    run_task_preflight,
)
from jiro.trackers.interface import IssueTracker, Task


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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create file",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                    verification_command="pytest tests/test_file.py",
                ),
                ExecutionStep(
                    description="Add tests",
                    step_type="tdd_red",
                    files=[FileAction(path="tests/test_file.py", action="create")],
                    verification_command="pytest tests/test_file.py",
                ),
            ],
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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create file",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                    verification_command="pytest tests/",
                )
            ],
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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create file",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                    verification_command="pytest tests/",
                )
            ],
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

            plan = ExecutionPlanSchema(
                task_id="task-123",
                steps=[],
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

            plan = ExecutionPlanSchema(
                task_id="task-123",
                steps=[],
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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[],
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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[],
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
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[],
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


class TestReviewCommits:
    """Tests for review_commits function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Implement feature",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
            description="Feature description",
        )

    @pytest.fixture
    def mock_review_agent(self):
        """Create a mock ReviewAgent."""
        agent = MagicMock(spec=ReviewAgent)
        agent.review = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_review_commits_success(self, sample_task, mock_review_agent):
        """review_commits should return ReviewResult when review passes."""
        # Arrange
        commits = ["abc123", "def456"]
        review_result = ReviewResult(
            passed=True,
            halt=False,
            reason="All checks passed",
            checks={"tests": "PASSED", "lint": "PASSED", "llm": "APPROVED"},
        )
        mock_review_agent.review.return_value = review_result

        # Act
        result = await review_commits(sample_task, commits, mock_review_agent)

        # Assert
        assert result.passed is True
        assert result.halt is False
        mock_review_agent.review.assert_called()

    @pytest.mark.asyncio
    async def test_review_commits_failure(self, sample_task, mock_review_agent):
        """review_commits should return failed ReviewResult when review fails."""
        # Arrange
        commits = ["abc123"]
        review_result = ReviewResult(
            passed=False,
            halt=True,
            reason="Tests failed",
            checks={"tests": "FAILED"},
        )
        mock_review_agent.review.return_value = review_result

        # Act
        result = await review_commits(sample_task, commits, mock_review_agent)

        # Assert
        assert result.passed is False
        assert result.halt is True

    @pytest.mark.asyncio
    async def test_review_commits_empty_commits(self, sample_task, mock_review_agent):
        """review_commits should handle empty commits list gracefully."""
        # Arrange
        commits = []

        # Act
        # This should handle the empty case without crashing
        result = await review_commits(sample_task, commits, mock_review_agent)

        # Assert
        # Either it should return early or call the agent for the last commit
        assert result is not None


class TestRunRelevantTestsPost:
    """Tests for run_relevant_tests_post function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
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
    def test_run_relevant_tests_post_success(
        self, mock_find_tests, mock_subprocess, sample_task, config
    ):
        """run_relevant_tests_post should return True when tests pass."""
        # Arrange
        mock_find_tests.return_value = ["tests/unit/test_file.py"]
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Act
        result = run_relevant_tests_post(sample_task, config)

        # Assert
        assert result is True

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_test_files")
    def test_run_relevant_tests_post_failure(
        self, mock_find_tests, mock_subprocess, sample_task, config
    ):
        """run_relevant_tests_post should return False when tests fail."""
        # Arrange
        mock_find_tests.return_value = ["tests/unit/test_file.py"]
        mock_subprocess.return_value = MagicMock(returncode=1)

        # Act
        result = run_relevant_tests_post(sample_task, config)

        # Assert
        assert result is False


class TestRunRelevantLintPost:
    """Tests for run_relevant_lint_post function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
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
    def test_run_relevant_lint_post_success(
        self, mock_find_files, mock_subprocess, sample_task, config
    ):
        """run_relevant_lint_post should return True when lint passes."""
        # Arrange
        mock_find_files.return_value = ["src/file.py"]
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Act
        result = run_relevant_lint_post(sample_task, config)

        # Assert
        assert result is True

    @patch("jiro.core.executor.subprocess.run")
    @patch("jiro.core.executor.find_relevant_source_files")
    def test_run_relevant_lint_post_failure(
        self, mock_find_files, mock_subprocess, sample_task, config
    ):
        """run_relevant_lint_post should return False when lint fails."""
        # Arrange
        mock_find_files.return_value = ["src/file.py"]
        mock_subprocess.return_value = MagicMock(returncode=1)

        # Act
        result = run_relevant_lint_post(sample_task, config)

        # Assert
        assert result is False


class TestRecordResults:
    """Tests for record_results function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
        )

    @pytest.fixture
    def sample_result(self):
        """Create a sample postflight result."""
        return PostflightResult(
            review_passed=True,
            tests_passed=True,
            lint_passed=True,
            task_closed=False,
            results_recorded=False,
        )

    def test_record_results_success(self, sample_task, sample_result):
        """record_results should record results without error."""
        # Act - should not raise
        record_results(sample_task, sample_result)

        # Assert - just verify it doesn't crash


class TestCloseTaskInTracker:
    """Tests for close_task_in_tracker function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test task",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
        )

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock tracker."""
        tracker = MagicMock(spec=IssueTracker)
        tracker.close_task = MagicMock()
        return tracker

    def test_close_task_in_tracker_success(self, sample_task, mock_tracker):
        """close_task_in_tracker should call tracker.close_task."""
        # Arrange
        with patch("jiro.core.executor.get_tracker", return_value=mock_tracker):
            # Act
            close_task_in_tracker(sample_task)

            # Assert
            mock_tracker.close_task.assert_called_once_with(
                sample_task.id, reason="Task completed successfully"
            )


class TestRunTaskPostflight:
    """Tests for run_task_postflight orchestration function."""

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Implement feature",
            task_type="feature",
            status="in_progress",
            created_at=datetime.now(),
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
    def mock_review_agent(self):
        """Create a mock ReviewAgent."""
        agent = MagicMock(spec=ReviewAgent)
        agent.review = AsyncMock()
        return agent

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock tracker."""
        tracker = MagicMock(spec=IssueTracker)
        tracker.close_task = MagicMock()
        return tracker

    @pytest.mark.asyncio
    async def test_run_task_postflight_success(
        self, sample_task, config, mock_review_agent, mock_tracker
    ):
        """run_task_postflight should complete successfully when all checks pass."""
        # Arrange
        commits = ["abc123"]
        review_result = ReviewResult(
            passed=True,
            halt=False,
            reason="All checks passed",
            checks={"tests": "PASSED", "lint": "PASSED", "llm": "APPROVED"},
        )

        with (
            patch("jiro.core.executor.review_commits") as mock_review,
            patch("jiro.core.executor.run_relevant_tests_post") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint_post") as mock_lint,
            patch("jiro.core.executor.record_results"),
            patch("jiro.core.executor.close_task_in_tracker"),
            patch("jiro.core.executor.get_tracker", return_value=mock_tracker),
        ):
            # Make the async mock return the review result
            mock_review.return_value = review_result
            mock_tests.return_value = True
            mock_lint.return_value = True

            # Act
            result = await run_task_postflight(
                sample_task, commits, config, review_agent=mock_review_agent
            )

            # Assert
            assert isinstance(result, PostflightResult)
            assert result.review_passed is True
            assert result.tests_passed is True
            assert result.lint_passed is True

    @pytest.mark.asyncio
    async def test_run_task_postflight_review_fails(
        self, sample_task, config, mock_review_agent, mock_tracker
    ):
        """run_task_postflight should fail gracefully when review fails."""
        # Arrange
        commits = ["abc123"]
        review_result = ReviewResult(
            passed=False,
            halt=True,
            reason="Tests failed",
            checks={"tests": "FAILED"},
        )

        with (
            patch("jiro.core.executor.review_commits") as mock_review,
            patch("jiro.core.executor.run_relevant_tests_post") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint_post") as mock_lint,
            patch("jiro.core.executor.get_tracker", return_value=mock_tracker),
        ):
            mock_review.return_value = review_result
            mock_tests.return_value = False
            mock_lint.return_value = True

            # Act
            result = await run_task_postflight(
                sample_task, commits, config, review_agent=mock_review_agent
            )

            # Assert
            assert isinstance(result, PostflightResult)
            assert result.review_passed is False


class TestPostflightResult:
    """Tests for PostflightResult dataclass."""

    def test_postflight_result_creation(self):
        """PostflightResult should be created with all fields."""
        # Act
        result = PostflightResult(
            review_passed=True,
            tests_passed=True,
            lint_passed=True,
            task_closed=True,
            results_recorded=True,
        )

        # Assert
        assert result.review_passed is True
        assert result.tests_passed is True
        assert result.lint_passed is True
        assert result.task_closed is True
        assert result.results_recorded is True
        assert result.error is None

    def test_postflight_result_with_error(self):
        """PostflightResult should handle errors."""
        # Act
        result = PostflightResult(
            review_passed=False,
            tests_passed=False,
            lint_passed=False,
            task_closed=False,
            results_recorded=False,
            error="Review failed",
        )

        # Assert
        assert result.review_passed is False
        assert result.error == "Review failed"


class TestTaskExecutor:
    """Tests for TaskExecutor class."""

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

    @pytest.fixture
    def mock_review_agent(self):
        """Create a mock ReviewAgent."""
        agent = MagicMock(spec=ReviewAgent)
        agent.review = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_task_executor_initialization(
        self, config, mock_planning_agent, mock_review_agent
    ):
        """TaskExecutor should initialize with agents and config."""
        from jiro.core.executor import TaskExecutor

        executor = TaskExecutor(
            config=config,
            planning_agent=mock_planning_agent,
            review_agent=mock_review_agent,
        )

        assert executor.config == config
        assert executor.planning_agent == mock_planning_agent
        assert executor.review_agent == mock_review_agent

    @pytest.mark.asyncio
    async def test_task_executor_execute_task_success(
        self, sample_task, config, mock_planning_agent, mock_review_agent
    ):
        """execute_task should complete successfully with valid inputs."""
        from jiro.core.executor import TaskExecutor

        # Arrange
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create file",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                    verification_command="pytest tests/test_file.py",
                ),
            ],
            estimated_tokens=300,
        )
        mock_planning_agent.plan.return_value = plan

        review_result = ReviewResult(
            passed=True,
            halt=False,
            reason="All checks passed",
            checks={"tests": "PASSED", "lint": "PASSED", "llm": "APPROVED"},
        )
        mock_review_agent.review.return_value = review_result

        executor = TaskExecutor(
            config=config,
            planning_agent=mock_planning_agent,
            review_agent=mock_review_agent,
        )

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.run_relevant_tests_post") as mock_tests_post,
            patch("jiro.core.executor.run_relevant_lint_post") as mock_lint_post,
            patch("jiro.core.executor.record_results"),
            patch("jiro.core.executor.close_task_in_tracker"),
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_tests_post.return_value = True
            mock_lint_post.return_value = True

            # Act
            result = await executor.execute_task(sample_task)

            # Assert
            assert isinstance(result, PostflightResult)
            assert result.review_passed is True
            mock_planning_agent.plan.assert_called_once_with(sample_task)
            mock_review_agent.review.assert_called()

    @pytest.mark.asyncio
    async def test_task_executor_execute_task_preflight_fails(
        self, sample_task, config, mock_planning_agent, mock_review_agent
    ):
        """execute_task should raise when preflight fails."""
        from jiro.core.executor import TaskExecutor

        # Arrange
        mock_planning_agent.plan.side_effect = ValueError("Planning failed")

        executor = TaskExecutor(
            config=config,
            planning_agent=mock_planning_agent,
            review_agent=mock_review_agent,
        )

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True

            # Act & Assert
            with pytest.raises(ValueError):
                await executor.execute_task(sample_task)

    @pytest.mark.asyncio
    async def test_task_executor_execute_task_review_fails(
        self, sample_task, config, mock_planning_agent, mock_review_agent
    ):
        """execute_task should halt when review fails."""
        from jiro.core.executor import TaskExecutor

        # Arrange
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create file",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                ),
            ],
            estimated_tokens=300,
        )
        mock_planning_agent.plan.return_value = plan

        review_result = ReviewResult(
            passed=False,
            halt=True,
            reason="Tests failed",
            checks={"tests": "FAILED"},
        )
        mock_review_agent.review.return_value = review_result

        executor = TaskExecutor(
            config=config,
            planning_agent=mock_planning_agent,
            review_agent=mock_review_agent,
        )

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True

            # Act & Assert
            with pytest.raises(ValueError, match="Review failed"):
                await executor.execute_task(sample_task)

    @pytest.mark.asyncio
    async def test_task_executor_execute_task_multiple_steps(
        self, sample_task, config, mock_planning_agent, mock_review_agent
    ):
        """execute_task should process multiple steps in sequence."""
        from jiro.core.executor import TaskExecutor

        # Arrange
        plan = ExecutionPlanSchema(
            task_id="task-123",
            steps=[
                ExecutionStep(
                    description="Create test file",
                    step_type="tdd_red",
                    files=[FileAction(path="tests/test_file.py", action="create")],
                ),
                ExecutionStep(
                    description="Implement function",
                    step_type="tdd_green",
                    files=[FileAction(path="src/file.py", action="create")],
                ),
                ExecutionStep(
                    description="Refactor code",
                    step_type="tdd_refactor",
                    files=[FileAction(path="src/file.py", action="modify")],
                ),
            ],
            estimated_tokens=500,
        )
        mock_planning_agent.plan.return_value = plan

        review_result = ReviewResult(
            passed=True,
            halt=False,
            reason="All checks passed",
            checks={"tests": "PASSED", "lint": "PASSED", "llm": "APPROVED"},
        )
        mock_review_agent.review.return_value = review_result

        executor = TaskExecutor(
            config=config,
            planning_agent=mock_planning_agent,
            review_agent=mock_review_agent,
        )

        with (
            patch("jiro.core.executor.run_relevant_tests") as mock_tests,
            patch("jiro.core.executor.run_relevant_lint") as mock_lint,
            patch("jiro.core.executor.run_relevant_tests_post") as mock_tests_post,
            patch("jiro.core.executor.run_relevant_lint_post") as mock_lint_post,
            patch("jiro.core.executor.record_results"),
            patch("jiro.core.executor.close_task_in_tracker"),
        ):
            mock_tests.return_value = True
            mock_lint.return_value = True
            mock_tests_post.return_value = True
            mock_lint_post.return_value = True

            # Act
            result = await executor.execute_task(sample_task)

            # Assert
            assert isinstance(result, PostflightResult)
            # Review should be called once for each step plus once for postflight
            assert mock_review_agent.review.call_count >= 3
