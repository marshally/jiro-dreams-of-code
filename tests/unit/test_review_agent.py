"""Tests for ReviewAgent."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.review import ReviewAgent
from jiro.config.schema import Config
from jiro.trackers.interface import Task


class TestReviewAgentInitialization:
    """Tests for ReviewAgent initialization."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_config(self):
        """Create a sample config."""
        return Config()

    @pytest.mark.unit
    def test_initialization_requires_client(self, sample_config):
        """ReviewAgent.__init__ should require client."""
        with pytest.raises(TypeError):
            ReviewAgent(None, sample_config)

    @pytest.mark.unit
    def test_initialization_requires_config(self, mock_client):
        """ReviewAgent.__init__ should require config."""
        with pytest.raises(TypeError):
            ReviewAgent(mock_client, None)

    @pytest.mark.unit
    def test_initialization_success(self, mock_client, sample_config):
        """ReviewAgent should initialize with client and config."""
        agent = ReviewAgent(mock_client, sample_config)
        assert agent.client == mock_client
        assert agent.config == sample_config


class TestDeterministicChecks:
    """Tests for deterministic checks (tests and lint)."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_config(self):
        """Create a sample config."""
        return Config()

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test feature",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Test description",
        )

    @pytest.mark.asyncio
    async def test_deterministic_checks_run_first(self, mock_client, sample_config, sample_task):
        """review() should run deterministic checks first."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {})
            mock_client.execute.return_value = AgentResult(
                success=True,
                output="APPROVED",
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            # Act
            await agent.review(commit_sha, sample_task)

            # Assert
            mock_checks.assert_called_once()

    @pytest.mark.asyncio
    async def test_halt_on_test_failure(self, mock_client, sample_config, sample_task):
        """review() should HALT if tests fail."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (False, {"tests": "FAILED - exit code 1"})

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert result.halt is True
            assert result.passed is False
            assert "tests" in result.checks
            assert result.reason == "Deterministic checks failed"

    @pytest.mark.asyncio
    async def test_halt_on_lint_failure(self, mock_client, sample_config, sample_task):
        """review() should HALT if linting fails."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (
                False,
                {"lint": "FAILED - code style issues"},
            )

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert result.halt is True
            assert result.passed is False
            assert "lint" in result.checks


class TestLLMReview:
    """Tests for LLM-based code review."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_config(self):
        """Create a sample config."""
        return Config()

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test feature",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Test description",
        )

    @pytest.mark.asyncio
    async def test_llm_review_runs_after_deterministic_pass(
        self, mock_client, sample_config, sample_task
    ):
        """review() should run LLM review after deterministic checks pass."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {"tests": "PASSED", "lint": "PASSED"})
            mock_client.execute.return_value = AgentResult(
                success=True,
                output="APPROVED: Code follows best practices",
                tokens_before=100,
                tokens_after=300,
                error=None,
            )

            # Act
            await agent.review(commit_sha, sample_task)

            # Assert
            mock_client.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_halt_on_llm_rejection(self, mock_client, sample_config, sample_task):
        """review() should HALT if LLM rejects the code."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {"tests": "PASSED", "lint": "PASSED"})
            mock_client.execute.return_value = AgentResult(
                success=True,
                output="REJECTED: Missing error handling in exception cases",
                tokens_before=100,
                tokens_after=300,
                error=None,
            )

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert result.halt is True
            assert result.passed is False
            assert result.reason == "LLM review rejected changes"

    @pytest.mark.asyncio
    async def test_llm_error_is_reported(self, mock_client, sample_config, sample_task):
        """review() should handle LLM execution errors."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {"tests": "PASSED", "lint": "PASSED"})
            mock_client.execute.return_value = AgentResult(
                success=False,
                output="",
                tokens_before=100,
                tokens_after=100,
                error="API connection failed",
            )

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert result.halt is True
            assert result.passed is False


class TestSuccessPath:
    """Tests for successful review."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_config(self):
        """Create a sample config."""
        return Config()

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Test feature",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Test description",
        )

    @pytest.mark.asyncio
    async def test_success_when_all_checks_pass(self, mock_client, sample_config, sample_task):
        """review() should succeed when all checks pass."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {"tests": "PASSED", "lint": "PASSED"})
            mock_client.execute.return_value = AgentResult(
                success=True,
                output="APPROVED: Code looks good",
                tokens_before=100,
                tokens_after=300,
                error=None,
            )

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert result.passed is True
            assert result.halt is False
            assert result.reason == "All checks passed"
            assert result.checks["tests"] == "PASSED"
            assert result.checks["lint"] == "PASSED"

    @pytest.mark.asyncio
    async def test_review_result_structure(self, mock_client, sample_config, sample_task):
        """ReviewResult should contain all required fields."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        commit_sha = "abc123def456"

        with patch("jiro.agents.review.ReviewAgent._run_deterministic_checks") as mock_checks:
            mock_checks.return_value = (True, {"tests": "PASSED", "lint": "PASSED"})
            mock_client.execute.return_value = AgentResult(
                success=True,
                output="APPROVED",
                tokens_before=100,
                tokens_after=300,
                error=None,
            )

            # Act
            result = await agent.review(commit_sha, sample_task)

            # Assert
            assert hasattr(result, "passed")
            assert hasattr(result, "halt")
            assert hasattr(result, "reason")
            assert hasattr(result, "checks")
            assert isinstance(result.checks, dict)
