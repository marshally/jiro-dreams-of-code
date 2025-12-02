"""Tests for SpecPlanner - spec planning agent for task decomposition."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlite_utils import Database

from jiro.agents.base import AgentConfig, AgentResult
from jiro.agents.client import AgentClient
from jiro.core.planner import Epic, PlanResult, Spec, SpecPlanner, Task
from jiro.db.database import ensure_schema, get_database
from jiro.db.repository import PromptRepository


@pytest.fixture
def db_with_schema(tmp_path: Path) -> Database:
    """Provide a database with schema initialized."""
    db = get_database(tmp_path / "test.db")
    ensure_schema(db)
    return db


@pytest.fixture
def prompt_repository(db_with_schema: Database) -> PromptRepository:
    """Provide a PromptRepository instance."""
    return PromptRepository(db_with_schema)


@pytest.fixture
def agent_config() -> AgentConfig:
    """Provide a sample AgentConfig."""
    return AgentConfig(
        model="claude-opus-4-1",
        system_prompt="You are a spec planning assistant.",
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=10,
    )


@pytest.fixture
def mock_agent_client(agent_config: AgentConfig, prompt_repository: PromptRepository):
    """Provide a mocked AgentClient."""
    return AgentClient(agent_config, prompt_repository)


@pytest.fixture
def sample_spec() -> Spec:
    """Provide a sample spec for testing."""
    return Spec(
        title="Build User Authentication",
        overview="Implement user authentication system with email/password and OAuth2.",
        requirements=[
            "User registration with email validation",
            "User login with JWT tokens",
            "OAuth2 integration with GitHub and Google",
            "Password reset functionality",
        ],
        acceptance_criteria=[
            "Users can register with email",
            "Users can login and receive JWT",
            "OAuth2 providers are integrated",
            "Password reset works end-to-end",
        ],
        out_of_scope=[
            "Social media authentication beyond GitHub/Google",
            "Biometric authentication",
            "MFA implementation",
        ],
        technical_notes="Use sqlite for user storage, JWT for tokens. Consider bcrypt for passwords.",
    )


class TestSpecPlannerInitialization:
    """Tests for SpecPlanner initialization."""

    @pytest.mark.unit
    def test_init_accepts_agent_client(self, mock_agent_client: AgentClient) -> None:
        """Should initialize with an AgentClient."""
        planner = SpecPlanner(mock_agent_client)
        assert planner.client == mock_agent_client

    @pytest.mark.unit
    def test_init_requires_agent_client(self) -> None:
        """Should require an AgentClient."""
        with pytest.raises(TypeError):
            SpecPlanner(None)  # type: ignore


class TestSpecPlannerPlan:
    """Tests for the plan() method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_returns_plan_result(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should return a PlanResult from a Spec."""
        mock_response = """
        {
            "epics": [
                {
                    "id": "epic-1",
                    "name": "Authentication Core",
                    "description": "Implement core authentication infrastructure"
                }
            ],
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Setup JWT library",
                    "description": "Install and configure JWT library",
                    "epic_id": "epic-1",
                    "dependencies": []
                }
            ],
            "dependencies": []
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            result = await planner.plan(sample_spec)

            assert isinstance(result, PlanResult)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_generates_epics(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should generate epics from the spec."""
        mock_response = """
        {
            "epics": [
                {
                    "id": "epic-1",
                    "name": "Authentication Core",
                    "description": "Implement core authentication infrastructure",
                    "tasks": ["task-1", "task-2"]
                },
                {
                    "id": "epic-2",
                    "name": "OAuth2 Integration",
                    "description": "Integrate OAuth2 providers",
                    "tasks": ["task-3", "task-4"]
                }
            ],
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Setup JWT library",
                    "description": "Install and configure JWT library",
                    "epic_id": "epic-1",
                    "dependencies": []
                },
                {
                    "id": "task-2",
                    "title": "Implement login endpoint",
                    "description": "Create POST /login endpoint with credentials validation",
                    "epic_id": "epic-1",
                    "dependencies": ["task-1"]
                },
                {
                    "id": "task-3",
                    "title": "GitHub OAuth setup",
                    "description": "Configure GitHub OAuth2",
                    "epic_id": "epic-2",
                    "dependencies": ["task-1"]
                },
                {
                    "id": "task-4",
                    "title": "Google OAuth setup",
                    "description": "Configure Google OAuth2",
                    "epic_id": "epic-2",
                    "dependencies": ["task-1"]
                }
            ],
            "dependencies": [
                {"from": "task-2", "to": "task-1"},
                {"from": "task-3", "to": "task-1"},
                {"from": "task-4", "to": "task-1"}
            ]
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            result = await planner.plan(sample_spec)

            assert len(result.epics) == 2
            assert result.epics[0].name == "Authentication Core"
            assert result.epics[1].name == "OAuth2 Integration"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_generates_tasks_in_epics(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should generate tasks within each epic."""
        mock_response = """
        {
            "epics": [
                {
                    "id": "epic-1",
                    "name": "Authentication Core",
                    "description": "Implement core authentication infrastructure",
                    "tasks": ["task-1", "task-2"]
                }
            ],
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Setup JWT library",
                    "description": "Install and configure JWT library",
                    "epic_id": "epic-1",
                    "dependencies": []
                },
                {
                    "id": "task-2",
                    "title": "Implement login endpoint",
                    "description": "Create POST /login endpoint",
                    "epic_id": "epic-1",
                    "dependencies": ["task-1"]
                }
            ],
            "dependencies": [
                {"from": "task-2", "to": "task-1"}
            ]
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            result = await planner.plan(sample_spec)

            assert len(result.tasks) == 2
            assert result.tasks[0].title == "Setup JWT library"
            assert result.tasks[1].title == "Implement login endpoint"
            assert result.tasks[0].epic_id == "epic-1"
            assert result.tasks[1].epic_id == "epic-1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_analyzes_task_dependencies(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should analyze and set dependencies between tasks."""
        mock_response = """
        {
            "epics": [
                {
                    "id": "epic-1",
                    "name": "Authentication Core",
                    "description": "Implement core authentication",
                    "tasks": ["task-1", "task-2"]
                }
            ],
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Setup JWT library",
                    "description": "Install and configure JWT",
                    "epic_id": "epic-1",
                    "dependencies": []
                },
                {
                    "id": "task-2",
                    "title": "Implement login endpoint",
                    "description": "Create login endpoint",
                    "epic_id": "epic-1",
                    "dependencies": ["task-1"]
                }
            ],
            "dependencies": [
                {"from": "task-2", "to": "task-1", "reason": "task-2 depends on task-1 being completed"}
            ]
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            result = await planner.plan(sample_spec)

            # task-2 should depend on task-1
            assert "task-1" in result.tasks[1].dependencies
            assert result.tasks[0].dependencies == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_calls_agent_client(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should use AgentClient for LLM-based decomposition."""
        mock_response = """
        {
            "epics": [
                {
                    "id": "epic-1",
                    "name": "Core Auth",
                    "description": "Core auth",
                    "tasks": []
                }
            ],
            "tasks": [],
            "dependencies": []
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            await planner.plan(sample_spec)

            # Verify agent client was called
            assert mock_execute.called
            # Verify a prompt was created
            call_args = mock_execute.call_args
            assert call_args is not None
            prompt = call_args[0][0]
            assert "Build User Authentication" in prompt or "authentication" in prompt.lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_handles_empty_response(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should handle empty LLM response gracefully."""
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output="",
                tokens_before=100,
                tokens_after=120,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            result = await planner.plan(sample_spec)

            # Should return a valid PlanResult even with empty response
            assert isinstance(result, PlanResult)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_plan_parses_spec_correctly(
        self, mock_agent_client: AgentClient, sample_spec: Spec
    ) -> None:
        """Should correctly parse the input spec."""
        mock_response = """
        {
            "epics": [],
            "tasks": [],
            "dependencies": []
        }
        """
        with patch.object(mock_agent_client, "execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = AgentResult(
                success=True,
                output=mock_response,
                tokens_before=100,
                tokens_after=200,
                error=None,
            )

            planner = SpecPlanner(mock_agent_client)
            await planner.plan(sample_spec)

            # Verify the spec was processed
            call_args = mock_execute.call_args
            assert call_args is not None
            prompt = call_args[0][0]
            # Prompt should contain spec information
            assert sample_spec.title in prompt or "authentication" in prompt.lower()


