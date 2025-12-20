"""Tests for PlanningAgent."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from jiro.agents.base import AgentResult
from jiro.agents.planning import PlanningAgent
from jiro.core.execution_plan import ExecutionPlanSchema, ExecutionStep, FileAction
from jiro.trackers.interface import Task


class TestPlanningAgentInitialization:
    """Tests for PlanningAgent initialization."""

    @pytest.mark.unit
    def test_initialization_requires_client(self):
        """PlanningAgent.__init__ should require client."""
        with pytest.raises(TypeError):
            PlanningAgent(None)

    @pytest.mark.unit
    def test_initialization_success(self):
        """PlanningAgent should initialize with client."""
        client = MagicMock()
        agent = PlanningAgent(client)
        assert agent.client == client


class TestPlanningAgent:
    """Tests for the PlanningAgent class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        client.execute = AsyncMock()
        return client

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for planning."""
        return Task(
            id="task-123",
            title="Implement user authentication",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
            description="Add JWT-based authentication to API",
            priority=1,
            labels=["auth", "feature"],
        )

    @pytest.mark.asyncio
    async def test_plan_returns_execution_plan(self, mock_client, sample_task):
        """plan() should return an ExecutionPlanSchema object."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model with password hashing"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass with id, email, password_hash"
    verification_command: "pytest tests/unit/test_user.py"

  - description: "Add authentication middleware"
    step_type: "tdd_green"
    files:
      - path: "src/middleware/auth.py"
        action: "create"
        content_hints: "Create JWTAuth middleware class"
    verification_command: "pytest tests/unit/test_auth.py"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=150,
            tokens_after=450,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert isinstance(result, ExecutionPlanSchema)
        assert result.task_id == "task-123"
        assert isinstance(result.steps, list)
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_plan_includes_files_and_actions(self, mock_client, sample_task):
        """plan() should include specific files and actions in steps."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
      - path: "tests/unit/test_user.py"
        action: "create"
        content_hints: "Add User model tests"
    verification_command: "pytest tests/unit/test_user.py"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=150,
            tokens_after=400,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert len(result.steps) == 1
        step = result.steps[0]
        assert isinstance(step, ExecutionStep)
        assert step.description == "Create User model"
        assert len(step.files) == 2
        assert step.files[0].path == "src/models/user.py"
        assert step.files[0].action == "create"
        assert step.files[1].path == "tests/unit/test_user.py"
        assert step.step_type == "tdd_green"

    @pytest.mark.asyncio
    async def test_plan_includes_verification_command(self, mock_client, sample_task):
        """plan() should include verification command per step."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
    verification_command: "pytest tests/unit/test_user.py -v --cov=src"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=150,
            tokens_after=400,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert result.steps[0].verification_command == "pytest tests/unit/test_user.py -v --cov=src"

    @pytest.mark.asyncio
    async def test_plan_tracks_context_usage(self, mock_client, sample_task):
        """plan() should track token usage in ExecutionPlanSchema."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
    verification_command: "pytest tests/unit/test_user.py"
```"""

        tokens_before = 200
        tokens_after = 650
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert result.estimated_tokens == (tokens_after - tokens_before)

    @pytest.mark.asyncio
    async def test_plan_handles_failure(self, mock_client, sample_task):
        """plan() should raise error when client returns failure."""
        # Arrange
        mock_client.execute.return_value = AgentResult(
            success=False,
            output="",
            tokens_before=100,
            tokens_after=100,
            error="API Error",
        )

        agent = PlanningAgent(mock_client)

        # Act & Assert
        with pytest.raises(ValueError, match="API Error"):
            await agent.plan(sample_task)

    @pytest.mark.asyncio
    async def test_plan_step_has_all_required_fields(self, mock_client, sample_task):
        """ExecutionStep should have all required fields."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model with password hashing"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
    verification_command: "pytest tests/unit/test_user.py"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=150,
            tokens_after=400,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert len(result.steps) >= 1
        step = result.steps[0]
        assert step.description
        assert step.files
        assert step.step_type

    @pytest.mark.asyncio
    async def test_plan_calls_client_with_task_context(self, mock_client, sample_task):
        """plan() should call client.execute with task context."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Test step"
    step_type: "tdd_green"
    files:
      - path: "src/test.py"
        action: "create"
    verification_command: "pytest tests/"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=100,
            tokens_after=300,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        await agent.plan(sample_task)

        # Assert
        assert mock_client.execute.called
        call_args = mock_client.execute.call_args[0][0]
        assert "task-123" in call_args
        assert "Implement user authentication" in call_args

    @pytest.mark.unit
    def test_build_planning_prompt(self, mock_client, sample_task):
        """_build_planning_prompt() should create prompt with task context."""
        # Arrange
        agent = PlanningAgent(mock_client)

        # Act
        prompt = agent._build_planning_prompt(sample_task)

        # Assert
        assert "task-123" in prompt
        assert "Implement user authentication" in prompt
        assert "feature" in prompt
        assert "JWT-based authentication" in prompt
        assert "YAML" in prompt

    @pytest.mark.unit
    def test_extract_files_from_step_with_dict_items(self, mock_client):
        """_extract_files_from_step() should extract FileAction objects from dict items."""
        # Arrange
        agent = PlanningAgent(mock_client)
        step_data = {
            "files": [
                {"path": "src/models/user.py", "action": "create", "content_hints": "User model"},
                {"path": "tests/unit/test_user.py", "action": "create"},
            ]
        }

        # Act
        result = agent._extract_files_from_step(step_data)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], FileAction)
        assert result[0].path == "src/models/user.py"
        assert result[0].action == "create"
        assert result[0].content_hints == "User model"
        assert result[1].path == "tests/unit/test_user.py"

    @pytest.mark.unit
    def test_extract_files_from_step_with_string_items(self, mock_client):
        """_extract_files_from_step() should convert string paths to FileAction."""
        # Arrange
        agent = PlanningAgent(mock_client)
        step_data = {"files": ["src/models/user.py", "tests/unit/test_user.py"]}

        # Act
        result = agent._extract_files_from_step(step_data)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], FileAction)
        assert result[0].path == "src/models/user.py"
        assert result[0].action == "modify"  # Default action for legacy strings
        assert result[1].path == "tests/unit/test_user.py"

    @pytest.mark.unit
    def test_extract_files_from_step_with_mixed_items(self, mock_client):
        """_extract_files_from_step() should handle mixed dict and string items."""
        # Arrange
        agent = PlanningAgent(mock_client)
        step_data = {
            "files": [
                {"path": "src/models/user.py", "action": "create"},
                "tests/unit/test_user.py",
            ]
        }

        # Act
        result = agent._extract_files_from_step(step_data)

        # Assert
        assert len(result) == 2
        assert result[0].path == "src/models/user.py"
        assert result[0].action == "create"
        assert result[1].path == "tests/unit/test_user.py"
        assert result[1].action == "modify"

    @pytest.mark.unit
    def test_extract_files_from_step_with_empty_files(self, mock_client):
        """_extract_files_from_step() should return empty list for empty files."""
        # Arrange
        agent = PlanningAgent(mock_client)
        step_data = {"files": []}

        # Act
        result = agent._extract_files_from_step(step_data)

        # Assert
        assert result == []

    @pytest.mark.unit
    def test_extract_files_from_step_with_no_files_key(self, mock_client):
        """_extract_files_from_step() should handle missing files key."""
        # Arrange
        agent = PlanningAgent(mock_client)
        step_data = {}

        # Act
        result = agent._extract_files_from_step(step_data)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_parse_plan_from_output_with_yaml_block(self, mock_client, sample_task):
        """_parse_plan_from_output() should extract YAML from markdown block."""
        # Arrange
        agent = PlanningAgent(mock_client)
        output = """Here's your plan:

```yaml
task_id: "task-123"

steps:
  - description: "Create file"
    step_type: "tdd_green"
    files:
      - path: "src/test.py"
        action: "create"
    verification_command: "pytest tests/"
```

That's your plan."""

        # Act
        result = agent._parse_plan_from_output(output, "task-123")

        # Assert
        assert isinstance(result, ExecutionPlanSchema)
        assert result.task_id == "task-123"
        assert len(result.steps) == 1
        assert result.steps[0].verification_command == "pytest tests/"

    @pytest.mark.asyncio
    async def test_parse_plan_from_output_without_yaml_block(self, mock_client):
        """_parse_plan_from_output() should handle raw YAML without markdown block."""
        # Arrange
        agent = PlanningAgent(mock_client)
        output = """task_id: "task-456"

steps:
  - description: "Create file"
    step_type: "tdd_green"
    files:
      - path: "src/file.py"
        action: "create"
    verification_command: "pytest"
"""

        # Act
        result = agent._parse_plan_from_output(output, "task-456")

        # Assert
        assert isinstance(result, ExecutionPlanSchema)
        assert result.task_id == "task-456"
        assert len(result.steps) == 1

    @pytest.mark.asyncio
    async def test_parse_plan_from_output_invalid_yaml(self, mock_client):
        """_parse_plan_from_output() should raise error for invalid YAML."""
        # Arrange
        agent = PlanningAgent(mock_client)
        invalid_output = """```yaml
task_id: task-123
  invalid: yaml: formatting
```"""

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse YAML"):
            agent._parse_plan_from_output(invalid_output, "task-123")

    @pytest.mark.asyncio
    async def test_parse_plan_from_output_empty_plan(self, mock_client):
        """_parse_plan_from_output() should raise error for empty plan."""
        # Arrange
        agent = PlanningAgent(mock_client)
        # Empty YAML will parse to None or empty string, triggering the error
        output = """```yaml
```"""

        # Act & Assert
        with pytest.raises(ValueError, match="valid execution plan"):
            agent._parse_plan_from_output(output, "task-123")

    @pytest.mark.asyncio
    async def test_parse_plan_from_output_no_steps(self, mock_client):
        """_parse_plan_from_output() should raise error when plan has no steps."""
        # Arrange
        agent = PlanningAgent(mock_client)
        output = """```yaml
task_id: "task-123"

steps: []
```"""

        # Act & Assert
        with pytest.raises(ValueError, match="any execution steps"):
            agent._parse_plan_from_output(output, "task-123")

    @pytest.mark.asyncio
    async def test_plan_with_multiple_steps(self, mock_client, sample_task):
        """plan() should handle multiple steps."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
    verification_command: "pytest tests/unit/test_user.py"

  - description: "Add auth middleware"
    step_type: "tdd_green"
    files:
      - path: "src/middleware/auth.py"
        action: "create"
        content_hints: "Create middleware"
    verification_command: "pytest tests/unit/test_auth.py"

  - description: "Update API routes"
    step_type: "tdd_green"
    files:
      - path: "src/api/routes.py"
        action: "modify"
        content_hints: "Add auth decorator"
    verification_command: "pytest tests/unit/test_routes.py"
```"""

        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=150,
            tokens_after=500,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert len(result.steps) == 3
        assert result.steps[0].description == "Create User model"
        assert result.steps[1].description == "Add auth middleware"
        assert result.steps[2].description == "Update API routes"

    @pytest.mark.asyncio
    async def test_plan_execution_plan_has_required_fields(self, mock_client, sample_task):
        """ExecutionPlanSchema should have all required fields."""
        # Arrange
        mock_output = """```yaml
task_id: "task-123"

steps:
  - description: "Create User model"
    step_type: "tdd_green"
    files:
      - path: "src/models/user.py"
        action: "create"
        content_hints: "Create User dataclass"
    verification_command: "pytest tests/unit/test_user.py"
```"""

        tokens_before = 150
        tokens_after = 400
        mock_client.execute.return_value = AgentResult(
            success=True,
            output=mock_output,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            error=None,
        )

        agent = PlanningAgent(mock_client)

        # Act
        result = await agent.plan(sample_task)

        # Assert
        assert result.task_id
        assert result.steps
        assert result.estimated_tokens
        assert result.estimated_tokens == (tokens_after - tokens_before)


