"""Tests for spec parser."""

from pathlib import Path

import pytest

from jiro.core.planner import Spec, parse_spec


class TestSpecDataclass:
    """Tests for Spec dataclass."""

    @pytest.mark.unit
    def test_spec_creation(self) -> None:
        """Spec should be creatable with required fields."""
        spec = Spec(
            title="Test Feature",
            overview="This is a test feature.",
            requirements=["Req 1", "Req 2"],
            acceptance_criteria=["[ ] Criterion 1", "[ ] Criterion 2"],
            out_of_scope=["Item 1"],
        )
        assert spec.title == "Test Feature"
        assert spec.overview == "This is a test feature."
        assert len(spec.requirements) == 2
        assert len(spec.acceptance_criteria) == 2
        assert len(spec.out_of_scope) == 1
        assert spec.technical_notes is None

    @pytest.mark.unit
    def test_spec_with_technical_notes(self) -> None:
        """Spec should support optional technical_notes."""
        spec = Spec(
            title="Test",
            overview="Overview",
            requirements=["Req 1"],
            acceptance_criteria=["[ ] Crit 1"],
            out_of_scope=["Out 1"],
            technical_notes="Some technical details",
        )
        assert spec.technical_notes == "Some technical details"


class TestParseSpecBasic:
    """Tests for basic spec parsing."""

    @pytest.fixture
    def simple_spec(self, tmp_path: Path) -> Path:
        """Create a simple valid spec file."""
        spec_content = """# Feature: User Authentication

## Overview

Implement JWT-based authentication to secure API endpoints.

## Requirements

- Users can register with email and password
- Users can login and receive a JWT token
- Protected endpoints validate JWT tokens

## Acceptance Criteria

- [ ] Registration endpoint returns 201 on success
- [ ] Login endpoint returns JWT token on valid credentials
- [ ] Protected endpoints return 401 without valid token

## Out of Scope

- Social login (OAuth)
- Multi-factor authentication
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)
        return spec_file

    @pytest.mark.unit
    def test_parse_spec_returns_spec_instance(self, simple_spec: Path) -> None:
        """parse_spec should return a Spec instance."""
        result = parse_spec(simple_spec)
        assert isinstance(result, Spec)

    @pytest.mark.unit
    def test_parse_spec_extracts_title(self, simple_spec: Path) -> None:
        """parse_spec should extract title from # Feature: title."""
        result = parse_spec(simple_spec)
        assert result.title == "User Authentication"

    @pytest.mark.unit
    def test_parse_spec_extracts_overview(self, simple_spec: Path) -> None:
        """parse_spec should extract overview section."""
        result = parse_spec(simple_spec)
        assert "JWT-based authentication" in result.overview
        assert "secure API endpoints" in result.overview

    @pytest.mark.unit
    def test_parse_spec_extracts_requirements(self, simple_spec: Path) -> None:
        """parse_spec should extract requirements as list."""
        result = parse_spec(simple_spec)
        assert len(result.requirements) == 3
        assert "Users can register with email and password" in result.requirements
        assert "Users can login and receive a JWT token" in result.requirements
        assert "Protected endpoints validate JWT tokens" in result.requirements

    @pytest.mark.unit
    def test_parse_spec_extracts_acceptance_criteria(self, simple_spec: Path) -> None:
        """parse_spec should extract acceptance criteria as list."""
        result = parse_spec(simple_spec)
        assert len(result.acceptance_criteria) == 3
        assert any("Registration endpoint" in c for c in result.acceptance_criteria)
        assert any("Login endpoint" in c for c in result.acceptance_criteria)
        assert any("Protected endpoints return 401" in c for c in result.acceptance_criteria)

    @pytest.mark.unit
    def test_parse_spec_extracts_out_of_scope(self, simple_spec: Path) -> None:
        """parse_spec should extract out of scope items."""
        result = parse_spec(simple_spec)
        assert len(result.out_of_scope) == 2
        assert "Social login (OAuth)" in result.out_of_scope
        assert "Multi-factor authentication" in result.out_of_scope

    @pytest.mark.unit
    def test_parse_spec_optional_technical_notes(self, simple_spec: Path) -> None:
        """parse_spec should set technical_notes to None if section missing."""
        result = parse_spec(simple_spec)
        assert result.technical_notes is None


