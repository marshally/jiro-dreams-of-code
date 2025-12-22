"""Tests for project infrastructure detection and bootstrap task generation."""

from pathlib import Path

import pytest

from jiro.core.infrastructure import (
    BootstrapTaskGenerator,
    DetectedLanguage,
    InfrastructureAnalysis,
    ProjectInspector,
)


class TestProjectInspectorLanguageDetection:
    """Tests for detecting programming languages."""

    @pytest.mark.unit
    def test_detects_python_with_pyproject(self, tmp_path: Path) -> None:
        """Should detect Python projects with pyproject.toml."""
        (tmp_path / "pyproject.toml").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(lang.name == "Python" for lang in analysis.languages)

    @pytest.mark.unit
    def test_detects_python_with_requirements(self, tmp_path: Path) -> None:
        """Should detect Python projects with requirements.txt."""
        (tmp_path / "requirements.txt").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(lang.name == "Python" for lang in analysis.languages)

    @pytest.mark.unit
    def test_detects_javascript_with_package_json(self, tmp_path: Path) -> None:
        """Should detect JavaScript projects with package.json."""
        (tmp_path / "package.json").write_text('{"name":"test"}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(lang.name == "JavaScript/TypeScript" for lang in analysis.languages)

    @pytest.mark.unit
    def test_detects_go(self, tmp_path: Path) -> None:
        """Should detect Go projects with go.mod."""
        (tmp_path / "go.mod").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(lang.name == "Go" for lang in analysis.languages)

    @pytest.mark.unit
    def test_detects_rust(self, tmp_path: Path) -> None:
        """Should detect Rust projects with Cargo.toml."""
        (tmp_path / "Cargo.toml").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(lang.name == "Rust" for lang in analysis.languages)

    @pytest.mark.unit
    def test_detects_no_languages(self, tmp_path: Path) -> None:
        """Should return empty list for projects with no detected languages."""
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert analysis.languages == []


class TestProjectInspectorPackageManagers:
    """Tests for detecting package managers."""

    @pytest.mark.unit
    def test_detects_poetry(self, tmp_path: Path) -> None:
        """Should detect poetry as Python package manager."""
        (tmp_path / "poetry.lock").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "Python" and lang.package_manager == "poetry"
            for lang in analysis.languages
        )

    @pytest.mark.unit
    def test_detects_pipenv(self, tmp_path: Path) -> None:
        """Should detect pipenv as Python package manager."""
        (tmp_path / "Pipfile").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "Python" and lang.package_manager == "pipenv"
            for lang in analysis.languages
        )

    @pytest.mark.unit
    def test_detects_uv(self, tmp_path: Path) -> None:
        """Should detect uv as Python package manager."""
        (tmp_path / "uv.lock").touch()
        (tmp_path / "pyproject.toml").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "Python" and lang.package_manager == "uv" for lang in analysis.languages
        )

    @pytest.mark.unit
    def test_detects_npm(self, tmp_path: Path) -> None:
        """Should detect npm as JavaScript package manager."""
        (tmp_path / "package-lock.json").touch()
        (tmp_path / "package.json").write_text('{"name":"test"}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "JavaScript/TypeScript" and lang.package_manager == "npm"
            for lang in analysis.languages
        )

    @pytest.mark.unit
    def test_detects_yarn(self, tmp_path: Path) -> None:
        """Should detect yarn as JavaScript package manager."""
        (tmp_path / "yarn.lock").touch()
        (tmp_path / "package.json").write_text('{"name":"test"}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "JavaScript/TypeScript" and lang.package_manager == "yarn"
            for lang in analysis.languages
        )

    @pytest.mark.unit
    def test_detects_pnpm(self, tmp_path: Path) -> None:
        """Should detect pnpm as JavaScript package manager."""
        (tmp_path / "pnpm-lock.yaml").touch()
        (tmp_path / "package.json").write_text('{"name":"test"}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(
            lang.name == "JavaScript/TypeScript" and lang.package_manager == "pnpm"
            for lang in analysis.languages
        )


