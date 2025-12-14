"""Tests for step class discovery convention."""

import pytest

from jiro.steps.discovery import get_module_path, to_pascal_case
from jiro.steps.types import StepType


class TestGetModulePath:
    """Tests for get_module_path function."""

    def test_tdd_red(self):
        """tdd_red should map to jiro.steps.tdd.red."""
        assert get_module_path("tdd_red") == "jiro.steps.tdd.red"

    def test_tdd_green(self):
        """tdd_green should map to jiro.steps.tdd.green."""
        assert get_module_path("tdd_green") == "jiro.steps.tdd.green"

    def test_tdd_refactor(self):
        """tdd_refactor should map to jiro.steps.tdd.refactor."""
        assert get_module_path("tdd_refactor") == "jiro.steps.tdd.refactor"

    def test_bug_red(self):
        """bug_red should map to jiro.steps.bug.red."""
        assert get_module_path("bug_red") == "jiro.steps.bug.red"

    def test_bug_green(self):
        """bug_green should map to jiro.steps.bug.green."""
        assert get_module_path("bug_green") == "jiro.steps.bug.green"

    def test_lint_fix(self):
        """lint_fix should map to jiro.steps.lint.fix."""
        assert get_module_path("lint_fix") == "jiro.steps.lint.fix"

    def test_test_only(self):
        """test_only should map to jiro.steps.test.only."""
        assert get_module_path("test_only") == "jiro.steps.test.only"

    def test_documentation(self):
        """documentation should map to jiro.steps.documentation."""
        assert get_module_path("documentation") == "jiro.steps.documentation"

    def test_refactoring(self):
        """refactoring should map to jiro.steps.refactoring."""
        assert get_module_path("refactoring") == "jiro.steps.refactoring"

    def test_config(self):
        """config should map to jiro.steps.config."""
        assert get_module_path("config") == "jiro.steps.config"

    def test_performance(self):
        """performance should map to jiro.steps.performance."""
        assert get_module_path("performance") == "jiro.steps.performance"

    def test_accepts_step_type_enum(self):
        """get_module_path should accept StepType enum."""
        assert get_module_path(StepType.TDD_RED) == "jiro.steps.tdd.red"


class TestToPascalCase:
    """Tests for to_pascal_case function."""

    def test_tdd_red(self):
        """tdd_red should become TddRed."""
        assert to_pascal_case("tdd_red") == "TddRed"

    def test_tdd_green(self):
        """tdd_green should become TddGreen."""
        assert to_pascal_case("tdd_green") == "TddGreen"

    def test_tdd_refactor(self):
        """tdd_refactor should become TddRefactor."""
        assert to_pascal_case("tdd_refactor") == "TddRefactor"

    def test_bug_red(self):
        """bug_red should become BugRed."""
        assert to_pascal_case("bug_red") == "BugRed"

    def test_bug_green(self):
        """bug_green should become BugGreen."""
        assert to_pascal_case("bug_green") == "BugGreen"

    def test_lint_fix(self):
        """lint_fix should become LintFix."""
        assert to_pascal_case("lint_fix") == "LintFix"

    def test_test_only(self):
        """test_only should become TestOnly."""
        assert to_pascal_case("test_only") == "TestOnly"

    def test_documentation(self):
        """documentation should become Documentation."""
        assert to_pascal_case("documentation") == "Documentation"

    def test_refactoring(self):
        """refactoring should become Refactoring."""
        assert to_pascal_case("refactoring") == "Refactoring"

    def test_config(self):
        """config should become Config."""
        assert to_pascal_case("config") == "Config"

    def test_performance(self):
        """performance should become Performance."""
        assert to_pascal_case("performance") == "Performance"

    def test_accepts_step_type_enum(self):
        """to_pascal_case should accept StepType enum."""
        assert to_pascal_case(StepType.TDD_RED) == "TddRed"


class TestClassNameGeneration:
    """Tests for generating class names from step types."""

    @pytest.mark.parametrize(
        "step_type,expected_command",
        [
            ("tdd_red", "TddRedCommand"),
            ("tdd_green", "TddGreenCommand"),
            ("tdd_refactor", "TddRefactorCommand"),
            ("bug_red", "BugRedCommand"),
            ("bug_green", "BugGreenCommand"),
            ("lint_fix", "LintFixCommand"),
            ("test_only", "TestOnlyCommand"),
            ("documentation", "DocumentationCommand"),
            ("refactoring", "RefactoringCommand"),
            ("config", "ConfigCommand"),
            ("performance", "PerformanceCommand"),
        ],
    )
    def test_command_class_names(self, step_type: str, expected_command: str):
        """Command class names should follow PascalCase + Command suffix."""
        assert f"{to_pascal_case(step_type)}Command" == expected_command

    @pytest.mark.parametrize(
        "step_type,expected_verify",
        [
            ("tdd_red", "TddRedVerify"),
            ("tdd_green", "TddGreenVerify"),
            ("documentation", "DocumentationVerify"),
        ],
    )
    def test_verify_class_names(self, step_type: str, expected_verify: str):
        """Verify class names should follow PascalCase + Verify suffix."""
        assert f"{to_pascal_case(step_type)}Verify" == expected_verify

    @pytest.mark.parametrize(
        "step_type,expected_commit",
        [
            ("tdd_red", "TddRedCommit"),
            ("tdd_green", "TddGreenCommit"),
            ("documentation", "DocumentationCommit"),
        ],
    )
    def test_commit_class_names(self, step_type: str, expected_commit: str):
        """Commit class names should follow PascalCase + Commit suffix."""
        assert f"{to_pascal_case(step_type)}Commit" == expected_commit


class TestFileNameGeneration:
    """Tests for generating file names from step types."""

    def test_command_file_name(self):
        """Command file should be {step_type}_command.py."""
        step_type = "tdd_red"
        expected_file = "tdd_red_command.py"
        assert f"{step_type}_command.py" == expected_file

    def test_verify_file_name(self):
        """Verify file should be {step_type}_verify.py."""
        step_type = "tdd_red"
        expected_file = "tdd_red_verify.py"
        assert f"{step_type}_verify.py" == expected_file

    def test_commit_file_name(self):
        """Commit file should be {step_type}_commit.py."""
        step_type = "tdd_red"
        expected_file = "tdd_red_commit.py"
        assert f"{step_type}_commit.py" == expected_file