class TestParseSpecWithTechnicalNotes:
    """Tests for spec parsing with technical notes."""

    @pytest.fixture
    def spec_with_notes(self, tmp_path: Path) -> Path:
        """Create a spec with technical notes."""
        spec_content = """# Feature: User Authentication

## Overview

Implement JWT-based authentication to secure API endpoints.

## Requirements

- Users can register with email and password
- Users can login and receive a JWT token
- Protected endpoints validate JWT tokens

## Acceptance Criteria

- [ ] Registration endpoint returns 201 on success
- [ ] Login endpoint returns JWT token on valid credentials
- [ ] Protected endpoints return 401 without valid token

## Out of Scope

- Social login (OAuth)

## Technical Notes

Use bcrypt for password hashing with cost factor 12. JWT should use RS256 algorithm with rotating keys.
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)
        return spec_file

    @pytest.mark.unit
    def test_parse_spec_extracts_technical_notes(self, spec_with_notes: Path) -> None:
        """parse_spec should extract technical notes section."""
        result = parse_spec(spec_with_notes)
        assert result.technical_notes is not None
        assert "bcrypt" in result.technical_notes
        assert "RS256" in result.technical_notes


class TestParseSpecValidation:
    """Tests for spec validation."""

    @pytest.mark.unit
    def test_parse_spec_missing_title(self, tmp_path: Path) -> None:
        """parse_spec should raise ValidationError if title missing."""
        spec_content = """## Overview

Some overview.

## Requirements

- Req 1

## Acceptance Criteria

- [ ] Crit 1

## Out of Scope

- Item 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Title"):
            parse_spec(spec_file)

    @pytest.mark.unit
    def test_parse_spec_missing_overview(self, tmp_path: Path) -> None:
        """parse_spec should raise ValidationError if overview missing."""
        spec_content = """# Feature: Test

## Requirements

- Req 1

## Acceptance Criteria

- [ ] Crit 1

## Out of Scope

- Item 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Overview"):
            parse_spec(spec_file)

    @pytest.mark.unit
    def test_parse_spec_missing_requirements(self, tmp_path: Path) -> None:
        """parse_spec should raise ValidationError if requirements missing."""
        spec_content = """# Feature: Test

## Overview

Some overview.

## Acceptance Criteria

- [ ] Crit 1

## Out of Scope

- Item 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Requirements"):
            parse_spec(spec_file)

    @pytest.mark.unit
    def test_parse_spec_missing_acceptance_criteria(self, tmp_path: Path) -> None:
        """parse_spec should raise ValidationError if acceptance criteria missing."""
        spec_content = """# Feature: Test

## Overview

Some overview.

## Requirements

- Req 1

## Out of Scope

- Item 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Acceptance Criteria"):
            parse_spec(spec_file)

    @pytest.mark.unit
    def test_parse_spec_missing_out_of_scope(self, tmp_path: Path) -> None:
        """parse_spec should raise ValidationError if out of scope missing."""
        spec_content = """# Feature: Test

## Overview

Some overview.

## Requirements

- Req 1

## Acceptance Criteria

- [ ] Crit 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Out of Scope"):
            parse_spec(spec_file)

    @pytest.mark.unit
    def test_parse_spec_file_not_found(self) -> None:
        """parse_spec should raise FileNotFoundError if file doesn't exist."""
        nonexistent = Path("/nonexistent/spec.md")
        with pytest.raises(FileNotFoundError):
            parse_spec(nonexistent)


class TestParseSpecEdgeCases:
    """Tests for edge cases in spec parsing."""

    @pytest.mark.unit
    def test_parse_spec_with_extra_whitespace(self, tmp_path: Path) -> None:
        """parse_spec should handle extra whitespace in sections."""
        spec_content = """# Feature: Test Feature

## Overview

This is an overview with extra whitespace.

Some more details here.

## Requirements

- First requirement
- Second requirement
- Third requirement

## Acceptance Criteria

- [ ] First criterion
- [ ] Second criterion
- [ ] Third criterion

## Out of Scope

- First out of scope
- Second out of scope
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)
        result = parse_spec(spec_file)

        assert result.title == "Test Feature"
        assert "This is an overview" in result.overview
        assert len(result.requirements) == 3
        assert len(result.acceptance_criteria) == 3
        assert len(result.out_of_scope) == 2

    @pytest.mark.unit
    def test_parse_spec_with_multiline_list_items(self, tmp_path: Path) -> None:
        """parse_spec should handle multiline list items in requirements."""
        spec_content = """# Feature: Complex Feature

## Overview

Complex feature overview.

## Requirements

- First requirement that spans multiple lines
- Second requirement
- Third requirement

## Acceptance Criteria

- [ ] First criterion
- [ ] Second criterion
- [ ] Third criterion

## Out of Scope

- Item 1
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)
        result = parse_spec(spec_file)

        assert len(result.requirements) == 3
        assert "First requirement that spans multiple lines" in result.requirements[0]

    @pytest.mark.unit
    def test_parse_spec_preserves_list_formatting(self, tmp_path: Path) -> None:
        """parse_spec should preserve list item text without leading dash."""
        spec_content = """# Feature: Test

## Overview

Overview text.

## Requirements

- Requirement with dashes in text - like this
- Another requirement

## Acceptance Criteria

- [ ] Criterion 1 - with dashes
- [ ] Criterion 2

## Out of Scope

- Out of scope item - with dashes
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)
        result = parse_spec(spec_file)

        assert any("with dashes in text" in r for r in result.requirements)
        assert len(result.requirements) == 2
