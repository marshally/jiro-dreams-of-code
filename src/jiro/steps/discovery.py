"""Discovery convention for step classes.

This module provides functions to discover and instantiate step-specific
classes (Command, Verification, Commit) based on the step type.

The discovery convention maps step type identifiers to module paths and class names:
- Underscores in step_type become dots in module path (directory separators)
- Class names are PascalCase(step_type) + suffix (Command, Verify, Commit)

Example mappings:
    tdd_red     → jiro.steps.tdd.red     → TddRedCommand
    lint_fix    → jiro.steps.lint.fix    → LintFixCommand
    documentation → jiro.steps.documentation → DocumentationCommand
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, cast

from jiro.steps.types import StepType

if TYPE_CHECKING:
    from jiro.commands.base import Command
    from jiro.commits.base import Commit
    from jiro.verifications.base import Verification


def get_module_path(step_type: str | StepType) -> str:
    """Convert step type to module path.

    Underscore always becomes dot (directory separator).

    Args:
        step_type: The step type identifier (e.g., "tdd_red", StepType.TDD_RED)

    Returns:
        Module path (e.g., "jiro.steps.tdd.red")

    Examples:
        >>> get_module_path("tdd_red")
        'jiro.steps.tdd.red'
        >>> get_module_path("lint_fix")
        'jiro.steps.lint.fix'
        >>> get_module_path("documentation")
        'jiro.steps.documentation'
    """
    step_value = str(step_type)
    return f"jiro.steps.{step_value.replace('_', '.')}"


def to_pascal_case(step_type: str | StepType) -> str:
    """Convert step_type to PascalCase.

    Args:
        step_type: The step type identifier (e.g., "tdd_red", StepType.TDD_RED)

    Returns:
        PascalCase version (e.g., "TddRed")

    Examples:
        >>> to_pascal_case("tdd_red")
        'TddRed'
        >>> to_pascal_case("lint_fix")
        'LintFix'
        >>> to_pascal_case("documentation")
        'Documentation'
    """
    step_value = str(step_type)
    return "".join(word.capitalize() for word in step_value.split("_"))


def discover_command(step_type: StepType) -> Command:
    """Discover and instantiate Command class for step type.

    Args:
        step_type: The step type to discover command for

    Returns:
        An instance of the appropriate Command subclass

    Raises:
        ModuleNotFoundError: If the module doesn't exist
        AttributeError: If the class doesn't exist in the module
    """
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Command"

    module = importlib.import_module(f"{module_path}.{step_type.value}_command")
    command_cls = getattr(module, class_name)
    return cast("Command", command_cls())


def discover_verification(step_type: StepType) -> Verification:
    """Discover and instantiate Verification class for step type.

    Args:
        step_type: The step type to discover verification for

    Returns:
        An instance of the appropriate Verification subclass

    Raises:
        ModuleNotFoundError: If the module doesn't exist
        AttributeError: If the class doesn't exist in the module
    """
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Verify"

    module = importlib.import_module(f"{module_path}.{step_type.value}_verify")
    verify_cls = getattr(module, class_name)
    return cast("Verification", verify_cls())


def discover_commit(step_type: StepType) -> Commit:
    """Discover and instantiate Commit class for step type.

    Args:
        step_type: The step type to discover commit for

    Returns:
        An instance of the appropriate Commit subclass

    Raises:
        ModuleNotFoundError: If the module doesn't exist
        AttributeError: If the class doesn't exist in the module
    """
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Commit"

    module = importlib.import_module(f"{module_path}.{step_type.value}_commit")
    commit_cls = getattr(module, class_name)
    return cast("Commit", commit_cls())
