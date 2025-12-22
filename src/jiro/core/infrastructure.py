"""Project infrastructure detection and bootstrap task generation."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class DetectedLanguage:
    """Represents a detected programming language."""

    name: str
    package_manager: str | None = None
    version_file: str | None = None


@dataclass
class DetectedFramework:
    """Represents a detected framework."""

    name: str
    language: str


@dataclass
class DetectedTool:
    """Represents a detected tool/infrastructure component."""

    category: str  # "testing", "linting", "ci", "hooks", etc.
    name: str
    config_file: str | None = None


@dataclass
class InfrastructureAnalysis:
    """Result of analyzing project infrastructure."""

    languages: list[DetectedLanguage] = field(default_factory=list)
    frameworks: list[DetectedFramework] = field(default_factory=list)
    tools: list[DetectedTool] = field(default_factory=list)
    missing_components: list[str] = field(default_factory=list)


class ProjectInspector:
    """Inspects a project directory for existing infrastructure."""

    def __init__(self, project_root: Path) -> None:
        """Initialize ProjectInspector.

        Args:
            project_root: Path to the project root directory.
        """
        self.project_root = project_root

    def analyze(self) -> InfrastructureAnalysis:
        """Analyze the project for existing infrastructure.

        Returns:
            InfrastructureAnalysis containing detected components.
        """
        analysis = InfrastructureAnalysis()

        # Detect languages and their tooling
        analysis.languages = self._detect_languages()
        analysis.frameworks = self._detect_frameworks()
        analysis.tools = self._detect_tools()

        # Identify missing components
        analysis.missing_components = self._identify_missing_components(analysis)

        logger.info(
            "infrastructure_analysis_complete",
            languages=[lang.name for lang in analysis.languages],
            frameworks=[fw.name for fw in analysis.frameworks],
            tools=[(t.category, t.name) for t in analysis.tools],
            missing_count=len(analysis.missing_components),
        )

        return analysis

    def _detect_languages(self) -> list[DetectedLanguage]:
        """Detect programming languages used in the project.

        Returns:
            List of detected programming languages.
        """
        languages = []

        # Python detection
        if self._has_python():
            lang = DetectedLanguage(
                name="Python",
                package_manager=self._detect_python_package_manager(),
                version_file=self._find_python_version_file(),
            )
            languages.append(lang)
            logger.info("detected_language", language="Python", package_manager=lang.package_manager)

        # JavaScript/TypeScript detection
        if self._has_javascript():
            lang = DetectedLanguage(
                name="JavaScript/TypeScript",
                package_manager=self._detect_js_package_manager(),
                version_file="package.json",
            )
            languages.append(lang)
            logger.info("detected_language", language="JavaScript/TypeScript", package_manager=lang.package_manager)

        # Go detection
        if self._has_go():
            lang = DetectedLanguage(
                name="Go",
                package_manager="go mod",
                version_file="go.mod",
            )
            languages.append(lang)
            logger.info("detected_language", language="Go")

        # Rust detection
        if self._has_rust():
            lang = DetectedLanguage(
                name="Rust",
                package_manager="cargo",
                version_file="Cargo.toml",
            )
            languages.append(lang)
            logger.info("detected_language", language="Rust")

        return languages

    def _detect_frameworks(self) -> list[DetectedFramework]:
        """Detect frameworks used in the project.

        Returns:
            List of detected frameworks.
        """
        frameworks = []

        # Python frameworks
        if self._check_dependency("django"):
            frameworks.append(DetectedFramework("Django", "Python"))
        if self._check_dependency("fastapi"):
            frameworks.append(DetectedFramework("FastAPI", "Python"))
        if self._check_dependency("flask"):
            frameworks.append(DetectedFramework("Flask", "Python"))

        # JavaScript/TypeScript frameworks
        if self._check_dependency("react"):
            frameworks.append(DetectedFramework("React", "JavaScript/TypeScript"))
        if self._check_dependency("next"):
            frameworks.append(DetectedFramework("Next.js", "JavaScript/TypeScript"))
        if self._check_dependency("vue"):
            frameworks.append(DetectedFramework("Vue.js", "JavaScript/TypeScript"))
        if self._check_dependency("express"):
            frameworks.append(DetectedFramework("Express", "JavaScript/TypeScript"))

        # Go frameworks
        if self._check_go_dependency("github.com/gin-gonic/gin"):
            frameworks.append(DetectedFramework("Gin", "Go"))
        if self._check_go_dependency("github.com/beego/beego"):
            frameworks.append(DetectedFramework("Beego", "Go"))

        for fw in frameworks:
            logger.info("detected_framework", name=fw.name, language=fw.language)

        return frameworks

    def _detect_tools(self) -> list[DetectedTool]:
        """Detect tools and infrastructure components.

        Returns:
            List of detected tools.
        """
        tools = []

        # Testing tools
        if self._file_exists("pytest.ini") or self._file_exists("setup.cfg"):
            tools.append(DetectedTool("testing", "pytest", "pytest.ini"))
        if self._file_exists("package.json") and self._check_dependency("jest"):
            tools.append(DetectedTool("testing", "jest", "jest.config.js"))
        if self._file_exists("package.json") and self._check_dependency("vitest"):
            tools.append(DetectedTool("testing", "vitest", "vitest.config.ts"))

        # Linting tools
        if self._file_exists("ruff.toml"):
            tools.append(DetectedTool("linting", "ruff", "ruff.toml"))
        elif self._file_exists("pyproject.toml") and self._has_ruff_config():
            tools.append(DetectedTool("linting", "ruff", "pyproject.toml"))
        if self._file_exists(".eslintrc.json") or self._file_exists(".eslintrc.js"):
            tools.append(DetectedTool("linting", "eslint", ".eslintrc.json"))
        if self._file_exists("golangci.yml"):
            tools.append(DetectedTool("linting", "golangci-lint", "golangci.yml"))

        # Commit hooks
        if self._dir_exists(".husky"):
            tools.append(DetectedTool("hooks", "husky", ".husky"))
        if self._file_exists(".pre-commit-config.yaml"):
            tools.append(DetectedTool("hooks", "pre-commit", ".pre-commit-config.yaml"))

        # CI/CD
        if self._dir_exists(".github/workflows"):
            tools.append(DetectedTool("ci", "GitHub Actions", ".github/workflows"))
        if self._file_exists(".gitlab-ci.yml"):
            tools.append(DetectedTool("ci", "GitLab CI", ".gitlab-ci.yml"))
        if self._file_exists(".travis.yml"):
            tools.append(DetectedTool("ci", "Travis CI", ".travis.yml"))

        # Container
        if self._file_exists("Dockerfile"):
            tools.append(DetectedTool("container", "Docker", "Dockerfile"))
        if self._file_exists("docker-compose.yml"):
            tools.append(DetectedTool("container", "Docker Compose", "docker-compose.yml"))

        for tool in tools:
            logger.info("detected_tool", category=tool.category, name=tool.name)

        return tools

    def _identify_missing_components(self, analysis: InfrastructureAnalysis) -> list[str]:
        """Identify missing infrastructure components.

        Args:
            analysis: The current infrastructure analysis.

        Returns:
            List of missing component names.
        """
        missing = []

        # For Python projects without testing
        has_python = any(lang.name == "Python" for lang in analysis.languages)
        has_testing = any(tool.category == "testing" for tool in analysis.tools)
        if has_python and not has_testing:
            missing.append("pytest")

        # For JavaScript projects without testing
        has_js = any(lang.name == "JavaScript/TypeScript" for lang in analysis.languages)
        if has_js and not has_testing:
            missing.append("jest")

        # For any project without linting
        has_linting = any(tool.category == "linting" for tool in analysis.tools)
        if not has_linting:
            if has_python:
                missing.append("ruff")
            elif has_js:
                missing.append("eslint")

        # For any project without commit hooks
        has_hooks = any(tool.category == "hooks" for tool in analysis.tools)
        if not has_hooks and self._has_git():
            missing.append("pre-commit")

        # For any project without CI/CD
        has_ci = any(tool.category == "ci" for tool in analysis.tools)
        if not has_ci and self._has_git():
            missing.append("ci-workflow")

        return missing

    # Helper methods for detection
    def _has_python(self) -> bool:
        """Check if project uses Python."""
        python_indicators = [
            "*.py",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]
        return self._has_indicators(python_indicators)

    def _has_javascript(self) -> bool:
        """Check if project uses JavaScript/TypeScript."""
        return self._file_exists("package.json")

    def _has_go(self) -> bool:
        """Check if project uses Go."""
        return self._file_exists("go.mod")

    def _has_rust(self) -> bool:
        """Check if project uses Rust."""
        return self._file_exists("Cargo.toml")

    def _has_git(self) -> bool:
        """Check if project uses Git."""
        return self._dir_exists(".git")

    def _detect_python_package_manager(self) -> str | None:
        """Detect the Python package manager.

        Returns:
            Name of the detected package manager or None.
        """
        if self._file_exists("uv.lock"):
            return "uv"
        if self._file_exists("poetry.lock"):
            return "poetry"
        if self._file_exists("Pipfile"):
            return "pipenv"
        if self._file_exists("requirements.txt"):
            return "pip"
        if self._file_exists("pyproject.toml"):
            return "pip"  # Default to pip for pyproject.toml without lock files
        return None

    def _find_python_version_file(self) -> str | None:
        """Find Python version specification file.

        Returns:
            Name of the version file or None.
        """
        if self._file_exists("pyproject.toml"):
            return "pyproject.toml"
        if self._file_exists("setup.py"):
            return "setup.py"
        return None

    def _detect_js_package_manager(self) -> str | None:
        """Detect the JavaScript package manager.

        Returns:
            Name of the detected package manager or None.
        """
        if self._file_exists("yarn.lock"):
            return "yarn"
        if self._file_exists("pnpm-lock.yaml"):
            return "pnpm"
        if self._file_exists("package-lock.json"):
            return "npm"
        return "npm"  # Default to npm if package.json exists

    def _check_dependency(self, dep_name: str) -> bool:
        """Check if a dependency is listed in package.json or requirements.

        Args:
            dep_name: Name of the dependency to check.

        Returns:
            True if dependency is found.
        """
        # Check Python requirements
        if self._file_exists("requirements.txt"):
            req_file = self.project_root / "requirements.txt"
            content = req_file.read_text()
            if dep_name.lower() in content.lower():
                return True

        # Check pyproject.toml
        if self._file_exists("pyproject.toml"):
            pyproject = self.project_root / "pyproject.toml"
            content = pyproject.read_text()
            if dep_name.lower() in content.lower():
                return True

        # Check package.json
        if self._file_exists("package.json"):
            package_file = self.project_root / "package.json"
            try:
                package_data = json.loads(package_file.read_text())
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                return dep_name in deps or dep_name in dev_deps
            except Exception:
                return False

        return False

    def _check_go_dependency(self, dep_name: str) -> bool:
        """Check if a Go dependency is listed in go.mod.

        Args:
            dep_name: Name of the Go module to check.

        Returns:
            True if dependency is found.
        """
        if self._file_exists("go.mod"):
            go_mod = self.project_root / "go.mod"
            content = go_mod.read_text()
            return dep_name in content
        return False

    def _file_exists(self, filename: str) -> bool:
        """Check if a file exists in project root.

        Args:
            filename: Name or pattern to check.

        Returns:
            True if file exists.
        """
        if "*" in filename:
            # Glob pattern
            return bool(list(self.project_root.glob(filename)))
        return (self.project_root / filename).exists()

    def _dir_exists(self, dirname: str) -> bool:
        """Check if a directory exists in project root.

        Args:
            dirname: Name of directory to check.

        Returns:
            True if directory exists.
        """
        return (self.project_root / dirname).is_dir()

    def _has_indicators(self, indicators: list[str]) -> bool:
        """Check if any of the provided indicators exist.

        Args:
            indicators: List of filenames or patterns to check.

        Returns:
            True if any indicator is found.
        """
        return any(self._file_exists(indicator) for indicator in indicators)

    def _has_ruff_config(self) -> bool:
        """Check if pyproject.toml has ruff configuration.

        Returns:
            True if ruff config is found in pyproject.toml.
        """
        if not self._file_exists("pyproject.toml"):
            return False
        try:
            pyproject = self.project_root / "pyproject.toml"
            content = pyproject.read_text()
            return "[tool.ruff" in content
        except Exception:
            return False


class BootstrapTaskGenerator:
    """Generates bootstrap tasks based on infrastructure analysis."""

    def __init__(self, analysis: InfrastructureAnalysis) -> None:
        """Initialize BootstrapTaskGenerator.

        Args:
            analysis: The infrastructure analysis result.
        """
        self.analysis = analysis

    def generate_tasks(self) -> list[dict]:
        """Generate bootstrap tasks for missing infrastructure.

        Returns:
            List of task dictionaries ready to be created.
        """
        tasks = []

        # Generate bootstrap tasks in priority order
        if "pytest" in self.analysis.missing_components:
            tasks.extend(self._generate_pytest_tasks())

        if "jest" in self.analysis.missing_components:
            tasks.extend(self._generate_jest_tasks())

        if "ruff" in self.analysis.missing_components:
            tasks.extend(self._generate_ruff_tasks())

        if "eslint" in self.analysis.missing_components:
            tasks.extend(self._generate_eslint_tasks())

        if "pre-commit" in self.analysis.missing_components:
            tasks.extend(self._generate_precommit_tasks())

        if "ci-workflow" in self.analysis.missing_components:
            tasks.extend(self._generate_ci_tasks())

        logger.info("bootstrap_tasks_generated", task_count=len(tasks))

        return tasks

    def _generate_pytest_tasks(self) -> list[dict]:
        """Generate pytest setup tasks.

        Returns:
            List of pytest bootstrap tasks.
        """
        return [
            {
                "title": "Set up pytest test harness",
                "description": "Initialize pytest with pyproject.toml configuration, conftest.py, and basic test structure.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create pyproject.toml with pytest config, set up tests/ directory, create conftest.py with shared fixtures.",
                "acceptance": [
                    "pytest.ini or [tool.pytest] in pyproject.toml configured",
                    "tests/ directory created with __init__.py",
                    "conftest.py created with basic fixtures",
                    "First test runs successfully",
                ],
            }
        ]

    def _generate_jest_tasks(self) -> list[dict]:
        """Generate Jest setup tasks.

        Returns:
            List of Jest bootstrap tasks.
        """
        return [
            {
                "title": "Set up Jest test harness",
                "description": "Initialize Jest with jest.config.js, test setup files, and basic test structure.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create jest.config.js, set up tests/ directory, create test setup file.",
                "acceptance": [
                    "jest.config.js created and configured",
                    "tests/ directory created with .gitkeep",
                    "First test runs successfully",
                    "Test command in package.json configured",
                ],
            }
        ]

    def _generate_ruff_tasks(self) -> list[dict]:
        """Generate Ruff linting tasks.

        Returns:
            List of Ruff bootstrap tasks.
        """
        return [
            {
                "title": "Configure Ruff for linting",
                "description": "Set up Ruff linting configuration with sensible defaults for Python code quality.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create ruff.toml with linting rules, configure isort, add lint commands to test suite.",
                "acceptance": [
                    "ruff.toml created with configuration",
                    "Lint command runs without syntax errors",
                    "Existing code passes linting or issues are documented",
                ],
            }
        ]

    def _generate_eslint_tasks(self) -> list[dict]:
        """Generate ESLint setup tasks.

        Returns:
            List of ESLint bootstrap tasks.
        """
        return [
            {
                "title": "Configure ESLint for linting",
                "description": "Set up ESLint configuration with sensible defaults for JavaScript/TypeScript code quality.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create .eslintrc.json or .eslintrc.js with configuration, configure Prettier integration.",
                "acceptance": [
                    ".eslintrc.json or .eslintrc.js created and configured",
                    "Lint command runs successfully",
                    "Existing code passes linting or issues are documented",
                ],
            }
        ]

    def _generate_precommit_tasks(self) -> list[dict]:
        """Generate pre-commit hooks tasks.

        Returns:
            List of pre-commit bootstrap tasks.
        """
        return [
            {
                "title": "Add pre-commit hooks configuration",
                "description": "Set up pre-commit hooks to run linting and formatting checks before commits.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create .pre-commit-config.yaml with hooks for linting, formatting, and security checks.",
                "acceptance": [
                    ".pre-commit-config.yaml created",
                    "pre-commit installed and configured",
                    "Hooks run successfully on test commit",
                    "Documentation on how to bypass hooks (if needed) is provided",
                ],
            }
        ]

    def _generate_ci_tasks(self) -> list[dict]:
        """Generate CI/CD workflow tasks.

        Returns:
            List of CI bootstrap tasks.
        """
        return [
            {
                "title": "Create GitHub Actions CI workflow",
                "description": "Set up GitHub Actions workflow for automated testing and linting on push and pull requests.",
                "epic": "project-infrastructure",
                "type": "task",
                "design": "Create .github/workflows/ci.yml with jobs for lint, test, and security checks. Use matrix builds if applicable.",
                "acceptance": [
                    ".github/workflows/ci.yml created",
                    "Workflow triggers on push and PR",
                    "Workflow runs successfully with test and lint jobs",
                    "Build status badge can be added to README",
                ],
            }
        ]