class TestProjectInspectorFrameworkDetection:
    """Tests for detecting frameworks."""

    @pytest.mark.unit
    def test_detects_fastapi(self, tmp_path: Path) -> None:
        """Should detect FastAPI in Python projects."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("fastapi>=0.100.0\nuvicorn\n")
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(fw.name == "FastAPI" for fw in analysis.frameworks)

    @pytest.mark.unit
    def test_detects_django(self, tmp_path: Path) -> None:
        """Should detect Django in Python projects."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("django>=4.0\n")
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(fw.name == "Django" for fw in analysis.frameworks)

    @pytest.mark.unit
    def test_detects_react(self, tmp_path: Path) -> None:
        """Should detect React in JavaScript projects."""
        (tmp_path / "package.json").write_text('{"name":"test","dependencies":{"react":"^18.0.0"}}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(fw.name == "React" for fw in analysis.frameworks)

    @pytest.mark.unit
    def test_detects_nextjs(self, tmp_path: Path) -> None:
        """Should detect Next.js in JavaScript projects."""
        (tmp_path / "package.json").write_text('{"name":"test","dependencies":{"next":"^13.0.0"}}')
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(fw.name == "Next.js" for fw in analysis.frameworks)

    @pytest.mark.unit
    def test_detects_express(self, tmp_path: Path) -> None:
        """Should detect Express in JavaScript projects."""
        (tmp_path / "package.json").write_text(
            '{"name":"test","dependencies":{"express":"^4.18.0"}}'
        )
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(fw.name == "Express" for fw in analysis.frameworks)


class TestProjectInspectorToolDetection:
    """Tests for detecting tools and infrastructure."""

    @pytest.mark.unit
    def test_detects_pytest(self, tmp_path: Path) -> None:
        """Should detect pytest configuration."""
        (tmp_path / "pytest.ini").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "pytest" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_jest(self, tmp_path: Path) -> None:
        """Should detect Jest configuration."""
        (tmp_path / "package.json").write_text(
            '{"name":"test","devDependencies":{"jest":"^29.0.0"}}'
        )
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "jest" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_ruff(self, tmp_path: Path) -> None:
        """Should detect ruff linting configuration."""
        (tmp_path / "ruff.toml").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "ruff" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_eslint(self, tmp_path: Path) -> None:
        """Should detect ESLint configuration."""
        (tmp_path / ".eslintrc.json").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "eslint" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_precommit(self, tmp_path: Path) -> None:
        """Should detect pre-commit configuration."""
        (tmp_path / ".pre-commit-config.yaml").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "pre-commit" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_husky(self, tmp_path: Path) -> None:
        """Should detect husky configuration."""
        (tmp_path / ".husky").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "husky" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_github_actions(self, tmp_path: Path) -> None:
        """Should detect GitHub Actions workflows."""
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "GitHub Actions" for tool in analysis.tools)

    @pytest.mark.unit
    def test_detects_docker(self, tmp_path: Path) -> None:
        """Should detect Docker configuration."""
        (tmp_path / "Dockerfile").touch()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert any(tool.name == "Docker" for tool in analysis.tools)


class TestMissingComponentDetection:
    """Tests for identifying missing infrastructure components."""

    @pytest.mark.unit
    def test_identifies_missing_pytest(self, tmp_path: Path) -> None:
        """Should identify missing pytest in Python projects."""
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".git").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert "pytest" in analysis.missing_components

    @pytest.mark.unit
    def test_identifies_missing_linting_python(self, tmp_path: Path) -> None:
        """Should identify missing linting in Python projects."""
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".git").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        # Check that linting is missing (ruff not detected)
        has_linting = any(tool.category == "linting" for tool in analysis.tools)
        assert not has_linting

    @pytest.mark.unit
    def test_identifies_missing_linting_js(self, tmp_path: Path) -> None:
        """Should identify missing linting in JavaScript projects."""
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / ".git").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert "eslint" in analysis.missing_components

    @pytest.mark.unit
    def test_identifies_missing_precommit(self, tmp_path: Path) -> None:
        """Should identify missing pre-commit in Git projects."""
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".git").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert "pre-commit" in analysis.missing_components

    @pytest.mark.unit
    def test_identifies_missing_ci(self, tmp_path: Path) -> None:
        """Should identify missing CI in Git projects."""
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".git").mkdir()
        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert "ci-workflow" in analysis.missing_components

    @pytest.mark.unit
    def test_no_missing_when_infrastructure_complete(self, tmp_path: Path) -> None:
        """Should report no missing components when infrastructure is complete."""
        # Create Python project with all infrastructure
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / "pytest.ini").touch()
        (tmp_path / "ruff.toml").touch()
        (tmp_path / ".pre-commit-config.yaml").touch()
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / ".git").mkdir()

        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()
        assert len(analysis.missing_components) == 0


