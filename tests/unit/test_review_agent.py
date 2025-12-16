"""Tests for ReviewAgent."""

import subprocess
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


class TestDeterministicCheckMethods:
    """Tests for deterministic check helper methods."""

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

    @pytest.mark.asyncio
    async def test_run_tests_success(self, mock_client, sample_config):
        """_run_tests() should return True when tests pass."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Act
            result = agent._run_tests()

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_run_tests_failure(self, mock_client, sample_config):
        """_run_tests() should return False when tests fail."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            # Act
            result = agent._run_tests()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_run_tests_timeout(self, mock_client, sample_config):
        """_run_tests() should return False on timeout."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

            # Act
            result = agent._run_tests()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_run_tests_exception(self, mock_client, sample_config):
        """_run_tests() should return False on general exception."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")

            # Act
            result = agent._run_tests()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_run_lint_success(self, mock_client, sample_config):
        """_run_lint() should return True when lint passes."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Act
            result = agent._run_lint()

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_run_lint_failure(self, mock_client, sample_config):
        """_run_lint() should return False when lint fails."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            # Act
            result = agent._run_lint()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_run_lint_timeout(self, mock_client, sample_config):
        """_run_lint() should return False on timeout."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)

            # Act
            result = agent._run_lint()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_run_lint_exception(self, mock_client, sample_config):
        """_run_lint() should return False on general exception."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")

            # Act
            result = agent._run_lint()

            # Assert
            assert result is False

    @pytest.mark.unit
    def test_parse_llm_response_approved(self, mock_client, sample_config):
        """_parse_llm_response() should return True for APPROVED."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        # Act
        result = agent._parse_llm_response("APPROVED: Everything looks good")

        # Assert
        assert result is True

    @pytest.mark.unit
    def test_parse_llm_response_rejected(self, mock_client, sample_config):
        """_parse_llm_response() should return False for REJECTED."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        # Act
        result = agent._parse_llm_response("REJECTED: Missing error handling")

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_parse_llm_response_case_insensitive(self, mock_client, sample_config):
        """_parse_llm_response() should be case insensitive."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        # Act
        result1 = agent._parse_llm_response("approved: code is fine")
        result2 = agent._parse_llm_response("rejected: needs work")

        # Assert
        assert result1 is True
        assert result2 is False

    @pytest.mark.unit
    def test_parse_llm_response_default(self, mock_client, sample_config):
        """_parse_llm_response() should default to False for unclear response."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        # Act
        result = agent._parse_llm_response("Maybe this is fine?")

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_build_review_prompt(self, mock_client, sample_config):
        """_build_review_prompt() should build valid prompt with task context."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-123",
            title="Test feature",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Test description",
        )

        # Act
        prompt = agent._build_review_prompt("abc123", task)

        # Assert
        assert "task-123" in prompt
        assert "Test feature" in prompt
        assert "feature" in prompt
        assert "Test description" in prompt
        assert "abc123" in prompt
        # New format checks
        assert "passed" in prompt
        assert "JSON" in prompt

    @pytest.mark.unit
    def test_run_deterministic_checks_both_pass(self, mock_client, sample_config):
        """_run_deterministic_checks() should return True when both tests and lint pass."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Act
            passed, results = agent._run_deterministic_checks()

            # Assert
            assert passed is True
            assert results["tests"] == "PASSED"
            assert results["lint"] == "PASSED"

    @pytest.mark.unit
    def test_run_deterministic_checks_tests_fail(self, mock_client, sample_config):
        """_run_deterministic_checks() should return False when tests fail."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            # First call (tests) returns non-zero, second call (lint) returns 0
            mock_run.side_effect = [
                MagicMock(returncode=1),  # tests fail
                MagicMock(returncode=0),  # lint passes
            ]

            # Act
            passed, results = agent._run_deterministic_checks()

            # Assert
            assert passed is False
            assert results["tests"] == "FAILED"
            assert results["lint"] == "PASSED"

    @pytest.mark.unit
    def test_run_deterministic_checks_lint_fail(self, mock_client, sample_config):
        """_run_deterministic_checks() should return False when lint fails."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            # First call (tests) returns 0, second call (lint) returns non-zero
            mock_run.side_effect = [
                MagicMock(returncode=0),  # tests pass
                MagicMock(returncode=1),  # lint fails
            ]

            # Act
            passed, results = agent._run_deterministic_checks()

            # Assert
            assert passed is False
            assert results["tests"] == "PASSED"
            assert results["lint"] == "FAILED"

    @pytest.mark.unit
    def test_run_deterministic_checks_both_fail(self, mock_client, sample_config):
        """_run_deterministic_checks() should return False when both fail."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            # Act
            passed, results = agent._run_deterministic_checks()

            # Assert
            assert passed is False
            assert results["tests"] == "FAILED"
            assert results["lint"] == "FAILED"


class TestLLMResponseParsing:
    """Tests for LLM response parsing with JSON format."""

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
    def test_parse_json_response_passed(self, mock_client, sample_config):
        """_parse_llm_response() should parse JSON with passed: true."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        json_response = """{
  "passed": true,
  "concerns": [],
  "summary": "All changes match the commit message"
}"""

        # Act
        result = agent._parse_llm_response(json_response)

        # Assert
        assert result is True

    @pytest.mark.unit
    def test_parse_json_response_failed(self, mock_client, sample_config):
        """_parse_llm_response() should parse JSON with passed: false."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        json_response = """{
  "passed": false,
  "concerns": [
    {
      "severity": "error",
      "description": "Scope creep detected",
      "file": "src/unrelated.py"
    }
  ],
  "summary": "Changes exceed claimed scope"
}"""

        # Act
        result = agent._parse_llm_response(json_response)

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_parse_json_response_with_text(self, mock_client, sample_config):
        """_parse_llm_response() should extract JSON from mixed text."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        mixed_response = """Let me analyze this commit...

