"""Base Result dataclass with serialization methods.

This module provides the foundational Result dataclass that all step-specific
results inherit from. It includes multiple serialization formats for different
use cases:
- as_dict(): For programmatic access
- as_json(): For storage and API responses
- as_toon(): For LLM token efficiency
- as_html(): For web UI rendering
- __str__(): For human-readable output
"""

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


@dataclass
class Result:
    """Base result dataclass with serialization methods.

    All step-specific result classes should inherit from this base class.
    Subclasses can add additional fields specific to their step type.

    Attributes:
        changed_files: List of files modified by this step
    """

    changed_files: list[Path]

    def as_dict(self) -> dict[str, Any]:
        """Convert result to dictionary with Path objects as strings.

        Returns:
            Dictionary representation with all Path objects converted to strings.
        """
        result: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, list):
                # Handle list of Paths
                result[field.name] = [
                    str(item) if isinstance(item, Path) else item for item in value
                ]
            elif isinstance(value, Path):
                result[field.name] = str(value)
            else:
                result[field.name] = value
        return result

    def as_json(self) -> str:
        """Convert result to JSON string.

        Returns:
            JSON string representation of the result.
        """
        return json.dumps(self.as_dict(), default=str)

    def as_toon(self) -> str:
        """Convert result to TOON format for LLM token efficiency.

        TOON (Token-Optimized Object Notation) is a compact format
        designed to minimize tokens while remaining parseable.

        Returns:
            TOON formatted string.
        """
        lines = []
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, list):
                if value:
                    items = [str(item) if isinstance(item, Path) else str(item) for item in value]
                    lines.append(f"{field.name}=[{','.join(items)}]")
                else:
                    lines.append(f"{field.name}=[]")
            elif isinstance(value, Path):
                lines.append(f"{field.name}={value}")
            else:
                lines.append(f"{field.name}={value}")
        return ";".join(lines)

    def as_html(self) -> str:
        """Convert result to HTML for web UI rendering.

        Returns:
            HTML formatted string.
        """
        lines = ["<div class='result'>"]
        for field in fields(self):
            value = getattr(self, field.name)
            lines.append("  <div class='field'>")
            lines.append(f"    <span class='label'>{field.name}:</span>")
            if isinstance(value, list):
                if value:
                    lines.append("    <ul>")
                    for item in value:
                        item_str = str(item) if isinstance(item, Path) else str(item)
                        lines.append(f"      <li>{item_str}</li>")
                    lines.append("    </ul>")
                else:
                    lines.append("    <span class='value'>(none)</span>")
            else:
                val_str = str(value) if isinstance(value, Path) else str(value)
                lines.append(f"    <span class='value'>{val_str}</span>")
            lines.append("  </div>")
        lines.append("</div>")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            Plain text representation of the result.
        """
        lines = ["Result:"]
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, list):
                if value:
                    items = [str(item) if isinstance(item, Path) else str(item) for item in value]
                    lines.append(f"  {field.name}:")
                    for item in items:
                        lines.append(f"    - {item}")
                else:
                    lines.append(f"  {field.name}: (none)")
            else:
                val_str = str(value) if isinstance(value, Path) else str(value)
                lines.append(f"  {field.name}: {val_str}")
        return "\n".join(lines)
