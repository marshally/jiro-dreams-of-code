"""Result from lint fix step."""

from dataclasses import dataclass

from jiro.results.base import Result


@dataclass
class LintFixResult(Result):
    """Result from lint fix step.

    Attributes:
        changed_files: List of files modified (single file only)
        error_code: Lint error code that was fixed (e.g., "E501", "W503")
        filename: File that was fixed
    """

    error_code: str
    filename: str
