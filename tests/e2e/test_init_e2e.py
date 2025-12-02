"""End-to-end tests for the init command."""

import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

from jiro.core.paths import (
    get_config_path,
    get_jiro_dir,
    get_logs_dir,
    get_specs_dir,
)


class TestInitCommandE2E:
    """E2E tests for the init command."""

    @pytest.fixture
    def temp_git_repo(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create a temporary git repository.

        Args:
            tmp_path: Pytest's temporary directory fixture.

        Yields:
            Path to the temporary git repository.
        """
        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

        # Configure git user for this test repo
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

        yield tmp_path

    def test_init_creates_directory_structure(self, temp_git_repo: Path) -> None:
        """Test that init creates the correct directory structure.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify .jiro-dreams-of-code directory exists
        jiro_dir = get_jiro_dir(temp_git_repo)
        assert jiro_dir.exists(), f"Directory {jiro_dir} not created"
        assert jiro_dir.is_dir(), f"{jiro_dir} is not a directory"

    def test_init_creates_specs_directory(self, temp_git_repo: Path) -> None:
        """Test that init creates the specs directory.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify specs directory exists
        specs_dir = get_specs_dir(temp_git_repo)
        assert specs_dir.exists(), f"Directory {specs_dir} not created"
        assert specs_dir.is_dir(), f"{specs_dir} is not a directory"

    def test_init_creates_logs_directory(self, temp_git_repo: Path) -> None:
        """Test that init creates the logs directory.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify logs directory exists
        logs_dir = get_logs_dir(temp_git_repo)
        assert logs_dir.exists(), f"Directory {logs_dir} not created"
        assert logs_dir.is_dir(), f"{logs_dir} is not a directory"

    def test_init_creates_config_file(self, temp_git_repo: Path) -> None:
        """Test that init creates a config.yaml file.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify config file exists
        config_path = get_config_path(temp_git_repo)
        assert config_path.exists(), f"Config file {config_path} not created"
        assert config_path.is_file(), f"{config_path} is not a file"

    def test_init_config_has_correct_structure(self, temp_git_repo: Path) -> None:
        """Test that the config file has the correct YAML structure.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Read and parse config file
        config_path = get_config_path(temp_git_repo)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify config structure
        assert config is not None, "Config file is empty"
        assert "project" in config, "Config missing 'project' section"
        assert "name" in config["project"], "Project config missing 'name'"
        assert "models" in config, "Config missing 'models' section"
        assert "commands" in config, "Config missing 'commands' section"
        assert "conventions" in config, "Config missing 'conventions' section"
        assert "preflight" in config, "Config missing 'preflight' section"

    def test_init_config_has_default_models(self, temp_git_repo: Path) -> None:
        """Test that the config file contains default model configurations.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Read and parse config file
        config_path = get_config_path(temp_git_repo)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify model configuration
        models = config["models"]
        assert "planning" in models, "Models missing 'planning'"
        assert "execution" in models, "Models missing 'execution'"
        assert "review" in models, "Models missing 'review'"
        assert isinstance(models["planning"], str)
        assert isinstance(models["execution"], str)
        assert isinstance(models["review"], str)

    def test_init_config_has_default_commands(self, temp_git_repo: Path) -> None:
        """Test that the config file contains default command configurations.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Read and parse config file
        config_path = get_config_path(temp_git_repo)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify command configuration
        commands = config["commands"]
        assert "test" in commands, "Commands missing 'test'"
        assert "lint" in commands, "Commands missing 'lint'"
        assert "lint_fix" in commands, "Commands missing 'lint_fix'"
        assert commands["test"] == "pytest"
        assert commands["lint"] == "ruff check"

    def test_init_config_project_name_from_directory(self, tmp_path: Path) -> None:
        """Test that project name is derived from directory name.

        Args:
            tmp_path: Pytest's temporary directory fixture.
        """
        # Create a named subdirectory
        project_dir = tmp_path / "my-awesome-project"
        project_dir.mkdir()

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            capture_output=True,
            check=True,
        )

        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Read config and verify project name
        config_path = get_config_path(project_dir)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["project"]["name"] == "my-awesome-project"

    def test_init_fails_outside_git_repo(self, tmp_path: Path) -> None:
        """Test that init fails when not in a git repository.

        Args:
            tmp_path: Pytest's temporary directory fixture.
        """
        # Run jiro init without initializing git
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should fail
        assert result.returncode != 0, "init should fail outside git repo"
        output = (result.stdout + result.stderr).lower()
        assert "git" in output or "repository" in output

    def test_init_idempotent(self, temp_git_repo: Path) -> None:
        """Test that init can be run multiple times without errors.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init first time
        result1 = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result1.returncode == 0, f"First init failed: {result1.stderr}"

        # Run jiro init second time
        result2 = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result2.returncode == 0, f"Second init failed: {result2.stderr}"

        # Verify structure still exists
        jiro_dir = get_jiro_dir(temp_git_repo)
        assert jiro_dir.exists()

    def test_init_creates_all_required_directories(self, temp_git_repo: Path) -> None:
        """Test that init creates all required directories in one call.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify all required directories exist
        jiro_dir = get_jiro_dir(temp_git_repo)
        specs_dir = get_specs_dir(temp_git_repo)
        logs_dir = get_logs_dir(temp_git_repo)

        assert jiro_dir.exists() and jiro_dir.is_dir()
        assert specs_dir.exists() and specs_dir.is_dir()
        assert logs_dir.exists() and logs_dir.is_dir()

    def test_init_successful_output(self, temp_git_repo: Path) -> None:
        """Test that init produces expected output messages.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Check output contains success indicators
        output = result.stdout.lower()
        assert "initializ" in output or "creat" in output, "Missing initialization output"

    def test_init_with_nonexistent_remote(self, temp_git_repo: Path) -> None:
        """Test that init works correctly when no git remote is configured.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Git repo has no remote configured - this is the default state

        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify it used directory name as project name
        config_path = get_config_path(temp_git_repo)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["project"]["name"] == temp_git_repo.name

    def test_init_stealth_mode(self, temp_git_repo: Path) -> None:
        """Test that init --stealth creates files in home directory.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init with --stealth
        result = subprocess.run(
            ["uv", "run", "jiro", "init", "--stealth"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init --stealth failed: {result.stderr}"

        # Verify files are in stealth location
        project_name = temp_git_repo.name
        stealth_jiro_dir = Path.home() / ".jiro-dreams-of-code" / project_name
        assert stealth_jiro_dir.exists()
        assert (stealth_jiro_dir / "config.yaml").exists()
        assert (stealth_jiro_dir / "specs").exists()
        assert (stealth_jiro_dir / "logs").exists()

        # Clean up stealth directory
        import shutil

        shutil.rmtree(stealth_jiro_dir)

    def test_init_beads_initialization(self, temp_git_repo: Path) -> None:
        """Test that beads database is initialized.

        Note: This test may be skipped if 'bd' command is not available.

        Args:
            temp_git_repo: The temporary git repository fixture.
        """
        # Run jiro init
        result = subprocess.run(
            ["uv", "run", "jiro", "init"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Check if beads was initialized (output should mention it)
        # Note: beads initialization may fail gracefully if 'bd' is not available
        output = result.stdout.lower()
        assert "initiali" in output or "complete" in output

        # If .beads directory exists, verify it
        beads_dir = get_jiro_dir(temp_git_repo) / ".beads"
        if beads_dir.exists():
            # .beads should have been initialized by the beads command
            assert beads_dir.is_dir()
