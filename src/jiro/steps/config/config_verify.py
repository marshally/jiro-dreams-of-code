"""Verification for config step.

Verifies that the config step result meets the verification rules:
- Only config files changed (.yaml, .yml, .toml, .json, .ini, .cfg, .conf, .env, etc.)
- git diff matches changed_files
- Valid config file extensions or special config files (Dockerfile, Makefile, pyproject.toml, etc.)
"""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from jiro.steps.types import StepType, VerificationError
from jiro.verifications.base import Verification, VerificationResult

if TYPE_CHECKING:
    from jiro.results.base import Result


# Config file extensions (lowercase for comparison)
CONFIG_EXTENSIONS = {
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".properties",
    ".xml",
    ".config",
}

# Special config files (without extensions or unconventional)
SPECIAL_CONFIG_FILES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
    "makefile.in",
    "cmakelists.txt",
    "pyproject.toml",
    "setup.cfg",
    "tox.ini",
    ".editorconfig",
    ".gitignore",
    ".gitattributes",
    ".env",
    ".env.example",
    ".env.local",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".prettierrc.toml",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".eslintrc.yaml",
    ".eslintrc.yml",
    "tsconfig.json",
    ".npmrc",
    ".nvmrc",
    "babel.config.js",
    "webpack.config.js",
    "rollup.config.js",
    "vite.config.js",
    "next.config.js",
    "nuxt.config.js",
    "gatsby-config.js",
    ".stylelintrc",
    ".stylelintrc.json",
    ".stylelintrc.js",
    ".stylelintrc.yaml",
    ".stylelintrc.yml",
}


class ConfigVerify(Verification):
    """Verification for config step.

    Validates that:
    1. Only config files changed (recognized file extensions or special config files)
    2. git diff --name-only matches exactly changed_files
    """

    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the config step result.

        Args:
            result: The ConfigResult from command execution

        Returns:
            VerificationResult with success status and details

        Raises:
            VerificationError: If any verification rule is violated
        """
        start_time = time.monotonic()

        try:
            # Get changed files from git
            changed_files = self._get_git_changed_files()

            # Verify changed files match result
            self._verify_git_diff_matches(result, changed_files)

            # Verify all changed files are config files
            config_types = set()
            for file_path in changed_files:
                self._verify_is_config_file(file_path)
                config_type = self._get_config_type(file_path)
                if config_type:
                    config_types.add(config_type)

            # Verify result counts match actual files
            if hasattr(result, "config_files_changed") and result.config_files_changed != len(
                changed_files
            ):
                raise VerificationError(
                    step_type=StepType.CONFIG,
                    rule_violated="Config file count mismatch",
                    expected=f"config_files_changed={len(changed_files)}",
                    actual=f"config_files_changed={result.config_files_changed}",
                    details=f"Result reported {result.config_files_changed} config files but found {len(changed_files)}",
                )

            verification_time = time.monotonic() - start_time

            return VerificationResult(
                success=True,
                verification_command="git diff --name-only + config file validation",
                verification_output=f"Config changes verified: {len(changed_files)} config file(s) changed (types: {', '.join(sorted(config_types))})",
                verification_time=verification_time,
            )
        except VerificationError:
            raise

    def _get_git_changed_files(self) -> list[str]:
        """Get list of changed files from git diff.

        Returns:
            List of file paths that have changed

        Raises:
            VerificationError: If git diff fails
        """
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_changes = output.stdout.strip().split("\n") if output.stdout.strip() else []
            return git_changes
        except subprocess.CalledProcessError as e:
            raise VerificationError(
                step_type=StepType.CONFIG,
                rule_violated="Could not run git diff",
                expected="git diff --name-only to succeed",
                actual=f"git command failed: {e.stderr}",
                details=str(e),
            ) from e

    def _verify_git_diff_matches(self, result: Result, changed_files: list[str]) -> None:
        """Verify git diff matches result.changed_files.

        Args:
            result: The ConfigResult
            changed_files: List of files from git diff

        Raises:
            VerificationError: If git diff doesn't match changed_files
        """
        result_files = {str(f) for f in result.changed_files}
        git_changes = set(changed_files)

        if git_changes != result_files:
            raise VerificationError(
                step_type=StepType.CONFIG,
                rule_violated="git diff does not match changed_files",
                expected=f"git diff to show exactly: {result_files}",
                actual=f"git diff showed: {git_changes}",
                details=f"Difference: expected={result_files}, actual={git_changes}",
            )

    def _verify_is_config_file(self, file_path: str) -> None:
        """Verify a file is a recognized config file.

        Args:
            file_path: Path to the file

        Raises:
            VerificationError: If file is not a recognized config file
        """
        # Check if it matches a known config extension
        for ext in CONFIG_EXTENSIONS:
            if file_path.lower().endswith(ext):
                return

        # Check if it's a special config file (case-insensitive)
        file_path_lower = file_path.lower()
        # Extract just the filename from the path
        file_name_only = file_path_lower.split("/")[-1]

        if file_path_lower in SPECIAL_CONFIG_FILES or file_name_only in SPECIAL_CONFIG_FILES:
            return

        # Not a recognized config file
        raise VerificationError(
            step_type=StepType.CONFIG,
            rule_violated="Non-config file changed",
            expected=f"Only config files (extensions: {CONFIG_EXTENSIONS})",
            actual=f"Found non-config file: {file_path}",
            details=f"File {file_path} is not a recognized config file",
        )

    def _get_config_type(self, file_path: str) -> str | None:
        """Determine the config file type (e.g., "yaml", "json").

        Args:
            file_path: Path to the config file

        Returns:
            The config type (e.g., "yaml", "toml", "json") or None if unknown
        """
        filename_lower = file_path.lower()

        # Check extensions first
        for ext in CONFIG_EXTENSIONS:
            if filename_lower.endswith(ext):
                # Remove leading dot and return
                return ext[1:].lower()

        # Check special files
        file_name_only = filename_lower.split("/")[-1]

        if "yaml" in file_name_only or "yml" in file_name_only:
            return "yaml"
        elif "json" in file_name_only:
            return "json"
        elif "toml" in file_name_only:
            return "toml"
        elif "ini" in file_name_only or "cfg" in file_name_only:
            return "ini"
        elif "env" in file_name_only:
            return "env"
        elif "dockerfile" in file_name_only:
            return "dockerfile"
        elif "makefile" in file_name_only:
            return "makefile"
        elif "xml" in file_name_only:
            return "xml"
        elif "properties" in file_name_only:
            return "properties"

        return None
