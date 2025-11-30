"""Tests for commit message templates."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestDocsCommitTemplate:
    """Tests for docs commit template."""

    @pytest.fixture
    def template_dir(self) -> Path:
        """Get the templates directory path."""
        return (
            Path(__file__).parent.parent.parent / "src" / "jiro" / "assets" / "templates" / "commit"
        )

    @pytest.fixture
    def jinja_env(self, template_dir: Path) -> Environment:
        """Create Jinja2 environment."""
        return Environment(loader=FileSystemLoader(str(template_dir)))

    @pytest.mark.unit
    def test_template_exists(self, template_dir: Path) -> None:
        """docs.txt.j2 template should exist."""
        template_path = template_dir / "docs.txt.j2"
        assert template_path.exists(), f"Template not found at {template_path}"

    @pytest.mark.unit
    def test_template_renders(self, jinja_env: Environment) -> None:
        """Template should render with valid context."""
        template = jinja_env.get_template("docs.txt.j2")
        result = template.render(
            task_id="TASK-123",
            task_type="docs",
            reason="Add API documentation for user endpoints",
            verification_command="mkdocs serve",
            verification_results="Documentation builds successfully",
            time_taken_seconds=120,
            context_tokens_before=5000,
            context_tokens_after=6500,
        )
        assert result is not None
        assert len(result) > 0

    @pytest.mark.unit
    def test_template_has_memo_emoji(self, jinja_env: Environment) -> None:
        """Template should include :memo: emoji prefix."""
        template = jinja_env.get_template("docs.txt.j2")
        result = template.render(
            task_id="TASK-123",
            task_type="docs",
            reason="Add docs",
            verification_command="mkdocs serve",
            verification_results="OK",
            time_taken_seconds=60,
            context_tokens_before=1000,
            context_tokens_after=1200,
        )
        assert "📝" in result or ":memo:" in result

    @pytest.mark.unit
    def test_template_includes_task_reference(self, jinja_env: Environment) -> None:
        """Template should include task ID."""
        template = jinja_env.get_template("docs.txt.j2")
        result = template.render(
            task_id="TASK-456",
            task_type="docs",
            reason="Update README",
            verification_command="cat README.md",
            verification_results="OK",
            time_taken_seconds=30,
            context_tokens_before=800,
            context_tokens_after=900,
        )
        assert "TASK-456" in result

    @pytest.mark.unit
    def test_template_includes_verification(self, jinja_env: Environment) -> None:
        """Template should include verification command and results."""
        template = jinja_env.get_template("docs.txt.j2")
        result = template.render(
            task_id="TASK-789",
            task_type="docs",
            reason="Add changelog entry",
            verification_command="markdownlint CHANGELOG.md",
            verification_results="No errors found",
            time_taken_seconds=45,
            context_tokens_before=2000,
            context_tokens_after=2100,
        )
        assert "markdownlint CHANGELOG.md" in result
        assert "No errors found" in result

    @pytest.mark.unit
    def test_template_includes_metrics(self, jinja_env: Environment) -> None:
        """Template should include time and token metrics."""
        template = jinja_env.get_template("docs.txt.j2")
        result = template.render(
            task_id="TASK-001",
            task_type="docs",
            reason="Add architecture docs",
            verification_command="mkdocs build",
            verification_results="Built successfully",
            time_taken_seconds=180,
            context_tokens_before=3000,
            context_tokens_after=4500,
        )
        # Should include time in some format
        assert "180" in result or "3m" in result or "3 min" in result
        # Should include token info
        assert "3000" in result or "4500" in result or "1500" in result
