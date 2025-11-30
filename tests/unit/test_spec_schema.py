"""Tests for spec schema template."""

from pathlib import Path

import pytest


class TestSpecSchemaTemplate:
    """Tests for spec schema template."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get the templates directory path."""
        return Path(__file__).parent.parent.parent / "src" / "jiro" / "assets" / "templates"

    @pytest.mark.unit
    def test_template_exists(self, templates_dir: Path) -> None:
        """spec_schema.md should exist."""
        template_path = templates_dir / "spec_schema.md"
        assert template_path.exists(), f"Template not found at {template_path}"

    @pytest.mark.unit
    def test_template_has_content(self, templates_dir: Path) -> None:
        """spec_schema.md should have content."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text()
        assert len(content) > 100, "Template content too short"

    @pytest.mark.unit
    def test_template_has_overview_section(self, templates_dir: Path) -> None:
        """Template should have overview section."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text().lower()
        assert "overview" in content

    @pytest.mark.unit
    def test_template_has_requirements_section(self, templates_dir: Path) -> None:
        """Template should have requirements section."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text().lower()
        assert "requirement" in content

    @pytest.mark.unit
    def test_template_has_acceptance_criteria(self, templates_dir: Path) -> None:
        """Template should have acceptance criteria section."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text().lower()
        assert "acceptance" in content and "criteria" in content

    @pytest.mark.unit
    def test_template_has_out_of_scope(self, templates_dir: Path) -> None:
        """Template should have out of scope section."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text().lower()
        assert "scope" in content

    @pytest.mark.unit
    def test_template_has_technical_notes(self, templates_dir: Path) -> None:
        """Template should have technical notes section."""
        template_path = templates_dir / "spec_schema.md"
        content = template_path.read_text().lower()
        assert "technical" in content