{"passed": true, "concerns": [], "summary": "Looks good"}

That's my review."""

        # Act
        result = agent._parse_llm_response(mixed_response)

        # Assert
        assert result is True

    @pytest.mark.unit
    def test_parse_legacy_approved_text(self, mock_client, sample_config):
        """_parse_llm_response() should handle legacy APPROVED text."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        text = "APPROVED: Code looks good and follows conventions."

        # Act
        result = agent._parse_llm_response(text)

        # Assert
        assert result is True

    @pytest.mark.unit
    def test_parse_legacy_rejected_text(self, mock_client, sample_config):
        """_parse_llm_response() should handle legacy REJECTED text."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        text = "REJECTED: Missing error handling on line 42."

        # Act
        result = agent._parse_llm_response(text)

        # Assert
        assert result is False

    @pytest.mark.unit
    def test_parse_ambiguous_response_defaults_false(self, mock_client, sample_config):
        """_parse_llm_response() should default to False for ambiguous responses."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        text = "The code seems okay but might need review."

        # Act
        result = agent._parse_llm_response(text)

        # Assert
        assert result is False


class TestCommitDataRetrieval:
    """Tests for getting commit message and diff."""

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
    def test_get_commit_message(self, mock_client, sample_config):
        """_get_commit_message() should retrieve commit message."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="docs: Update API documentation\n\nAdded examples for auth endpoints.",
            )

            # Act
            result = agent._get_commit_message("abc123")

            # Assert
            assert result == "docs: Update API documentation\n\nAdded examples for auth endpoints."
            mock_run.assert_called_once()

    @pytest.mark.unit
    def test_get_commit_message_failure(self, mock_client, sample_config):
        """_get_commit_message() should return empty string on failure."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            # Act
            result = agent._get_commit_message("invalid")

            # Assert
            assert result == ""

    @pytest.mark.unit
    def test_get_commit_diff(self, mock_client, sample_config):
        """_get_commit_diff() should retrieve commit diff."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        expected_diff = """commit abc123
Author: Test <test@example.com>
Date:   Mon Jan 1 00:00:00 2024 +0000

    docs: Update

diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # Project
+Updated"""

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=expected_diff)

            # Act
            result = agent._get_commit_diff("abc123")

            # Assert
            assert "README.md" in result
            assert "Updated" in result

    @pytest.mark.unit
    def test_get_commit_diff_failure(self, mock_client, sample_config):
        """_get_commit_diff() should return empty string on failure."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        with patch("jiro.agents.review.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="")

            # Act
            result = agent._get_commit_diff("invalid")

            # Assert
            assert result == ""


