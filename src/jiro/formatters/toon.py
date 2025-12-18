"""TOON (Text-Only Output Notation) formatter for structured text output.

TOON is a lightweight, human-readable text format optimized for AI consumption
and parsing. It uses simple tag-based sections with key-value pairs.

Format example:
    [task]
    id: task-123
    title: Fix bug in parser
    status: open
    [/task]
"""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from jiro.trackers.interface import Task


class ToonFormatter:
    """Formatter for TOON (Text-Only Output Notation) format.

    TOON is designed to be:
    - Human-readable for developers
    - Easy to parse with simple regex or line-by-line processing
    - Optimized for LLM/AI consumption
    - Language-agnostic
    """

    def format_task(self, task: Task) -> str:
        """Format a single task to TOON format.

        Args:
            task: The Task object to format.

        Returns:
            TOON formatted string representation of the task.
        """
        task_dict = self._task_to_dict(task)
        return self._format_section("task", task_dict)

    def format_tasks(self, tasks: list[Task]) -> str:
        """Format multiple tasks to TOON format.

        Args:
            tasks: List of Task objects to format.

        Returns:
            TOON formatted string with all tasks.
        """
        if not tasks:
            return ""

        sections = [self.format_task(task) for task in tasks]
        return "\n".join(sections)

    def format_dict(self, data: dict[str, Any], section_name: str) -> str:
        """Format a dictionary to TOON format.

        Args:
            data: Dictionary to format.
            section_name: Name of the section tag.

        Returns:
            TOON formatted string.
        """
        return self._format_section(section_name, data)

    def format_list(self, items: list[dict[str, Any]], section_name: str) -> str:
        """Format a list of dictionaries to TOON format.

        Args:
            items: List of dictionaries to format.
            section_name: Name of the section tag for each item.

        Returns:
            TOON formatted string with all items.
        """
        sections = [self._format_section(section_name, item) for item in items]
        return "\n".join(sections)

    def _task_to_dict(self, task: Task) -> dict[str, Any]:
        """Convert a Task object to a dictionary.

        Args:
            task: The Task to convert.

        Returns:
            Dictionary representation of the task.
        """
        return {
            "id": task.id,
            "title": task.title,
            "task_type": task.task_type,
            "status": task.status,
            "description": task.description,
            "epic_id": task.epic_id,
            "priority": task.priority,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "closed_at": task.closed_at,
            "labels": task.labels,
        }

    def _format_section(self, section_name: str, data: dict[str, Any]) -> str:
        """Format a dictionary as a TOON section.

        Args:
            section_name: Name for the section tag.
            data: Dictionary to format.

        Returns:
            TOON formatted string.
        """
        lines = [f"[{section_name}]"]

        for key, value in data.items():
            if value is None:
                # Skip None values
                continue
            formatted_value = self._format_value(value)
            lines.append(f"{key}: {formatted_value}")

        lines.append(f"[/{section_name}]")
        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format a value for TOON output.

        Handles various data types including:
        - Strings
        - Numbers
        - Booleans
        - Dates/datetimes
        - Lists
        - Nested structures

        Args:
            value: The value to format.

        Returns:
            String representation suitable for TOON format.
        """
        if isinstance(value, bool):
            # Format booleans as lowercase for consistency
            return str(value).lower()

        if isinstance(value, datetime):
            # Format datetimes in ISO format
            return value.isoformat()

        if isinstance(value, int | float):
            # Keep numbers as-is
            return str(value)

        if isinstance(value, list | tuple):
            # Format lists as comma-separated values
            if not value:
                return ""
            formatted_items = [self._format_value(item) for item in value]
            return ", ".join(formatted_items)

        if is_dataclass(value) and not isinstance(value, type):
            # Convert dataclass to dict and format
            value_dict = asdict(value)
            return str(value_dict)

        # Default: convert to string
        return str(value)

    def parse_toon(self, toon_str: str) -> dict[str, Any]:
        """Parse TOON formatted string back to Python objects.

        Args:
            toon_str: TOON formatted string.

        Returns:
            Dictionary representation of the TOON data.

        Raises:
            ValueError: If the TOON format is invalid.
        """
        sections: dict[str, list[dict[str, Any]]] = {}
        current_section: str | None = None
        current_data: dict[str, Any] = {}
        lines = toon_str.split("\n")

        for line in lines:
            stripped = line.strip()

            # Check for section opening tag
            if (
                stripped.startswith("[")
                and stripped.endswith("]")
                and not stripped.startswith("[/")
            ):
                # Save previous section if exists
                if current_section and current_data:
                    if current_section not in sections:
                        sections[current_section] = []
                    sections[current_section].append(current_data)
                    current_data = {}

                # Start new section
                current_section = stripped[1:-1]

            # Check for section closing tag
            elif stripped.startswith("[/") and stripped.endswith("]"):
                # Save current section
                if current_section and current_data:
                    if current_section not in sections:
                        sections[current_section] = []
                    sections[current_section].append(current_data)
                    current_data = {}
                    current_section = None

            # Parse key-value pair
            elif ":" in stripped and current_section:
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Attempt to parse value as Python literal
                current_data[key] = self._parse_value(value)

        return sections

    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value back to appropriate Python type.

        Args:
            value_str: String representation of the value.

        Returns:
            Parsed Python value.
        """
        # Try parsing as boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Try parsing as number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str