class TestPlanningPromptDefinitionOfDone:
    """Tests for Definition of Done constraints in planning prompt."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock AgentClient."""
        client = MagicMock()
        return client

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            id="task-123",
            title="Add feature X",
            task_type="feature",
            status="open",
            created_at=datetime.now(),
        )

    @pytest.mark.unit
    def test_prompt_forbids_separate_testing_phase(self, mock_client, sample_task):
        """Prompt should explicitly forbid separate testing phases."""
        agent = PlanningAgent(mock_client)
        prompt = agent._build_planning_prompt(sample_task)

        # The prompt should contain guidance about not creating separate testing phases
        assert "NEVER create separate" in prompt or "never create separate" in prompt.lower()
        assert "testing phase" in prompt.lower()

    @pytest.mark.unit
    def test_prompt_forbids_separate_linting_phase(self, mock_client, sample_task):
        """Prompt should explicitly forbid separate linting phases."""
        agent = PlanningAgent(mock_client)
        prompt = agent._build_planning_prompt(sample_task)

        # The prompt should contain guidance about not creating separate linting phases
        assert "linting phase" in prompt.lower() or "lint phase" in prompt.lower()

    @pytest.mark.unit
    def test_prompt_forbids_separate_documentation_phase(self, mock_client, sample_task):
        """Prompt should explicitly forbid separate documentation phases."""
        agent = PlanningAgent(mock_client)
        prompt = agent._build_planning_prompt(sample_task)

        # The prompt should contain guidance about not creating separate documentation phases
        assert "documentation phase" in prompt.lower()

    @pytest.mark.unit
    def test_prompt_includes_definition_of_done(self, mock_client, sample_task):
        """Prompt should include definition of done concept."""
        agent = PlanningAgent(mock_client)
        prompt = agent._build_planning_prompt(sample_task)

        # The prompt should explain definition of done
        assert "definition of done" in prompt.lower()