class TestPromptBuilding:
    """Tests for LLM prompt construction."""

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
    def test_build_review_prompt_includes_diff(self, mock_client, sample_config):
        """_build_review_prompt() should include commit diff."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-123",
            title="Add docs",
            task_type="docs",
            status="open",
            created_at=datetime.now(),
            description="Add API documentation",
        )

        with (
            patch.object(agent, "_get_commit_message") as mock_msg,
            patch.object(agent, "_get_commit_diff") as mock_diff,
        ):
            mock_msg.return_value = "docs: Add API examples"
            mock_diff.return_value = "--- a/README.md\n+++ b/README.md\n@@ -1,3 +1,5 @@ Example"

            # Act
            prompt = agent._build_review_prompt("abc123", task)

            # Assert
            assert "task-123" in prompt
            assert "Add docs" in prompt
            assert "Add API examples" in prompt
            assert "README.md" in prompt
            assert "Example" in prompt

    @pytest.mark.unit
    def test_build_review_prompt_includes_task_context(self, mock_client, sample_config):
        """_build_review_prompt() should include full task context."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-456",
            title="Fix bug",
            task_type="bug_fix",
            status="in_progress",
            created_at=datetime.now(),
            description="Fix null pointer in parser",
        )

        with (
            patch.object(agent, "_get_commit_message") as mock_msg,
            patch.object(agent, "_get_commit_diff") as mock_diff,
        ):
            mock_msg.return_value = "fix: null check in parser"
            mock_diff.return_value = "--- a/src/parser.py\n+++ b/src/parser.py"

            # Act
            prompt = agent._build_review_prompt("def456", task)

            # Assert
            assert "task-456" in prompt
            assert "Fix bug" in prompt
            assert "bug_fix" in prompt
            assert "Fix null pointer in parser" in prompt

    @pytest.mark.unit
    def test_build_review_prompt_truncates_large_diff(self, mock_client, sample_config):
        """_build_review_prompt() should truncate very large diffs."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-789",
            title="Large changes",
            task_type="refactor",
            status="open",
            created_at=datetime.now(),
            description="Large refactoring",
        )

        # Create a very large diff
        large_diff = "\n".join([f"+ line {i}" for i in range(600)])

        with (
            patch.object(agent, "_get_commit_message") as mock_msg,
            patch.object(agent, "_get_commit_diff") as mock_diff,
        ):
            mock_msg.return_value = "refactor: large changes"
            mock_diff.return_value = large_diff

            # Act
            prompt = agent._build_review_prompt("ghi789", task)

            # Assert
            assert "truncated" in prompt
            assert "600 lines omitted" in prompt or "lines omitted" in prompt


class TestTDDTypeContext:
    """Tests for TDD-specific commit type validation context."""

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
    def test_get_commit_type_context_tdd_green(self, mock_client, sample_config):
        """_get_commit_type_context() should include green phase validation rules."""
        # Arrange
        from jiro.steps.types import StepType

        agent = ReviewAgent(mock_client, sample_config)

        # Act
        context = agent._get_commit_type_context(StepType.TDD_GREEN)

        # Assert
        assert "TDD Green Phase Validation" in context
        assert "Code Minimalism" in context
        assert "over-engineering" in context
        assert "No Unnecessary Complexity" in context

    @pytest.mark.unit
    def test_get_commit_type_context_tdd_refactor(self, mock_client, sample_config):
        """_get_commit_type_context() should include refactor phase validation rules."""
        # Arrange
        from jiro.steps.types import StepType

        agent = ReviewAgent(mock_client, sample_config)

        # Act
        context = agent._get_commit_type_context(StepType.TDD_REFACTOR)

        # Assert
        assert "TDD Refactor Phase Validation" in context
        assert "Behavior Neutrality" in context
        assert "functional changes" in context
        assert "No Hidden Functional Changes" in context

    @pytest.mark.unit
    def test_get_commit_type_context_non_tdd(self, mock_client, sample_config):
        """_get_commit_type_context() should return empty string for non-TDD commits."""
        # Arrange
        from jiro.steps.types import StepType

        agent = ReviewAgent(mock_client, sample_config)

        # Act
        context = agent._get_commit_type_context(StepType.DOCUMENTATION)

        # Assert
        assert context == ""

    @pytest.mark.unit
    def test_get_commit_type_context_none(self, mock_client, sample_config):
        """_get_commit_type_context() should handle None step type."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)

        # Act
        context = agent._get_commit_type_context(None)

        # Assert
        assert context == ""

    @pytest.mark.unit
    def test_build_review_prompt_includes_tdd_green_context(self, mock_client, sample_config):
        """_build_review_prompt() should include green phase context in prompt."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-green",
            title="Implement feature",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Make failing test pass",
        )

        with (
            patch.object(agent, "_get_commit_message") as mock_msg,
            patch.object(agent, "_get_commit_diff") as mock_diff,
            patch.object(agent, "_extract_step_type_from_commit") as mock_step,
        ):
            from jiro.steps.types import StepType

            mock_msg.return_value = "🟢 Implement user authentication"
            mock_diff.return_value = "--- a/src/auth.py\n+++ b/src/auth.py\n+def authenticate():"
            mock_step.return_value = StepType.TDD_GREEN

            # Act
            prompt = agent._build_review_prompt("abc123", task)

            # Assert
            assert "TDD Green Phase Validation" in prompt
            assert "Code Minimalism" in prompt

    @pytest.mark.unit
    def test_build_review_prompt_includes_tdd_refactor_context(self, mock_client, sample_config):
        """_build_review_prompt() should include refactor phase context in prompt."""
        # Arrange
        agent = ReviewAgent(mock_client, sample_config)
        task = Task(
            id="task-refactor",
            title="Refactor code",
            task_type="refactor",
            status="open",
            created_at=datetime.now(),
            description="Improve code structure",
        )

        with (
            patch.object(agent, "_get_commit_message") as mock_msg,
            patch.object(agent, "_get_commit_diff") as mock_diff,
            patch.object(agent, "_extract_step_type_from_commit") as mock_step,
        ):
            from jiro.steps.types import StepType

            mock_msg.return_value = "♻️ Refactor authentication module"
            mock_diff.return_value = (
                "--- a/src/auth.py\n+++ b/src/auth.py\n-def old_auth():\n+def authenticate():"
            )
            mock_step.return_value = StepType.TDD_REFACTOR

            # Act
            prompt = agent._build_review_prompt("def456", task)

            # Assert
            assert "TDD Refactor Phase Validation" in prompt
            assert "Behavior Neutrality" in prompt
