"""Tests for agent prompts."""

from pathlib import Path

import pytest


class TestPlanningAgentPrompt:
    """Tests for planning agent prompt."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get the prompts directory path."""
        return Path(__file__).parent.parent.parent / "src" / "jiro" / "assets" / "prompts"

    @pytest.mark.unit
    def test_prompt_exists(self, prompts_dir: Path) -> None:
        """planning_agent.md should exist."""
        prompt_path = prompts_dir / "planning_agent.md"
        assert prompt_path.exists(), f"Prompt not found at {prompt_path}"

    @pytest.mark.unit
    def test_prompt_is_not_empty(self, prompts_dir: Path) -> None:
        """planning_agent.md should have content."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text()
        assert len(content) > 100, "Prompt content too short"

    @pytest.mark.unit
    def test_prompt_has_yaml_output_format(self, prompts_dir: Path) -> None:
        """Prompt should specify YAML output format."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text().lower()
        assert "yaml" in content, "Prompt should mention YAML output format"

    @pytest.mark.unit
    def test_prompt_mentions_task_analysis(self, prompts_dir: Path) -> None:
        """Prompt should mention analyzing task."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text().lower()
        assert "task" in content and ("analyz" in content or "understand" in content)

    @pytest.mark.unit
    def test_prompt_mentions_codebase(self, prompts_dir: Path) -> None:
        """Prompt should mention codebase context."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text().lower()
        assert "codebase" in content or "code" in content

    @pytest.mark.unit
    def test_prompt_mentions_files(self, prompts_dir: Path) -> None:
        """Prompt should mention identifying files."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text().lower()
        assert "file" in content

    @pytest.mark.unit
    def test_prompt_mentions_verification(self, prompts_dir: Path) -> None:
        """Prompt should mention verification."""
        prompt_path = prompts_dir / "planning_agent.md"
        content = prompt_path.read_text().lower()
        assert "verif" in content or "test" in content
