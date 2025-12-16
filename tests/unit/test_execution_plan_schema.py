"""Tests for execution plan schema."""

import json

import pytest

from jiro.core.execution_plan import (
    ExecutionPlanSchema,
    ExecutionStep,
    FileAction,
)


class TestFileAction:
    """Tests for FileAction dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """FileAction should require path and action."""
        action = FileAction(path="src/foo.py", action="create")
        assert action.path == "src/foo.py"
        assert action.action == "create"

    @pytest.mark.unit
    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        action = FileAction(path="src/foo.py", action="modify")
        assert action.content_hints is None
        assert action.location is None

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """FileAction should accept all fields."""
        action = FileAction(
            path="src/foo.py",
            action="modify",
            content_hints="Add error handling for edge case",
            location="line 42",
        )
        assert action.content_hints == "Add error handling for edge case"
        assert action.location == "line 42"

    @pytest.mark.unit
    def test_to_dict(self) -> None:
        """to_dict should serialize to dictionary."""
        action = FileAction(
            path="src/foo.py",
            action="modify",
            content_hints="Add validation",
            location="function validate()",
        )
        result = action.to_dict()
        assert result == {
            "path": "src/foo.py",
            "action": "modify",
            "content_hints": "Add validation",
            "location": "function validate()",
        }

    @pytest.mark.unit
    def test_from_dict(self) -> None:
        """from_dict should deserialize from dictionary."""
        data = {
            "path": "src/bar.py",
            "action": "create",
            "content_hints": "New utility module",
            "location": None,
        }
        action = FileAction.from_dict(data)
        assert action.path == "src/bar.py"
        assert action.action == "create"
        assert action.content_hints == "New utility module"
        assert action.location is None

    @pytest.mark.unit
    def test_from_dict_minimal(self) -> None:
        """from_dict should handle minimal data."""
        data = {"path": "src/foo.py", "action": "delete"}
        action = FileAction.from_dict(data)
        assert action.path == "src/foo.py"
        assert action.action == "delete"
        assert action.content_hints is None
        assert action.location is None

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_dict then from_dict should produce equivalent object."""
        original = FileAction(
            path="tests/test_foo.py",
            action="modify",
            content_hints="Add new test case",
            location="class TestFoo",
        )
        restored = FileAction.from_dict(original.to_dict())
        assert restored.path == original.path
        assert restored.action == original.action
        assert restored.content_hints == original.content_hints
        assert restored.location == original.location