class TestDataClasses:
    """Tests for Epic, Task, and PlanResult dataclasses."""

    @pytest.mark.unit
    def test_epic_creation(self) -> None:
        """Should create an Epic with id, name, description, and tasks."""
        epic = Epic(
            id="epic-1",
            name="Authentication",
            description="Auth implementation",
            tasks=["task-1", "task-2"],
        )
        assert epic.id == "epic-1"
        assert epic.name == "Authentication"
        assert epic.description == "Auth implementation"
        assert len(epic.tasks) == 2

    @pytest.mark.unit
    def test_task_creation(self) -> None:
        """Should create a Task with id, title, description, epic_id, and dependencies."""
        task = Task(
            id="task-1",
            title="Setup JWT",
            description="Configure JWT library",
            epic_id="epic-1",
            dependencies=["task-0"],
        )
        assert task.id == "task-1"
        assert task.title == "Setup JWT"
        assert task.description == "Configure JWT library"
        assert task.epic_id == "epic-1"
        assert "task-0" in task.dependencies

    @pytest.mark.unit
    def test_plan_result_creation(self) -> None:
        """Should create a PlanResult with epics, tasks, and dependencies."""
        epic = Epic("epic-1", "Core", "Core auth", ["task-1"])
        task = Task("task-1", "JWT", "Setup JWT", "epic-1", [])
        result = PlanResult(epics=[epic], tasks=[task], dependencies=[])

        assert len(result.epics) == 1
        assert len(result.tasks) == 1
        assert result.epics[0].name == "Core"
        assert result.tasks[0].title == "JWT"