class TestBootstrapTaskGenerator:
    """Tests for generating bootstrap tasks."""

    @pytest.mark.unit
    def test_generates_pytest_tasks(self) -> None:
        """Should generate pytest setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["pytest"],
            languages=[DetectedLanguage("Python")],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any("pytest" in task["title"].lower() for task in tasks)

    @pytest.mark.unit
    def test_generates_jest_tasks(self) -> None:
        """Should generate Jest setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["jest"],
            languages=[DetectedLanguage("JavaScript/TypeScript")],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any("jest" in task["title"].lower() for task in tasks)

    @pytest.mark.unit
    def test_generates_ruff_tasks(self) -> None:
        """Should generate Ruff setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["ruff"],
            languages=[DetectedLanguage("Python")],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any("ruff" in task["title"].lower() for task in tasks)

    @pytest.mark.unit
    def test_generates_eslint_tasks(self) -> None:
        """Should generate ESLint setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["eslint"],
            languages=[DetectedLanguage("JavaScript/TypeScript")],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any("eslint" in task["title"].lower() for task in tasks)

    @pytest.mark.unit
    def test_generates_precommit_tasks(self) -> None:
        """Should generate pre-commit setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["pre-commit"],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any("pre-commit" in task["title"].lower() for task in tasks)

    @pytest.mark.unit
    def test_generates_ci_tasks(self) -> None:
        """Should generate CI/CD setup tasks."""
        analysis = InfrastructureAnalysis(
            missing_components=["ci-workflow"],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert any(
            "ci" in task["title"].lower() or "github actions" in task["title"].lower()
            for task in tasks
        )

    @pytest.mark.unit
    def test_task_has_required_fields(self) -> None:
        """Should generate tasks with all required fields."""
        analysis = InfrastructureAnalysis(
            missing_components=["pytest"],
        )
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()

        for task in tasks:
            assert "title" in task
            assert "description" in task
            assert "epic" in task
            assert "type" in task
            assert "design" in task
            assert "acceptance" in task

    @pytest.mark.unit
    def test_generates_no_tasks_for_no_missing(self) -> None:
        """Should generate no tasks when no components are missing."""
        analysis = InfrastructureAnalysis()
        generator = BootstrapTaskGenerator(analysis)
        tasks = generator.generate_tasks()
        assert len(tasks) == 0


class TestIntegrationCompleteProject:
    """Integration tests for complete project analysis."""

    @pytest.mark.unit
    def test_analyzes_python_project_completely(self, tmp_path: Path) -> None:
        """Should completely analyze a Python project."""
        # Create a complete Python project
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\nversion = '0.1.0'\n")
        (tmp_path / "requirements.txt").write_text("fastapi>=0.100.0\n")
        (tmp_path / "pytest.ini").touch()
        (tmp_path / "ruff.toml").touch()
        (tmp_path / ".git").mkdir()

        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()

        assert len(analysis.languages) > 0
        assert any(lang.name == "Python" for lang in analysis.languages)
        assert any(fw.name == "FastAPI" for fw in analysis.frameworks)
        assert len(analysis.tools) > 0

    @pytest.mark.unit
    def test_analyzes_javascript_project_completely(self, tmp_path: Path) -> None:
        """Should completely analyze a JavaScript project."""
        # Create a complete JavaScript project
        (tmp_path / "package.json").write_text(
            '{"name":"test","version":"1.0.0","dependencies":{"react":"^18.0.0"},'
            '"devDependencies":{"jest":"^29.0.0"}}'
        )
        (tmp_path / "jest.config.js").touch()
        (tmp_path / ".eslintrc.json").touch()
        (tmp_path / ".git").mkdir()

        inspector = ProjectInspector(tmp_path)
        analysis = inspector.analyze()

        assert len(analysis.languages) > 0
        assert any(lang.name == "JavaScript/TypeScript" for lang in analysis.languages)
        assert any(fw.name == "React" for fw in analysis.frameworks)
        assert len(analysis.tools) > 0
