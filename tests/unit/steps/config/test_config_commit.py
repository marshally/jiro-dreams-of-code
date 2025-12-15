"""Tests for ConfigCommit class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.steps.config.config_commit import ConfigCommit
from jiro.steps.config.config_result import ConfigResult
from jiro.steps.types import VerificationError
from jiro.verifications.base import VerificationResult


class TestConfigCommitIsCommit:
    """Test that ConfigCommit is a proper Commit subclass."""

    def test_is_commit_subclass(self):
        """ConfigCommit should inherit from Commit."""
        assert issubclass(ConfigCommit, Commit)

    def test_can_instantiate(self):
        """Should be able to instantiate ConfigCommit."""
        commit = ConfigCommit()
        assert isinstance(commit, ConfigCommit)


class TestConfigCommitCreate:
    """Test the create method."""

    @patch("jiro.steps.config.config_commit.subprocess.run")
    def test_create_success_single_file(self, mock_run):
        """Should create commit successfully for single file."""
        mock_run.return_value = MagicMock(
            stdout="[main abc1234] message",
            stderr="",
            returncode=0,
        )

        commit = ConfigCommit()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="git diff --name-only",
            verification_output="verified",
            verification_time=0.5,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=1.5,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "abc1234"
        assert "⚙️" in commit_result.message
        assert "config.yaml" not in commit_result.message  # filename not in message

    @patch("jiro.steps.config.config_commit.subprocess.run")
    def test_create_success_multiple_files(self, mock_run):
        """Should create commit successfully for multiple files."""
        mock_run.return_value = MagicMock(
            stdout="[main def5678] message",
            stderr="",
            returncode=0,
        )

        commit = ConfigCommit()
        result = ConfigResult(
            changed_files=[Path("config.yaml"), Path("settings.json"), Path(".env")],
            config_files_changed=3,
            config_types=["yaml", "json", "env"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="git diff --name-only",
            verification_output="verified",
            verification_time=0.5,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=1.5,
        )

        assert commit_result.sha == "def5678"
        assert "⚙️" in commit_result.message
        assert "3 files" in commit_result.message

    @patch("jiro.steps.config.config_commit.subprocess.run")
    def test_create_commit_message_format(self, mock_run):
        """Should format commit message with emoji."""
        mock_run.return_value = MagicMock(
            stdout="[main abc1234] message",
            stderr="",
            returncode=0,
        )

        commit = ConfigCommit()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="git diff --name-only",
            verification_output="verified",
            verification_time=0.5,
        )

        commit_result = commit.create(
            result=result,
            verification=verification,
            e2e_time=1.5,
        )

        # Should have the ⚙️ emoji
        assert commit_result.message.startswith("⚙️")

    @patch("jiro.steps.config.config_commit.subprocess.run")
    def test_create_fails_git_add_error(self, mock_run):
        """Should raise VerificationError if git add fails."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "git add", stderr="error")

        commit = ConfigCommit()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="git diff --name-only",
            verification_output="verified",
            verification_time=0.5,
        )

        with pytest.raises(VerificationError):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=1.5,
            )

    @patch("jiro.steps.config.config_commit.subprocess.run")
    def test_create_fails_git_commit_error(self, mock_run):
        """Should raise VerificationError if git commit fails."""
        from subprocess import CalledProcessError

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add succeeds
            CalledProcessError(1, "git commit", stderr="error"),  # git commit fails
        ]

        commit = ConfigCommit()
        result = ConfigResult(
            changed_files=[Path("config.yaml")],
            config_files_changed=1,
            config_types=["yaml"],
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        verification = VerificationResult(
            success=True,
            verification_command="git diff --name-only",
            verification_output="verified",
            verification_time=0.5,
        )

        with pytest.raises(VerificationError):
            commit.create(
                result=result,
                verification=verification,
                e2e_time=1.5,
            )


class TestConfigCommitExtractSha:
    """Test the _extract_sha static method."""

    def test_extract_sha_standard_format(self):
        """Should extract SHA from standard git output."""
        output = "[main abc123def456] Config message\n"
        sha = ConfigCommit._extract_sha(output)
        assert sha == "abc123def456"

    def test_extract_sha_with_branch_name(self):
        """Should extract SHA with various branch names."""
        output = "[feature/my-branch f00ba9] Update config\n"
        sha = ConfigCommit._extract_sha(output)
        assert sha == "f00ba9"

    def test_extract_sha_short_hash(self):
        """Should extract short SHA."""
        output = "[main a1b2c3d] message\n"
        sha = ConfigCommit._extract_sha(output)
        assert sha == "a1b2c3d"

    def test_extract_sha_long_hash(self):
        """Should extract long SHA."""
        output = "[main abcdef0123456789abcdef0123456789abcdef01] message\n"
        sha = ConfigCommit._extract_sha(output)
        assert sha == "abcdef0123456789abcdef0123456789abcdef01"

    def test_extract_sha_invalid_raises_error(self):
        """Should raise ValueError if SHA cannot be extracted."""
        output = "Some unexpected output without SHA\n"
        with pytest.raises(ValueError):
            ConfigCommit._extract_sha(output)
