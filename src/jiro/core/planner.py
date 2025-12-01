"""Spec parser for feature specifications."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Spec:
    """A parsed feature specification."""

    title: str
    overview: str
    requirements: list[str]
    acceptance_criteria: list[str]
    out_of_scope: list[str]
    technical_notes: str | None = None


def parse_spec(path: Path) -> Spec:
    """
    Parse a feature specification markdown file.

    Args:
        path: Path to the specification markdown file.

    Returns:
        Spec dataclass with parsed sections.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If required sections are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    content = path.read_text()

    # Extract title from # Feature: Title
    title = _extract_title(content)
    if not title:
        raise ValueError("Title (# Feature: ...) section is required")

    # Extract sections
    overview = _extract_section(content, "Overview")
    if not overview:
        raise ValueError("Overview section is required")

    requirements = _extract_list_section(content, "Requirements")
    if not requirements:
        raise ValueError("Requirements section is required")

    acceptance_criteria = _extract_list_section(content, "Acceptance Criteria")
    if not acceptance_criteria:
        raise ValueError("Acceptance Criteria section is required")

    out_of_scope = _extract_list_section(content, "Out of Scope")
    if not out_of_scope:
        raise ValueError("Out of Scope section is required")

    technical_notes = _extract_section(content, "Technical Notes")

    return Spec(
        title=title,
        overview=overview,
        requirements=requirements,
        acceptance_criteria=acceptance_criteria,
        out_of_scope=out_of_scope,
        technical_notes=technical_notes,
    )


def _extract_title(content: str) -> str | None:
    """Extract title from # Feature: Title format."""
    match = re.search(r"^#\s+Feature:\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _extract_section(content: str, section_name: str) -> str | None:
    """Extract text content of a section by heading."""
    # Match ## Section Name and capture everything until next ## or EOF
    pattern = rf"^##\s+{re.escape(section_name)}$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        text = match.group(1).strip()
        # Remove list markers if they exist
        lines = text.split("\n")
        # Filter out list items and join remaining paragraphs
        non_list_lines = []
        for line in lines:
            if not line.strip().startswith("-") and not line.strip().startswith("["):
                non_list_lines.append(line)
        result = "\n".join(non_list_lines).strip()
        return result if result else None
    return None


def _extract_list_section(content: str, section_name: str) -> list[str]:
    """Extract list items from a section."""
    # Match ## Section Name and capture everything until next ## or EOF
    pattern = rf"^##\s+{re.escape(section_name)}$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return []

    section_text = match.group(1)
    items = []

    # Split by lines and look for list items starting with - or [ ]
    lines = section_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-"):
            # Remove leading dash and whitespace
            item = stripped[1:].strip()
            items.append(item)

    return items