class TestExecutionStep:
    """Tests for ExecutionStep dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """ExecutionStep should require description and step_type."""
        step = ExecutionStep(
            description="Add failing test for login validation",
            step_type="tdd_red",
        )
        assert step.description == "Add failing test for login validation"
        assert step.step_type == "tdd_red"

    @pytest.mark.unit
    def test_optional_fields_default(self) -> None:
        """Optional fields should have appropriate defaults."""
        step = ExecutionStep(
            description="Test step",
            step_type="docs",
        )
        assert step.files == []
        assert step.verification_command is None

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """ExecutionStep should accept all fields."""
        step = ExecutionStep(
            description="Implement login validation",
            step_type="tdd_green",
            files=[
                FileAction(path="src/auth.py", action="modify"),
            ],
            verification_command="pytest tests/test_auth.py -k test_login",
        )
        assert len(step.files) == 1
        assert step.verification_command == "pytest tests/test_auth.py -k test_login"

    @pytest.mark.unit
    def test_to_dict(self) -> None:
        """to_dict should serialize to dictionary."""
        step = ExecutionStep(
            description="Add documentation",
            step_type="docs",
            files=[
                FileAction(path="README.md", action="modify", content_hints="Add usage"),
            ],
            verification_command="mdformat README.md --check",
        )
        result = step.to_dict()
        assert result["description"] == "Add documentation"
        assert result["step_type"] == "docs"
        assert len(result["files"]) == 1
        assert result["files"][0]["path"] == "README.md"
        assert result["verification_command"] == "mdformat README.md --check"

    @pytest.mark.unit
    def test_from_dict(self) -> None:
        """from_dict should deserialize from dictionary."""
        data = {
            "description": "Fix linting error",
            "step_type": "lint_fix",
            "files": [{"path": "src/foo.py", "action": "modify"}],
            "verification_command": "ruff check src/foo.py",
        }
        step = ExecutionStep.from_dict(data)
        assert step.description == "Fix linting error"
        assert step.step_type == "lint_fix"
        assert len(step.files) == 1
        assert step.files[0].path == "src/foo.py"
        assert step.verification_command == "ruff check src/foo.py"

    @pytest.mark.unit
    def test_from_dict_minimal(self) -> None:
        """from_dict should handle minimal data."""
        data = {
            "description": "Simple step",
            "step_type": "config",
        }
        step = ExecutionStep.from_dict(data)
        assert step.description == "Simple step"
        assert step.step_type == "config"
        assert step.files == []
        assert step.verification_command is None

    @pytest.mark.unit
    def test_roundtrip(self) -> None:
        """to_dict then from_dict should produce equivalent object."""
        original = ExecutionStep(
            description="Refactor extraction",
            step_type="tdd_refactor",
            files=[
                FileAction(path="src/utils.py", action="create"),
                FileAction(path="src/main.py", action="modify", location="line 50"),
            ],
            verification_command="pytest tests/",
        )
        restored = ExecutionStep.from_dict(original.to_dict())
        assert restored.description == original.description
        assert restored.step_type == original.step_type
        assert len(restored.files) == len(original.files)
        assert restored.verification_command == original.verification_command


class TestExecutionPlanSchema:
    """Tests for ExecutionPlanSchema dataclass."""

    @pytest.mark.unit
    def test_required_fields(self) -> None:
        """ExecutionPlanSchema should require task_id."""
        plan = ExecutionPlanSchema(task_id="TASK-123")
        assert plan.task_id == "TASK-123"

    @pytest.mark.unit
    def test_optional_fields_default(self) -> None:
        """Optional fields should have appropriate defaults."""
        plan = ExecutionPlanSchema(task_id="TASK-123")
        assert plan.steps == []
        assert plan.estimated_tokens is None

    @pytest.mark.unit
    def test_all_fields(self) -> None:
        """ExecutionPlanSchema should accept all fields."""
        plan = ExecutionPlanSchema(
            task_id="TASK-456",
            steps=[
                ExecutionStep(description="Step 1", step_type="tdd_red"),
                ExecutionStep(description="Step 2", step_type="tdd_green"),
            ],
            estimated_tokens=5000,
        )
        assert len(plan.steps) == 2
        assert plan.estimated_tokens == 5000

    @pytest.mark.unit
    def test_to_dict(self) -> None:
        """to_dict should serialize to dictionary."""
        plan = ExecutionPlanSchema(
            task_id="TASK-789",
            steps=[
                ExecutionStep(
                    description="Add test",
                    step_type="tdd_red",
                    files=[FileAction(path="tests/test_x.py", action="create")],
                ),
            ],
            estimated_tokens=3000,
        )
        result = plan.to_dict()
        assert result["task_id"] == "TASK-789"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_type"] == "tdd_red"
        assert result["estimated_tokens"] == 3000

    @pytest.mark.unit
    def test_from_dict(self) -> None:
        """from_dict should deserialize from dictionary."""
        data = {
            "task_id": "TASK-ABC",
            "steps": [
                {"description": "Doc update", "step_type": "docs"},
            ],
            "estimated_tokens": 1500,
        }
        plan = ExecutionPlanSchema.from_dict(data)
        assert plan.task_id == "TASK-ABC"
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == "docs"
        assert plan.estimated_tokens == 1500

    @pytest.mark.unit
    def test_from_dict_minimal(self) -> None:
        """from_dict should handle minimal data."""
        data = {"task_id": "TASK-MIN"}
        plan = ExecutionPlanSchema.from_dict(data)
        assert plan.task_id == "TASK-MIN"
        assert plan.steps == []
        assert plan.estimated_tokens is None

    @pytest.mark.unit
    def test_to_json(self) -> None:
        """to_json should serialize to JSON string."""
        plan = ExecutionPlanSchema(
            task_id="TASK-JSON",
            steps=[ExecutionStep(description="Test", step_type="test_only")],
        )
        json_str = plan.to_json()
        parsed = json.loads(json_str)
        assert parsed["task_id"] == "TASK-JSON"
        assert len(parsed["steps"]) == 1

    @pytest.mark.unit
    def test_from_json(self) -> None:
        """from_json should deserialize from JSON string."""
        json_str = '{"task_id": "TASK-PARSE", "steps": [], "estimated_tokens": 2000}'
        plan = ExecutionPlanSchema.from_json(json_str)
        assert plan.task_id == "TASK-PARSE"
        assert plan.steps == []
        assert plan.estimated_tokens == 2000

    @pytest.mark.unit
    def test_roundtrip_dict(self) -> None:
        """to_dict then from_dict should produce equivalent object."""
        original = ExecutionPlanSchema(
            task_id="TASK-ROUND",
            steps=[
                ExecutionStep(
                    description="Red phase",
                    step_type="tdd_red",
                    files=[FileAction(path="tests/test_feature.py", action="create")],
                    verification_command="pytest tests/test_feature.py",
                ),
                ExecutionStep(
                    description="Green phase",
                    step_type="tdd_green",
                    files=[FileAction(path="src/feature.py", action="create")],
                    verification_command="pytest tests/test_feature.py",
                ),
            ],
            estimated_tokens=8000,
        )
        restored = ExecutionPlanSchema.from_dict(original.to_dict())
        assert restored.task_id == original.task_id
        assert len(restored.steps) == len(original.steps)
        assert restored.estimated_tokens == original.estimated_tokens
        assert restored.steps[0].description == original.steps[0].description
        assert restored.steps[1].step_type == original.steps[1].step_type

    @pytest.mark.unit
    def test_roundtrip_json(self) -> None:
        """to_json then from_json should produce equivalent object."""
        original = ExecutionPlanSchema(
            task_id="TASK-JSON-ROUND",
            steps=[
                ExecutionStep(
                    description="Performance optimization",
                    step_type="performance",
                    files=[
                        FileAction(
                            path="src/slow.py",
                            action="modify",
                            location="function slow_operation()",
                        ),
                    ],
                ),
            ],
            estimated_tokens=4500,
        )
        json_str = original.to_json()
        restored = ExecutionPlanSchema.from_json(json_str)
        assert restored.task_id == original.task_id
        assert len(restored.steps) == 1
        assert restored.steps[0].files[0].location == "function slow_operation()"
        assert restored.estimated_tokens == original.estimated_tokens
