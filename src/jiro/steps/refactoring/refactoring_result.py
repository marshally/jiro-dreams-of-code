"""Result from refactoring step."""

from dataclasses import dataclass

from jiro.results.base import Result


@dataclass
class RefactoringResult(Result):
    """Result from refactoring step.

    Attributes:
        changed_files: List of files modified (implementation files only)
        test_specifier: Full pytest specifier (e.g., "tests/test_auth.py::test_login")
        test_output: Output from running the test (showing it passes)
        refactoring_type: Type of refactoring applied (e.g., "rename", "extract_method")
        checksum: Checksum from refactoring MCP proving behavior preservation
    """

    test_specifier: str
    test_output: str
    refactoring_type: str
    checksum: str
