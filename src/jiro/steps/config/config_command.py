"""Config step command.

This command spawns a subagent to modify configuration files.
The subagent is responsible for:
1. Modifying configuration files (.yaml, .toml, .json, .ini, etc.)
2. Ensuring only config files are changed
3. Running verification to confirm changes are config-only
4. Returning structured result with config change details
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from jiro.commands.base import Command
from jiro.steps.config.config_result import ConfigResult

if TYPE_CHECKING:
    from jiro.agents.client import AgentClient
    from jiro.steps.types import PlanStep
    from jiro.trackers.interface import Task


class ConfigCommand(Command):
    """Command to spawn a subagent that modifies configuration files.

    The subagent will:
    - Modify configuration files based on planning context
    - Ensure all changes are config-only (no code changes)
    - Return structured output with config change details
    """

    tools: ClassVar[list[type]] = []  # Will be populated with actual tools
    output_schema: ClassVar[type] = ConfigResult

    def __init__(self, client: AgentClient) -> None:
        """Initialize ConfigCommand.

        Args:
            client: AgentClient for executing the config agent.
        """
        self.client = client

    async def execute(self, *, step: PlanStep, task: Task) -> ConfigResult:
        """Execute the config command.

        Spawns a subagent to modify configuration files based on planning context.

        Args:
            step: The plan step containing planning context
            task: The task being executed

        Returns:
            ConfigResult with config change details and subagent metrics

        Raises:
            ValueError: If the agent execution fails.
        """
        start_time = time.monotonic()

        # Build prompt for config agent
        prompt = self._build_config_prompt(step, task)

        # Execute the agent
        result = await self.client.execute(prompt)

        if not result.success:
            raise ValueError(f"Config agent execution failed: {result.error}")

        # Calculate execution time
        execution_time = time.monotonic() - start_time

        # Get changed files from git
        changed_files = self._get_changed_files()

        # Categorize config files and extract types
        config_types = self._categorize_config_files(changed_files)

        return ConfigResult(
            changed_files=[Path(f) for f in changed_files],
            config_files_changed=len(changed_files),
            config_types=list(config_types),
            subagent_type=self.client.config.model,
            subagent_prompt=prompt,
            tokens_in=result.tokens_before,
            tokens_out=result.tokens_after - result.tokens_before,
            subagent_time=execution_time,
        )

    def _build_config_prompt(self, step: PlanStep, task: Task) -> str:
        """Build the prompt for the config agent.

        Args:
            step: The plan step containing planning context.
            task: The task being executed.

        Returns:
            Formatted prompt for the config agent.
        """
        return f"""You are a configuration agent. Your task is to modify configuration files
based on the following planning context.

## Task Information
Task ID: {task.id}
Task Title: {task.title}
Task Description: {task.description or 'No description'}

## Step Instructions
{step.planning_context}

## Rules
1. ONLY modify configuration files:
   - .yaml, .yml, .toml, .json, .ini, .cfg, .conf, .env, .properties, .xml
   - Special config files: Dockerfile, Makefile, docker-compose.yml, pyproject.toml, setup.cfg, etc.
2. DO NOT modify any code files (Python, JavaScript, Java, C++, etc.)
3. Ensure all configuration files are in valid format after modification
4. All changes should be related to the same configuration purpose
5. Stage your changes with `git add` but do NOT commit

Execute the configuration modifications now."""

    def _get_changed_files(self) -> list[str]:
        """Get list of changed files from git diff.

        Returns:
            List of file paths that have been modified.
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = output.stdout.strip().split("\n") if output.stdout.strip() else []
            return [f for f in files if f]  # Filter empty strings
        except subprocess.CalledProcessError:
            return []

    def _categorize_config_files(self, changed_files: list[str]) -> set[str]:
        """Categorize config files by type.

        Args:
            changed_files: List of changed file paths.

        Returns:
            Set of config file types found (e.g., "yaml", "toml", "json").
        """
        config_types = set()

        for file_path in changed_files:
            filename_lower = file_path.lower()

            # Check special config file names first (before extensions)
            if "docker-compose" in filename_lower:
                config_types.add("docker-compose")
            elif filename_lower in ("dockerfile", "makefile"):
                config_types.add(filename_lower)
            elif "pyproject.toml" in filename_lower:
                config_types.add("toml")
            elif "setup.cfg" in filename_lower or "tox.ini" in filename_lower:
                config_types.add("ini")
            elif ".editorconfig" in filename_lower:
                config_types.add("editorconfig")
            elif ".gitignore" in filename_lower or ".gitattributes" in filename_lower:
                config_types.add("git")
            elif "eslintrc" in filename_lower or "prettierrc" in filename_lower:
                config_types.add("javascript")
            elif "tsconfig" in filename_lower:
                config_types.add("typescript")
            elif "babel.config" in filename_lower or "webpack.config" in filename_lower:
                config_types.add("build")
            elif "stylelintrc" in filename_lower:
                config_types.add("css")
            elif ".npmrc" in filename_lower or ".nvmrc" in filename_lower:
                config_types.add("nodejs")
            # Check standard extensions
            elif filename_lower.endswith(".yaml") or filename_lower.endswith(".yml"):
                config_types.add("yaml")
            elif filename_lower.endswith(".toml"):
                config_types.add("toml")
            elif filename_lower.endswith(".json"):
                config_types.add("json")
            elif filename_lower.endswith(".ini") or filename_lower.endswith(".cfg"):
                config_types.add("ini")
            elif filename_lower.endswith(".conf"):
                config_types.add("conf")
            elif filename_lower.endswith(".env"):
                config_types.add("env")
            elif filename_lower.endswith(".properties"):
                config_types.add("properties")
            elif filename_lower.endswith(".xml"):
                config_types.add("xml")
            elif filename_lower.endswith(".config"):
                config_types.add("config")

        return config_types
